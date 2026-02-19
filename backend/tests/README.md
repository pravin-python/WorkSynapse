# WorkSynapse Testing

This directory contains the comprehensive test suite for the WorkSynapse backend.

## Structure

- `fixtures/`: Reusable test data factories (Users, Notes, Projects, Agents).
- `mocks/`: Mock implementations for external services (OpenAI, Google, Slack).
- `load_test/`: Locust load testing scripts.
- `conftest.py`: Global test configuration, database setup, and fixtures.

## Running Tests

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov httpx faker aiosqlite
    ```

2.  **Run All Tests:**
    ```bash
    pytest
    ```

3.  **Run with Coverage:**
    ```bash
    pytest --cov=app --cov-report=html
    ```
    Open `htmlcov/index.html` to view the report.

## Load Testing

1.  **Install Locust:**
    ```bash
    pip install locust
    ```

2.  **Run Locust:**
    ```bash
    locust -f tests/load_test/locustfile.py
    ```
    Open http://localhost:8089 in your browser.

## Continuous Integration

The project includes a GitHub Actions workflow `.github/workflows/ci.yml` that automatically runs tests on push/PR.
