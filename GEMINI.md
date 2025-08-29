# Gemini Code Assistant Context

## Project Overview

This project is a Python-based tool for testing and evaluating Large Language Models (LLMs). It enables users to run structured tests against various models, primarily through the OpenRouter API. The tool is designed to assess model performance based on correctness, response time, and cost.

The core workflow is as follows:
1.  **Test Definition:** Test cases are defined in Markdown files within the `tests/` directory. Each file contains a description, a system prompt (role), the main prompt, and a series of questions with their corresponding expected answers.
2.  **Execution:** The main script (`main.py`) reads a specified test file, sends the questions to a configured LLM, and captures the responses.
3.  **Evaluation:** The tool compares the model's answers to the expected answers. For JSON responses, it performs a direct comparison. For text responses, it uses another LLM call to evaluate correctness.
4.  **Scoring:** A performance score is calculated for each test run, factoring in the percentage of correct answers and the median response time.
5.  **Reporting:** Detailed results are logged to a text file in the `result/` directory, and a summary of each test run is appended to an Excel spreadsheet (`report/report.xlsx`).

### Key Technologies
*   **Language:** Python 3
*   **Core Libraries:**
    *   `aiohttp`: For making asynchronous API requests to the LLM provider.
    *   `openpyxl`: For writing results to Excel files.
    *   `tabulate`: For formatting and displaying results in the console.
    *   `python-dotenv`: For managing environment variables (like API keys).

## Building and Running

This project does not have a formal build process. It is run directly as a Python script.

### Prerequisites
1.  **Python 3:** Ensure you have Python 3 installed.
2.  **Dependencies:** Install the required Python packages. Based on the imports, you can create a `requirements.txt` file and install them:
    ```bash
    # Create and activate a virtual environment (recommended)
    python3 -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    pip install aiohttp python-dotenv openpyxl tabulate
    ```
3.  **API Key:** You need an API key from [OpenRouter](https://openrouter.ai/keys). Create a `.env` file in the project root and add your key:
    ```
    OPENROUTER_API_KEY="your_openrouter_api_key_here"
    ```

### Running a Test

1.  **Configure the Test:** Open `main.py` and set the following variables:
    *   `model`: The identifier of the model you want to test (e.g., `"google/gemini-pro"`).
    *   `test_name`: The name of the test file (without the `.md` extension) from the `tests/` directory (e.g., `"get_metadata_1"`).
2.  **Execute the Script:** Run the `main.py` file from your terminal:
    ```bash
    python3 main.py
    ```
3.  **View Results:**
    *   The console will display a real-time summary of the test progress.
    *   A detailed log will be created at `result/<model_name>.txt`.
    *   A summary row will be added to `report/report.xlsx`.

## Development Conventions

### Code Structure
*   `main.py`: The main entry point for running tests. Contains the primary configuration and execution loop.
*   `func.py`: Contains helper functions, primarily for parsing Markdown test files (`get_section`) and writing output (`output`).
*   `providers/`: This directory contains modules for interacting with LLM providers.
    *   `open_router_async.py`: Handles asynchronous requests to the OpenRouter API.
    *   `open_router.py`: Contains synchronous functions, including one to fetch model details.
*   `report/`: This directory is for generating and storing reports.
    *   `calc_ball.py`: Implements the logic for calculating the final performance score.
    *   `check.py`: Contains functions for comparing model outputs against expected answers.
    *   `to_excel.py`: Handles writing summary data to the Excel report.
*   `tests/`: Contains the test case files in Markdown format.
*   `result/`: Stores the detailed text logs from test runs.

### Adding a New Test
1.  Create a new `.md` file in the `tests/` directory.
2.  Follow the existing structure:
    *   `# Описание`: A brief description of the test's goal.
    *   `# Роль`: The system prompt for the model.
    *   `# Промпт`: The main user prompt.
    *   `# Тесты`: A section containing one or more `## Вопрос X` and `## Ответ X` pairs.
3.  Update the `test_name` variable in `main.py` to run your new test.

### Adding a New Provider
1.  Create a new Python file in the `providers/` directory (e.g., `my_provider.py`).
2.  Implement a function that takes similar arguments to `openrouter_async` and returns a dictionary with the keys `"answer"`, `"prompt_tokens"`, and `"completion_tokens"`.
3.  Import and call this new function from `main.py`.
