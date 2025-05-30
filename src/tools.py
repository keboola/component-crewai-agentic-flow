from crewai.tools import BaseTool
from pydantic import Field
from utils import get_data_path
import logging


class ReadKeboolaTableTool(BaseTool):
    name: str = Field(default="read_keboola_table_tool")
    description: str = Field(default="Read all CSV files from /data/in/tables")

    def _run(self) -> str:
        base_path = get_data_path("in/tables")
        contents = []
        for file in base_path.glob("*.csv"):
            logging.info(f"[ReadKeboolaTableTool] Reading file: {file}")
            contents.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}\n")
        return "\n".join(contents)


class ReadKeboolaFileTool(BaseTool):
    name: str = Field(default="read_keboola_file_tool")
    description: str = Field(default="Read all files from /data/in/files")

    def _run(self) -> str:
        base_path = get_data_path("in/files")
        contents = []
        for file in base_path.glob("*"):
            if file.is_file():
                logging.info(f"[ReadKeboolaFileTool] Reading file: {file}")
                contents.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}\n")
        return "\n".join(contents)


class WriteKeboolaTableTool(BaseTool):
    name: str = Field(default="write_keboola_table_tool")
    description: str = Field(default="Write a CSV file to /data/out/tables")

    def _run(self, content: str, filename: str = "output.csv") -> str:
        output_path = get_data_path(f"out/tables/{filename}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logging.info(f"[WriteKeboolaTableTool] File written to: {output_path.resolve()}")
        return f"Successfully wrote table to {output_path.resolve()}"


class WriteKeboolaFileTool(BaseTool):
    name: str = Field(default="write_keboola_file_tool")
    description: str = Field(default="Write a text file to /data/out/files")

    def _run(self, content: str, filename: str = "output.txt") -> str:
        output_path = get_data_path(f"out/files/{filename}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        logging.info(f"[WriteKeboolaFileTool] File written to: {output_path.resolve()}")
        return f"Successfully wrote file to {output_path.resolve()}"


class DownloadKeboolaDataTool(BaseTool):
    name: str = Field(default="download_keboola_data_tool")
    description: str = Field(default=(
        "Download input data from either /data/in/tables or /data/in/files directory."
        "Returns all readable files with filenames as headers."
    ))

    def _run(self) -> str:
        logging.info("[DownloadKeboolaDataTool] Invoked")
        contents = []
        for subdir in ["in/tables", "in/files"]:
            base_path = get_data_path(subdir)
            logging.info(f"[DownloadKeboolaDataTool] Scanning: {base_path}")
            for file in base_path.glob("*"):
                if file.is_file():
                    logging.info(f"[DownloadKeboolaDataTool] Reading file: {file}")
                    contents.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}\n")
        if not contents:
            logging.warning("[DownloadKeboolaDataTool] No files found to read.")
        return "\n".join(contents)
