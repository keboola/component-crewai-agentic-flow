from pathlib import Path
from crewai.tools import BaseTool


class ReadKeboolaTableTool(BaseTool):
    name: str = "read_keboola_table_tool"
    description: str = "Read all CSV files from /data/in/tables"

    def _run(self) -> str:
        base_path = Path("/data/in/tables")
        contents = []
        for file in base_path.glob("*.csv"):
            contents.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}\n")
        return "\n".join(contents)


class ReadKeboolaFileTool(BaseTool):
    name: str = "read_keboola_file_tool"
    description: str = "Read all files from /data/in/files"

    def _run(self) -> str:
        base_path = Path("/data/in/files")
        contents = []
        for file in base_path.glob("*"):
            if file.is_file():
                contents.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}\n")
        return "\n".join(contents)


class WriteKeboolaTableTool(BaseTool):
    name: str = "write_keboola_table_tool"
    description: str = "Write a CSV file to /data/out/tables"

    def _run(self, content: str, filename: str = "output.csv") -> str:
        output_path = Path("/data/out/tables") / filename
        output_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote table to {output_path}"


class WriteKeboolaFileTool(BaseTool):
    name: str = "write_keboola_file_tool"
    description: str = "Write a text file to /data/out/files"

    def _run(self, content: str, filename: str = "output.txt") -> str:
        output_path = Path("/data/out/files") / filename
        output_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote file to {output_path}"


class DownloadKeboolaDataTool(BaseTool):
    name: str = "download_keboola_data_tool"
    description: str = (
        "Download input data from either /data/in/tables or /data/in/files directory."
        "Returns all readable files with filenames as headers."
    )

    def _run(self) -> str:
        contents = []
        for directory in ["/data/in/tables", "/data/in/files"]:
            base_path = Path(directory)
            for file in base_path.glob("*"):
                if file.is_file():
                    contents.append(f"--- {file.name} ---\n{file.read_text(encoding='utf-8')}\n")
        return "\n".join(contents)