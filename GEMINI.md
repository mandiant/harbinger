# Gemini Agent Instructions for the Harbinger Project

This document contains important context and lessons learned for any Gemini agent working on this codebase. Adhering to these guidelines will ensure smoother and more efficient development.

## 1. Getting Started

This section provides a step-by-step guide to get the project up and running for development.

### 1.1. Virtual Environment

The project uses a Python virtual environment. The convention is to locate it at `harbinger/venv/`. You might see other `venv` directories in the project root (`venv/`, `venv2/`, etc.), but `harbinger/venv/` is the correct one to use.

To create and activate the virtual environment:

```bash
python3 -m venv harbinger/venv
source harbinger/venv/bin/activate
```

### 1.2. Dependencies

The project's dependencies are managed in `requirements.txt` and `requirements_dev.txt`.

To install all necessary dependencies, run the following commands from the `harbinger` directory:

```bash
pip install -r requirements.txt
pip install -r requirements_dev.txt
```

### 1.3. Database Migrations

The project uses Alembic for database migrations. After setting up the environment and installing dependencies, you need to run the database migrations to set up the database schema.

The `pyproject.toml` file contains a script for this:

```bash
harbinger_migrate
```

### 1.4. Running the Application

The application consists of a backend (FastAPI) and a frontend (Quasar).

*   **To run the backend:**

    ```bash
    task uvicorn/reload
    ```

*   **To run the frontend:**

    ```bash
    task frontend
    ```

## 2. Codebase Overview

This section provides a high-level overview of the project's structure and where to find key features.

*   `harbinger/src/harbinger/`: This is the main application directory.
    *   `api/`: Contains the FastAPI application.
        *   `v1/endpoints/`: This is where all the API endpoints are defined. Each file corresponds to a specific feature (e.g., `files.py`, `users.py`).
    *   `models/`: Contains the SQLAlchemy database models. Each file represents a database table.
    *   `schemas/`: Contains the Pydantic schemas used for data validation and serialization. These are used in the API endpoints to define the shape of the request and response bodies.
    *   `crud/`: Contains the Create, Read, Update, Delete (CRUD) logic for the database models. This is where the database operations are defined.
    *   `worker/`: Contains the Temporal.io background worker, workflows, and activities.
    *   `connectors/`: Contains the code for interacting with external systems, such as C2 frameworks.
    *   `config/`: Contains the application's configuration and dependencies. `app.py` is the main entry point for the FastAPI application, and `dependencies.py` defines the dependencies used in the API endpoints.
    *   `scripts/`: Contains various scripts for development and maintenance, such as `generate_boilerplate.py` for creating new models, schemas, and CRUD files.
*   `harbinger/interface/`: Contains the Quasar frontend application.
*   `go/`: Contains Go services used by the application.
*   `proto/`: Contains the Protocol Buffer definitions used for communication between services.

## 3. Configuration

The application is configured primarily through environment variables. Key configuration variables include:

*   `pg_dsn`: The PostgreSQL database connection string.
*   `redis_dsn`: The Redis connection string.
*   `minio_access_key`: The MinIO access key.
*   `minio_secret_key`: The MinIO secret key.
*   `minio_host`: The MinIO host.
*   `minio_default_bucket`: The default MinIO bucket.
*   `temporal_host`: The Temporal host.

## 4. API Documentation

The project uses FastAPI, which automatically generates API documentation. You can access the Swagger UI at `http://localhost:8000/docs` and the ReDoc documentation at `http://localhost:8000/redoc` when the backend is running.

## 5. Go Services & Protocol Buffers

The project includes Go services located in the `go/` directory. These services communicate with the Python backend using gRPC. The Protocol Buffer definitions are located in the `proto/` directory.

To compile the protocol buffers, run the following command:

```bash
task protoc
```

## 6. Background Worker & Connectors

The project uses a background worker to process long-running tasks. The worker is built using the `temporalio` library and is defined in `harbinger/src/harbinger/worker/run_worker.py`.

The worker is responsible for:

*   Running playbooks
*   Processing files
*   Interacting with C2 servers
*   Generating suggestions
*   And more.

The worker is divided into two main task queues:

