from uuid import UUID
from pydantic import BaseModel
import pprint


class ValidateBaseModel(BaseModel, validate_assignment=True):    
    def __repr__(self):
        return pprint.pformat(self.model_dump(), indent=4)


class ModelWithID(ValidateBaseModel):
    id: UUID


class ModelWithCode(ValidateBaseModel):
    code: str