from __future__ import annotations
from typing import Dict, List, TYPE_CHECKING
from types import ModuleType
import yaml
from configuration import Configuration
from keboola.component.exceptions import UserException

# Import for type checking, real import is done lazy by requires_import decorator
if TYPE_CHECKING:
    from crewai import Agent, Crew, Task
    from crewai.llm import LLM
    from tools import (
        ReadKeboolaTableTool,
        ReadKeboolaFileTool,
        WriteKeboolaTableTool,
        WriteKeboolaFileTool,
        DownloadKeboolaDataTool,
    )


def requires_import(*mods):
    """
    A decorator to lazily import modules or objects from modules.
    It handles both `import module` and `from module import object`.
    Example 1 - 'import yaml':

        @requires_import('yaml')
        def my_function():
            pass

    Example 2 - 'from crewai import Agent, Crew, Task':

        @requires_import(('crewai', ['Agent', 'Crew', 'Task']))
        def my_function():
            pass
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            for mod in mods:
                if isinstance(mod, tuple):
                    # Handles 'from module import name' or 'from module import name1, name2'
                    package, names = mod
                    if isinstance(names, str):
                        names = [names]

                    module = __import__(package, fromlist=names)

                    for name in names:
                        if name not in globals():
                            globals()[name] = getattr(module, name)
                elif isinstance(mod, str):
                    # Handles 'import module'
                    if mod not in globals() or not isinstance(globals().get(mod), ModuleType):
                        globals()[mod] = __import__(mod)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


class CrewAIFlowBuilder:
    """
    This class handles the loading of a CrewAI YAML-defined flow
    from the Keboola config input and builds metadata structures for execution.
    """

    # Use a lazy import because crewai consumes almost all memory during the execution of the sync action.
    @requires_import(
        ("crewai.llm", "LLM"),
        ("crewai", ["Agent", "Crew", "Task"]),
        (
            "tools",
            [
                "ReadKeboolaTableTool",
                "ReadKeboolaFileTool",
                "WriteKeboolaTableTool",
                "WriteKeboolaFileTool",
                "DownloadKeboolaDataTool",
            ],
        ),
    )
    def __init__(self, config: Configuration):
        self.config = config

        parsed = self._safe_parse_metadata(config.crewai_metadata)
        self.agents = parsed.get("agents", {})
        self.tasks = parsed.get("tasks", {})
        self.flow = parsed.get("flow", {})
        self.inputs = parsed.get("inputs", {})

    def _safe_parse_metadata(self, metadata) -> dict:
        try:
            for name, content in metadata.__dict__.items():
                if isinstance(content, str) and any(x in content for x in ["__import__", "eval", "exec"]):
                    raise UserException(f"Security warning: disallowed content in crewai_metadata.{name}")

            parsed_agents = yaml.safe_load(metadata.agents)
            parsed_tasks = yaml.safe_load(metadata.tasks)
            parsed_flow = yaml.safe_load(metadata.flows)

            return {
                "agents": parsed_agents.get("agents", parsed_agents),
                "tasks": parsed_tasks.get("tasks", parsed_tasks),
                "flow": parsed_flow.get("flow", parsed_flow),
                "inputs": parsed_flow.get("inputs", {}),
            }
        except yaml.YAMLError as e:
            raise UserException(f"Invalid YAML in crewai_metadata: {e}")

    def metadata(self) -> Dict:
        return {
            "agents": self.agents,
            "tasks": self.tasks,
            "flow": self.flow,
            "inputs": self.inputs,
        }

    def build_crewai_flow(self, inputs: Dict = None) -> Crew:
        llm = LLM(
            model=self.config.model,
            api_key=self.config.authorization.api_token,
            base_url=self.config.authorization.dict().get("base_url", None)
        )

        tool_registry = {
            "read_keboola_table_tool": ReadKeboolaTableTool(),
            "read_keboola_file_tool": ReadKeboolaFileTool(),
            "write_keboola_table_tool": WriteKeboolaTableTool(),
            "write_keboola_file_tool": WriteKeboolaFileTool(),
            "download_keboola_data_tool": DownloadKeboolaDataTool(),
        }

        print("[DEBUG] Registered tools:", list(tool_registry.keys()))

        agents_by_name = {}
        for agent_name, agent_config in self.agents.items():
            tool_names = agent_config.get("tools", [])
            tools = [tool_registry[name] for name in tool_names if name in tool_registry]

            agents_by_name[agent_name] = Agent(
                role=agent_config.get("role", agent_name),
                goal=agent_config.get("goal", ""),
                backstory=agent_config.get("backstory", ""),
                tools=tools,
                llm=llm,
                verbose=self.config.debug,
            )

        tasks_by_name = {}
        for task_name, task_config in self.tasks.items():
            agent_name = task_config.get("agent")
            if not agent_name or agent_name not in agents_by_name:
                raise UserException(f"Agent '{agent_name}' for task '{task_name}' not defined or missing in agents")

            tasks_by_name[task_name] = Task(
                description=task_config.get("description", ""),
                expected_output=task_config.get("expected_output", ""),
                agent=agents_by_name[agent_name],
            )

        flow_def = self.flow
        task_sequence: List[str] = flow_def.get("tasks", [])
        ordered_tasks = [tasks_by_name[name] for name in task_sequence if name in tasks_by_name]

        return Crew(
            name=flow_def.get("name", "CrewAI Flow"),
            agents=list(agents_by_name.values()),
            tasks=ordered_tasks,
            verbose=self.config.debug,
            process=flow_def.get("process", "sequential"),
            chat_llm=llm,
            _inputs=inputs or self.inputs,
        )