*   `WORKER_TASK_QUEUE`: For general tasks.
*   `FILE_PROCESSING_TASK_QUEUE`: For file processing tasks.

The project also has a system of connectors for interacting with external systems. The main connector is the `C2ConnectorWorkflow`, which is responsible for interacting with C2 servers. The `connectors` directory contains the code for the various connectors.

## 7. Project Structure: Avoid Monolithic Files

**Lesson:** The project was originally structured with monolithic files (`models.py`, `schemas.py`, `crud.py`) which became very difficult to manage as the project grew. A major refactoring effort was undertaken to split these files into a feature-based structure.

**Instruction:**
*   **ALWAYS** follow the established modular structure.
*   When adding a new database model, create a new file for it in `harbinger/src/harbinger/models/`.
*   Similarly, new schemas and CRUD logic should go into their respective directories (`schemas/`, `crud/`).
*   Do not add new logic to the old monolithic files if they still exist. The goal is to fully deprecate them.

## 8. Tooling and Commands

This section provides an overview of the tooling used in the project and the commands to run them.

### 8.1. Taskfile

The project uses `Taskfile` for running common tasks. You can see the available tasks in the `Taskfile.yml` file. To run a task, use `task <task_name>`. For example, to run the frontend, use `task frontend`.

### 8.2. Virtual Environment

The project uses a specific Python virtual environment located at `harbinger/venv/`. Standard commands like `pytest` or `mypy` may not be in the system's `PATH`.

**Instruction:**
*   **ALWAYS** use the Python executable from the project's virtual environment to run tools.
    *   For `pytest`: `harbinger/venv/bin/python -m pytest`
    *   For `mypy`: `harbinger/venv/bin/python -m mypy .`
*   This ensures that the correct versions of all dependencies are used.

### 8.3. Code Quality

The project uses `ruff` for linting and formatting, and `mypy` for static type checking.

*   **To format the code and handle import sorting:**

    ```bash
    harbinger/venv/bin/python -m ruff format .
    ```

*   **To automatically remove unused imports and perform other linting checks:**

    ```bash
    harbinger/venv/bin/python -m ruff check --select F401 --fix .
    ```

*   **To run static type checking:**

    ```bash
    harbinger/venv/bin/python -m mypy .
    ```

## 9. Testing

**Lesson:** The test suite (`pytest`) has a hard dependency on **Testcontainers**, which requires a running and accessible Docker daemon to spin up services like PostgreSQL.

**Instruction:**
*   The testing suite needs to be executed from outside the dev containers because it spins up new components. Ask the user to run pytest or ignore the errors related to databases.

## 10. Database Migrations

The project uses Alembic for database migrations. The `pyproject.toml` file contains scripts to help with this.

*   **To create a new migration:**

    ```bash
    harbinger_revision --autogenerate -m "Your migration message"
    ```

*   **To apply migrations:**

    ```bash
    harbinger_migrate
    ```

*   **To downgrade a migration:**

    ```bash
    harbinger_downgrade -1
    ```

## 11. Frontend

