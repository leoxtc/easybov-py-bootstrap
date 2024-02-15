import time
import base64
import hashlib
import hmac
import json
from abc import ABC
from typing import Any, List, Optional, Type, Union, Tuple, Iterator
from urllib.parse import urlencode

from pydantic import BaseModel
from requests import Session
from requests.exceptions import HTTPError
from itertools import chain

from easybov.common.constants import (
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_RETRY_WAIT_SECONDS,
    DEFAULT_RETRY_EXCEPTION_CODES,
)

from easybov import __version__
from easybov.common.exceptions import APIError, RetryException
from easybov.common.types import RawData, HTTPResult, Credentials
from .constants import PageItem
from .enums import PaginationType, BaseURL


class RESTClient(ABC):
    def __init__(
        self,
        base_url: Union[BaseURL, str],
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        api_version: str = "v1",
        raw_data: bool = False,
        retry_attempts: Optional[int] = None,
        retry_wait_seconds: Optional[int] = None,
        retry_exception_codes: Optional[List[int]] = None,
    ) -> None:

        self._api_key, self._secret_key = self._validate_credentials(
            api_key, secret_key
        )
        self._api_version: str = api_version
        self._base_url: Union[BaseURL, str] = base_url
        self._use_raw_data: bool = raw_data
        self._session: Session = Session()

        # setting up request retry configurations
        self._retry: int = DEFAULT_RETRY_ATTEMPTS
        self._retry_wait: int = DEFAULT_RETRY_WAIT_SECONDS
        self._retry_codes: List[int] = DEFAULT_RETRY_EXCEPTION_CODES

        if retry_attempts and retry_attempts > 0:
            self._retry = retry_attempts

        if retry_wait_seconds and retry_wait_seconds > 0:
            self._retry_wait = retry_wait_seconds

        if retry_exception_codes:
            self._retry_codes = retry_exception_codes

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[Union[dict, str]] = None,
        base_url: Optional[Union[BaseURL, str]] = None,
        api_version: Optional[str] = None,
    ) -> HTTPResult:
        """Prepares and submits HTTP requests to given API endpoint and returns response.
        Handles retrying if 429 (Rate Limit) error arises.

        Args:
            method (str): The API endpoint HTTP method
            path (str): The API endpoint path
            data (Optional[Union[dict, str]]): Either the payload in json format, query params urlencoded, or a dict
             of values to be converted to appropriate format based on `method`. Defaults to None.
            base_url (Optional[Union[BaseURL, str]]): The base URL of the API. Defaults to None.
            api_version (Optional[str]): The API version. Defaults to None.

        Returns:
            HTTPResult: The response from the API
        """
        base_url = base_url or self._base_url
        version = api_version if api_version else self._api_version
        api_path = "/api/" + version + path
        url: str = base_url + api_path

        opts = {
            "allow_redirects": False,
        }

        if method.upper() in ["GET", "DELETE"]:
            opts["params"] = data
        else:
            opts["json"] = data

        opts["headers"] = self._get_default_headers(method.upper(), api_path,
                                                     urlencode(opts["params"]) if "params" in opts else None,
                                                     json.dumps(opts["json"]) if "json" in opts else None)

        retry = self._retry

        while retry >= 0:
            try:
                return self._one_request(method, url, opts, retry)
            except RetryException:
                time.sleep(self._retry_wait)
                retry -= 1
                continue

    def _get_default_headers(self, method: str, url: str, query_string: str=None, payload_string: str=None) -> dict:       
        headers = self._get_auth_headers(method, url, query_string, payload_string)

        headers["User-Agent"] = "EASYBOV/" + __version__
        headers["cache-control"] = "no-cache"

        return headers

    def _generate_signature(self, ts: str, method: str, url: str, query_string: str=None, payload_string: str=None) -> str:
        m = hashlib.sha512()
        m.update((payload_string or "").encode('utf-8'))
        hashed_payload = m.hexdigest()
        s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, ts)
        sign = hmac.new(self._secret_key.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
        return sign


    def _get_auth_headers(self, method: str, url: str, query_string: str=None, payload_string: str=None) -> dict:
        headers = {}
        ts = str(time.time())
        sign = self._generate_signature(ts, method, url, query_string, payload_string)

        headers["EB-ACCESS-KEY"] = self._api_key
        headers["EB-ACCESS-TIMESTAMP"] = ts
        headers["EB-ACCESS-SIGN"] = sign

        return headers

    def _one_request(self, method: str, url: str, opts: dict, retry: int) -> dict:
        """Perform one request, possibly raising RetryException in the case
        the response is 429. Otherwise, if error text contain "code" string,
        then it decodes to json object and returns APIError.
        Returns the body json in the 200 status.

        Args:
            method (str): The HTTP method - GET, POST, etc
            url (str): The API endpoint URL
            opts (dict): Contains optional parameters including headers and parameters
            retry (int): The number of times to retry in case of RetryException

        Raises:
            RetryException: Raised if request produces 429 error and retry limit has not been reached
            APIError: Raised if API returns an error

        Returns:
            dict: The response data
        """
        response = self._session.request(method, url, **opts)

        try:
            response.raise_for_status()
        except HTTPError as http_error:
            # retry if we hit Rate Limit
            if response.status_code in self._retry_codes and retry > 0:
                raise RetryException()

            # raise API error for all other errors
            error = response.text

            raise APIError(error, http_error)

        if response.text != "":
            return response.json()

    def get(self, path: str, data: Union[dict, str] = None, **kwargs) -> HTTPResult:
        return self._request("GET", path, data, **kwargs)

    def post(self, path: str, data: Union[dict, List[dict], str] = None) -> HTTPResult:
        return self._request("POST", path, data)

    def put(self, path: str, data: Union[dict, str] = None) -> dict:
        return self._request("PUT", path, data)

    def patch(self, path: str, data: Union[dict, str] = None) -> dict:
        return self._request("PATCH", path, data)

    def delete(self, path, data: Union[dict, str] = None) -> dict:
        return self._request("DELETE", path, data)

    # TODO: Refactor to be able to handle both parsing to types and parsing to collections of types (parse_as_obj)
    def response_wrapper(
        self, model: Type[BaseModel], raw_data: RawData, **kwargs
    ) -> Union[BaseModel, RawData]:
        """To allow the user to get raw response from the api, we wrap all
        functions with this method, checking if the user has set raw_data
        bool. if they didn't, we wrap the response with a BaseModel object.

        Args:
            model (Type[BaseModel]): Class that response will be wrapped in
            raw_data (RawData): The raw data from API in dictionary
            kwargs : Any constructor parameters necessary for the base model

        Returns:
            Union[BaseModel, RawData]: either raw or parsed data
        """
        if self._use_raw_data:
            return raw_data
        else:
            return model(raw_data=raw_data, **kwargs)

    @staticmethod
    def _validate_pagination(
        max_items_limit: Optional[int], handle_pagination: Optional[PaginationType]
    ) -> PaginationType:
        """
        Private method for validating the max_items_limit and handle_pagination arguments, returning the resolved
        PaginationType.
        """
        if handle_pagination is None:
            handle_pagination = PaginationType.FULL

        if handle_pagination != PaginationType.FULL and max_items_limit is not None:
            raise ValueError(
                "max_items_limit can only be specified for PaginationType.FULL"
            )
        return handle_pagination

    @staticmethod
    def _return_paginated_result(
        iterator: Iterator[PageItem], handle_pagination: PaginationType
    ) -> Union[List[PageItem], Iterator[List[PageItem]]]:
        """
        Private method for converting an iterator that yields results to the proper pagination type result.
        """
        if handle_pagination == PaginationType.NONE:
            # user wants no pagination, so just do a single page
            return next(iterator)
        elif handle_pagination == PaginationType.FULL:
            # the iterator returns "pages", so we use chain to flatten them all into 1 list
            return list(chain.from_iterable(iterator))
        elif handle_pagination == PaginationType.ITERATOR:
            return iterator
        else:
            raise ValueError(f"Invalid pagination type: {handle_pagination}.")

    @staticmethod
    def _validate_credentials(
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
    ) -> Credentials:

        if not api_key or not secret_key:
            raise ValueError("You must supply a api_key and secret_key pair")

        return api_key, secret_key
