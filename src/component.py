"""
CrewAI Agentic Flow App main class.
"""
from datetime import datetime, UTC
import logging

from keboola.component.base import ComponentBase
from keboola.component.exceptions import UserException

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
