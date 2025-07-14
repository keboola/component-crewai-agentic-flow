# CrewAI Agentic Flow Data App

This project provides a generic, reusable CrewAI component designed to run LLM-powered agentic workflows within the Keboola ecosystem. It allows you to:

- Define agents, tasks, tools, and flows in a structured config.
- Orchestrate workflows where LLM agents perform data loading, analysis, and reporting.
- Execute flows inside the Keboola platform using the /data/in and /data/out directories.
- Extend flows to solve specific problems such as analytics, summarization, extraction, etc.

It is flexible enough to power various use cases but ships with a default flow example that calculates grouped metrics from CSV inputs and generates a summary.

## ⚙️ Example Configuration

```json
{
  "parameters": {
    "model": "gpt-4.1",
    "authorization": {
      "service": "openai",
      "#api_token": "<your-api-token>"
    },
    "crewai_metadata": {
      "flows": "flow:\n  name: universal_usage_summary\n  tasks:\n    - download_data_task\n    - calculate_metrics_task\n    - generate_summary_task\n    - write_summary_task",
      "agents": "agents:\n  data_analyst:\n    role: Data Analyst\n    goal: >\n      Analyze structured CSV data from the Keboola environment and generate grouped summaries based on the task outputs.\n    backstory: >\n      You are a focused data analyst who specializes in extracting useful insights from structured datasets.\n    tools:\n      - read_keboola_table_tool\n      - read_keboola_file_tool\n      - download_keboola_data_tool\n      - write_keboola_file_tool",
      "tasks": "tasks:\n  download_data_task:\n    description: >\n      Load all available input CSV datasets from the Keboola environment.\n      Use the tool `download_keboola_data_tool` to read every available table or file from disk.\n    expected_output: >\n      Full CSV content loaded from the available files or tables.\n    agent: data_analyst\n\n  calculate_metrics_task:\n    description: >\n      Use the CSV data to calculate totals, averages, counts, or ratios.\n    expected_output: >\n      A list of grouped metrics calculated from the input data.\n    agent: data_analyst\n\n  generate_summary_task:\n    description: >\n      Combine task outputs into a clear, structured summary grouped by a common key.\n    expected_output: >\n      A clean summary of all calculated metrics.\n    agent: data_analyst\n\n  write_summary_task:\n    description: >\n      Save the summary to a text file using the `write_keboola_file_tool`.\n    expected_output: >\n      Confirmation that the file was saved to /data/out/files/summary.txt.\n    agent: data_analyst"
    },
    "debug": false
  }
}
```

## 🔍 Deep Dive: universal_usage_summary Flow

This is the included demo flow that showcases the full capabilities of this app.

### 🧑 Agent: data_analyst

- **Role**: Performs all actions from data loading to analysis and reporting.
- **Tools**:
    - `download_keboola_data_tool`: loads all CSV data.
    - `read_keboola_table_tool`, `read_keboola_file_tool`: direct access tools.
    - `write_keboola_file_tool`: writes the final output file.

### 🔁 Tasks

| Task Name                | Description                                                                  |
| ------------------------ | ---------------------------------------------------------------------------- |
| `download_data_task`     | Loads all CSVs from `data/in/tables` and `data/in/files`.                    |
| `calculate_metrics_task` | Groups the data and computes metrics such as count, sum, or unique values.   |
| `generate_summary_task`  | Combines metrics into a readable format per entity (e.g., Company, Product). |
| `write_summary_task`     | Saves the final summary as `summary.txt` into `/data/out/files/`.            |

### 📦 Output

The result of the above pipeline is a file:

```bash
/data/out/files/summary.txt
```

```text
Entity: Alice   Total value: 10   Average value: 10.00   Count: 1
Entity: Bob     Total value: 15   Average value: 15.00   Count: 1

Entity: Widget  Total quantity: 10   Average quantity: 5.00   Count: 2
Entity: Gadget  Total quantity: 7    Average quantity: 7.00   Count: 1
```

### 🧩 Custom Flows

You can replace the crewai_metadata with any compatible CrewAI-style flow. All logic and tool orchestration is delegated to the LLM, based on your YAML definition.

To define your own flow:

- Update the flows, agents, and tasks keys in crewai_metadata.
- Register any custom tools in Python.
- Supply valid Keboola input files.

## 🚀 Running the Component

```bash
KBC_DATADIR=./data python3 src/component.py
```

Place your test `.csv` files under:

- `./data/in/tables/`
- `./data/in/files/`

Outputs will be written to:

- `./data/out/files/summary.txt`