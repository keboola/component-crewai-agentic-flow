import logging

from pydantic import BaseModel, Field, ValidationError, field_validator
from keboola.component.exceptions import UserException


class Authorization(BaseModel):
    service: str
    api_token: str = Field(alias="#api_token")

    @field_validator("api_token", "service")
    def must_not_be_empty(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError(f"Field '{info.field_name}' cannot be empty")
        return value


class SyncOptions(BaseModel):
    github_repo: str
    github_branch: str = Field(default="main")
    github_folder: str

    @field_validator("github_repo", "github_folder")
    def must_not_be_empty(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError(f"Field '{info.field_name}' cannot be empty")
        return value


class Configuration(BaseModel):
    model: str = Field(default="gpt-4.1")
    authorization: Authorization
    sync_options: SyncOptions
    debug: bool = False

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError as e:
            error_messages = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
            raise UserException(f"Validation Error: {', '.join(error_messages)}")

        if self.debug:
            logging.debug("Component will run in Debug mode")
