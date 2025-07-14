import logging
from typing import Optional
from pydantic import BaseModel, Field, ValidationError, field_validator
from keboola.component.exceptions import UserException
import yaml


class Authorization(BaseModel):
    service: str
    api_token: str = Field(alias="#api_token")
    api_base: Optional[str] = ""
    deployment_id: Optional[str] = ""
    api_version: Optional[str] = ""

    @field_validator("api_token", "service")
    def must_not_be_empty(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError(f"Field '{info.field_name}' cannot be empty")
        return value


class CrewAIMetadata(BaseModel):
    agents: str
    tasks: str
    flows: str
    inputs: Optional[str] = None

    def parsed(self) -> dict:
        try:
            for name, content in self.__dict__.items():
                if isinstance(content, str) and any(x in content for x in ["__import__", "eval", "exec"]):
                    raise UserException(f"Security warning: disallowed content in crewai_metadata.{name}")

            return {
                "agents": yaml.safe_load(self.agents),
                "tasks": yaml.safe_load(self.tasks),
                "flow": yaml.safe_load(self.flows),
                "inputs": yaml.safe_load(self.inputs) if self.inputs else {},
            }
        except yaml.YAMLError as e:
            raise UserException(f"Invalid YAML in crewai_metadata: {e}")


class Configuration(BaseModel):
    model: str = Field(default="gpt-4.1", description="LLM model name")
    authorization: Authorization
    crewai_metadata: CrewAIMetadata
    template: str = Field(default="empty_template", description="Template name")
    debug: bool = False

    def __init__(self, **data):
        try:
            super().__init__(**data)
        except ValidationError as e:
            error_messages = [f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in e.errors()]
            raise UserException(f"Validation Error: {', '.join(error_messages)}")

        if self.debug:
            logging.debug("Component will run in Debug mode")
