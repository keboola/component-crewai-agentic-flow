"""
CrewAI Agentic Flow App main class.
"""
from datetime import datetime, UTC
import logging

from keboola.component.base import ComponentBase, sync_action
from keboola.component.exceptions import UserException
from keboola.component.sync_actions import ValidationResult, MessageType
import yaml

from configuration import Configuration
from crewai_flow_builder import CrewAIFlowBuilder


class Component(ComponentBase):
    def __init__(self):
        super().__init__()

    def run(self):
        run_time = datetime.now(UTC)
        run_time_str = run_time.strftime("%Y-%m-%dT%H:%M:%SZ")

        config = Configuration(**self.configuration.parameters)
        # state = self.get_state_file()
        new_state = {}

        logging.info("Initializing CrewAI flow...")
        crew_ai_flow = CrewAIFlowBuilder(config)

        crew = crew_ai_flow.build_crewai_flow(inputs={})

        logging.info("Running CrewAI flow...")
        result = crew.kickoff()

        print("\n=== CrewAI Flow Completed ===")
        print("Final Output:\n", result)

        # Update state
        new_state["last_successful_run"] = run_time_str
        self.write_state_file(new_state)
        logging.info("Component state saved.")
        logging.info("CrewAI processing completed successfully!")

    def validate_yaml(self, yaml_string: str) -> bool:
        try:
            yaml.safe_load(yaml_string)
            return True
        except yaml.YAMLError:
            return False
        except Exception as e:
            logging.error(f"Unexpected error during YAML validation: {e!r}")
            return False

    @sync_action('validate_config_yamls')
    def validate_config_yamls(self) -> ValidationResult:
        config = Configuration(**self.configuration.parameters)
        invalid_sections = []

        config_parts = [
            (config.crewai_metadata.flows, "flows"),
            (config.crewai_metadata.agents, "agents"),
            (config.crewai_metadata.tasks, "tasks")
        ]

        for yaml_string, section_name in config_parts:
            if not self.validate_yaml(yaml_string):
                invalid_sections.append(section_name)

        if not invalid_sections:
            return ValidationResult(
                "Configuration YAMLs are valid",
                MessageType.SUCCESS
            )
        else:
            if len(invalid_sections) > 1:
                error_message = "These configuration YAMLs are invalid: " + ", ".join(invalid_sections)
            else:
                error_message = "This configuration YAML is invalid: " + ", ".join(invalid_sections)
            return ValidationResult(
                error_message,
                MessageType.DANGER
            )


"""
        Main entrypoint
"""
if __name__ == "__main__":
    try:
        comp = Component()
        comp.execute_action()
    except UserException as exc:
        logging.exception(exc)
        exit(1)
    except Exception as exc:
        logging.exception(exc)
        exit(2)
