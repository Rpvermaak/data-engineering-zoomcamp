# Module 2: Workflow Orchestration — Notes

## Session: April 18, 2026

### What I Set Up

- Launched **Kestra** via Docker Compose with 4 services:
  - `kestra` (orchestrator UI on port 8080)
  - `kestra_postgres` (Kestra's internal metadata DB)
  - `pgdatabase` (Postgres for NY taxi data on port 5432)
  - `pgadmin` (DB admin UI on port 8085)
- Login: `admin@kestra.io` / `Admin1234!`

### Flows Completed

#### Flow 01 — Hello World (`01_hello_world.yaml`)
- **Inputs**: define parameters a flow accepts (e.g., `name` with a default value)
- **Variables**: template interpolation with `{{ inputs.name }}`
- **Tasks**: sequential steps — `Log`, `Return`, `Sleep`
- **Outputs**: reference previous task results with `{{ outputs.task_id.value }}`
- **pluginDefaults**: set default config for all tasks of a given type (e.g., log level)
- **Concurrency**: limit parallel executions (`behavior: FAIL`, `limit: 2`)
- **Triggers**: schedule-based execution with cron expressions (disabled in this flow)

#### Flow 02 — Python (`02_python.yaml`)
- Runs Python in an **isolated Docker container** (`python:slim`)
- Kestra installs dependencies automatically (`requests`, `kestra`)
- Use `Kestra.outputs()` to pass data back from Python to the flow
- First run is slow (pulls the Docker image), subsequent runs are faster

#### Flow 03 — Getting Started Data Pipeline (`03_getting_started_data_pipeline.yaml`)
- Simple ETL pipeline: **HTTP extract → Python transform → DuckDB query**
- Demonstrates chaining tasks where each step uses the output of the previous one

## Session: April 22, 2026

#### Flow 04 — Postgres Taxi Pipeline (`04_postgres_taxi.yaml`)
- Loads NYC yellow/green taxi CSV data into local Postgres using a **staging + merge** pattern
- Inputs: taxi type (`yellow`/`green`), year, month — fully parameterised
- **Staging table pattern**: truncate staging → bulk copy → MD5 unique ID → `MERGE INTO` final table
  - Idempotent: re-running the same month produces no duplicates
- **MD5 unique row ID**: concatenates key fields and hashes them (no natural PK in source data)
- **Conditional branching** (`If` task): yellow and green taxis have different schemas, so each gets its own branch
- `pluginDefaults` sets Postgres connection once for all tasks
- `render()` needed when interpolating `vars` inside other `vars`
- `PurgeCurrentExecutionFiles` cleans up temp storage after each run

### Key Takeaways

- Kestra is YAML-based — flows define `id`, `namespace`, `tasks`, and optionally `inputs`, `triggers`, `variables`
- Python tasks run in isolated containers, not on the host — clean dependency management
- Docker socket mount (`/var/run/docker.sock`) is required for Kestra to spin up task containers
- `docker compose down` stops everything; volumes persist so flows survive restarts
- Staging + merge is the correct pattern for idempotent loads — never insert directly into final tables
- `pluginDefaults` keeps JDBC credentials DRY across all Postgres tasks

#### Flow 05 — Scheduled Postgres Taxi Pipeline (`05_postgres_taxi_scheduled.yaml`)
- Identical logic to Flow 04, with a `triggers` block added at the bottom
- Two `Schedule` triggers (green at 09:00, yellow at 10:00, both on the 1st of the month)
- `trigger.date | date('yyyy-MM')` — auto-derives the correct month's file from the scheduled fire time
- `concurrency: limit: 1` — prevents concurrent executions from racing on the staging table
- **Backfilling**: replay past scheduled intervals from the Kestra UI (Triggers tab → Backfill executions); each execution gets the correct `trigger.date` injected automatically
- Add a `backfill: true` label from the UI to distinguish backfill runs in execution history
- Backfilling only works safely because the pipeline is idempotent (staging + MERGE)

#### ETL vs ELT
- **ETL**: transform before loading — data is cleaned outside the destination (Python, Spark); raw data not retained; suited to expensive/limited storage
- **ELT**: load raw first, transform inside the destination using SQL — raw data preserved, easy to re-process; the modern cloud warehouse pattern
- Flows 04–05 are **ELT**: raw CSV loads into a Postgres staging table, then SQL transforms it in place
- dbt (used later) is the canonical tool for the T in ELT

### Key Takeaways

- Kestra is YAML-based — flows define `id`, `namespace`, `tasks`, and optionally `inputs`, `triggers`, `variables`
- Python tasks run in isolated containers, not on the host — clean dependency management
- Docker socket mount (`/var/run/docker.sock`) is required for Kestra to spin up task containers
- `docker compose down` stops everything; volumes persist so flows survive restarts
- Staging + merge is the correct pattern for idempotent loads — never insert directly into final tables
- `pluginDefaults` keeps JDBC credentials DRY across all Postgres tasks
- Idempotency is a prerequisite for safe backfilling

### Next Up

- GCP pipelines (flows 06–09): GCS and BigQuery
- AI integration (flows 10–11)