The frontend is a [Quasar](https://quasar.dev/) project located in the `harbinger/interface` directory.

To start the frontend development server, run:

```bash
task frontend
```

**Lesson:** There was a mismatch between the API paths expected by the frontend and the paths defined in the backend.

**Instruction:**
*   **The frontend is the source of truth for API paths.** When a mismatch is found, update the backend (`app.py`) to match the paths used in the frontend. This minimizes the number of files that need to be changed.

## 12. Handling Circular Dependencies

**Lesson:** The initial refactoring of the models revealed several circular dependencies between modules (e.g., `File` <-> `ProxyJob`). These were handled, but they indicate tight coupling in the data model.

**Instruction:**
*   When adding new models or relationships, be mindful of creating new circular dependencies.
*   Prefer using string-based forward references in SQLAlchemy relationships to mitigate direct import cycles (e.g., `relationship("MyOtherModel", ...)`).
*   If a new feature requires complex, bidirectional relationships, consider if the data model can be simplified to be unidirectional.
*   **Fixing Circular Dependencies:** The standard Python solution for this is to use a `typing.TYPE_CHECKING` block. Imports needed for type hints on relationships should be placed inside this block. This allows `mypy` to see the imports while preventing the Python runtime from encountering a circular import error.
    ```python
    from typing import TYPE_CHECKING

    # ... other imports ...

    if TYPE_CHECKING:
        from .related_model import RelatedModel

    class MyModel(Base):
        # ... columns ...
        related: Mapped["RelatedModel"] = relationship("RelatedModel")
    ```

## 13. Shared/Common Code

**Lesson:** During refactoring, a duplicated `mapped_column` definition was found across all new model files. This was centralized into `harbinger/src/harbinger/database/types.py`.

**Instruction:**
*   If you identify a piece of code (like a type definition, utility function, or base class) that is or could be used by multiple, otherwise unrelated features, place it in a shared location.
*   The `harbinger/src/harbinger/database/types.py` file is a good precedent. A more general `harbinger/src/harbinger/common/` directory would be an excellent candidate for future shared code.

## 14. Static Analysis & Refactoring

**Lesson:** During the refactoring of `models.py`, `mypy` failed with an `AssertionError` due to circular dependencies between the new model files. Furthermore, once the critical error was fixed, hundreds of previously ignored type annotation errors were revealed.

**Instruction:**
*   **Incremental Verification:** When running static analysis after a major change, it's best to start with the most specific package possible (e.g., `mypy harbinger/src/harbinger/models/`). Once that package is clean, expand the scope to the entire project (`mypy .`) to find and fix integration issues.
*   **Outdated Imports:** A major refactoring can leave old import paths in unexpected places (e.g., Alembic scripts, older utility scripts). Always perform a global search for the old module path (e.g., `harbinger.database.models`) to ensure all imports have been updated to the new structure (`harbinger.models`).

## 15. API Endpoint Refactoring

**Lesson:** The API endpoints were also initially structured in monolithic files (e.g., `c2.py`) and scattered across the codebase. A major refactoring effort was undertaken to split these files into a feature-based structure and consolidate them into a centralized `api/v1/endpoints` directory.

**Instruction:**
*   **Follow the established modular structure for endpoints.** When adding a new endpoint, create a new file for it in `harbinger/src/harbinger/api/v1/endpoints/`.
*   **Consolidate related, small endpoints.** For example, the various statistics endpoints were merged into a single `statistics.py` file.
*   **Split large, multi-functional endpoints.** For example, the `c2.py` endpoint was split into `c2_implants.py`, `c2_jobs.py`, `c2_output.py`, `c2_servers.py`, and `c2_tasks.py`.

## 16. FastAPI Routing and Static Files

**Lesson:** The order of router inclusion in `app.py` is critical. A WebSocket request was being incorrectly handled by the static file server, causing an `AssertionError`.

**Instruction:**
*   **Register all specific API and WebSocket routes *first*.**
*   **Mount the static file server as the very last step.** This ensures that any request that doesn't match an API route will fall through and be handled by the static file server.
    ```python
    # In harbinger/src/harbinger/config/app.py

    # ... include all your API and WebSocket routers first ...
    app.include_router(ws.router, prefix='/ws', tags=["ws"])
    app.include_router(events.router, prefix='/events', tags=["events"])

    # ... then mount the static files as the last step ...
    app.mount("/", StaticFiles(directory="dist", html=True))
    ```

## 17. Filter Refactoring

**Lesson:** The `filters.py` file was a monolithic file containing filter classes for many different models.

**Instruction:**
*   **Split filters into individual files.** Just like models, schemas, and CRUD, filters should be split into individual files within a `harbinger/filters` directory.
*   **Use the `__init__.py` file to expose all filters.** This allows for easy importing from the top-level package (`from harbinger import filters`).

## 18. Code Generation

**Lesson:** Creating all the necessary files for a new model (model, schema, CRUD, filter, endpoint) is a repetitive and error-prone process.

**Instruction:**
*   **Use the `generate_boilerplate.py` script to create the initial files for a new model.** This script, located in `harbinger/src/harbinger/scripts/`, will create the five necessary files with boilerplate code and provide instructions for the final integration steps.
    ```bash
    python harbinger/src/harbinger/scripts/generate_boilerplate.py MyNewModel
    ```