import logging
import tempfile
from pathlib import Path
from typing import Dict, List

import git
import yaml

from configuration import Configuration
from keboola.component.exceptions import UserException
from crewai import Agent, Crew, Task
from crewai.llm import LLM
from tools import (
    ReadKeboolaTableTool,
    ReadKeboolaFileTool,
    WriteKeboolaTableTool,
    WriteKeboolaFileTool,
    DownloadKeboolaDataTool,
)


class CrewAIFlowBuilder:
    """
    This class handles the loading of a CrewAI YAML-defined flow
    from a Git repository and builds metadata structures for further execution.
    """

    REQUIRED_FILES = ["agents.yaml", "tasks.yaml", "flow.yaml"]

    def __init__(self, config: Configuration):
        self.config = config
        self.repo_url = config.sync_options.github_repo
        self.repo_branch = config.sync_options.github_branch
        self.flow_folder = config.sync_options.github_folder

        self.local_repo_path = self._clone_repo()
        self.flow_path = self.local_repo_path / self.flow_folder

        self._validate_required_files()

        self.agents = self._load_yaml("agents.yaml")
        self.tasks = self._load_yaml("tasks.yaml")
        self.flow = self._load_yaml("flow.yaml")

    def _clone_repo(self) -> Path:
        """Clone the GitHub repository to a temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="crewai-flow-")
        logging.info(f"Cloning GitHub repo {self.repo_url}@{self.repo_branch} to {temp_dir}")
        git.Repo.clone_from(self.repo_url, temp_dir, branch=self.repo_branch)
        return Path(temp_dir)

    def _validate_required_files(self):
        """Ensure all required YAML files exist in the flow folder."""
        missing = [f for f in self.REQUIRED_FILES if not (self.flow_path / f).is_file()]
        if missing:
            raise UserException(f"Missing required files in flow folder '{self.flow_folder}': {', '.join(missing)}")

    def _load_yaml(self, filename: str) -> Dict:
        file_path = self.flow_path / filename
        logging.debug(f"Loading YAML: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if any(x in content for x in ["__import__", "eval", "exec"]):
                raise UserException(f"Security warning: disallowed content in {filename}")

            return yaml.safe_load(content)

        except yaml.YAMLError as e:
            raise UserException(f"Invalid YAML in file '{filename}': {e}")
        except Exception as e:
            raise UserException(f"Failed to load file '{filename}': {e}")

    def metadata(self) -> Dict:
        return {
            "agents": self.agents,
            "tasks": self.tasks,
            "flow": self.flow,
        }

    def build_crewai_flow(self, inputs: Dict) -> Crew:
        llm = LLM(
            model=self.config.model,
            temperature=getattr(self.config, "temperature", 0.2),
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

        agents_by_name = {}
        for agent_name, agent_cfg in self.agents.items():
            tool_names = agent_cfg.get("tools", [])
            tools = [tool_registry[name] for name in tool_names if name in tool_registry]

            agents_by_name[agent_name] = Agent(
                role=agent_cfg.get("role", agent_name),
                goal=agent_cfg.get("goal", ""),
                backstory=agent_cfg.get("backstory", ""),
                tools=tools,
                llm=llm,
                verbose=self.config.debug,
            )

        tasks_by_name = {}
        for task_name, task_cfg in self.tasks.items():
            agent_name = task_cfg.get("agent")
            if agent_name not in agents_by_name:
                raise UserException(f"Agent '{agent_name}' for task '{task_name}' not defined in agents.yaml")

            tasks_by_name[task_name] = Task(
                description=task_cfg.get("description", ""),
                expected_output=task_cfg.get("expected_output", ""),
                agent=agents_by_name[agent_name],
            )

        flow_def = self.flow.get("flow", {})
        task_sequence: List[str] = flow_def.get("tasks", [])
        ordered_tasks = [tasks_by_name[name] for name in task_sequence if name in tasks_by_name]

        return Crew(
            name=flow_def.get("name", "CrewAI Flow"),
            agents=list(agents_by_name.values()),
            tasks=ordered_tasks,
            verbose=self.config.debug,
            process=flow_def.get("process", "sequential"),
            chat_llm=llm,
            _inputs=inputs,
        )
