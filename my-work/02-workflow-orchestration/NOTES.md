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

## Session: April 24, 2026

### GCP ELT Pipelines (Flows 06–09)

#### Flow 06 — GCP KV Setup (`06_gcp_kv.yaml`)
- Uses Kestra's **Key-Value (KV) store** to hold GCP config without hardcoding it in flows
- KV pairs set: `GCP_PROJECT_ID`, `GCP_LOCATION`, `GCS_BUCKET_NAME`, `GCP_DATASET`
- Access in flows with `{{ kv('KEY_NAME') }}`
- KV store is plain text — don't put credentials there; use **Secrets** instead
- Secrets: add `SECRET_<KEY>=value` as env vars in Docker Compose; reference in flows as `{{ secret('KEY') }}`
- GCP service account JSON stored as `SECRET_GCP_CREDS` (base64-encoded in Docker Compose env)

#### Flow 07 — Create GCP Infrastructure (`07_gcp_setup.yaml`)
- Creates the **GCS bucket** (data lake) and **BigQuery dataset** in one execution
- Uses `pluginDefaults` for GCP auth: `projectId`, `location`, `serviceAccount` (pulled from secret)
- Run once during project setup; both resources are create-if-not-exists so it's safe to re-run

#### Flow 08 — GCS + BigQuery ELT Pipeline (`08_gcp_taxi.yaml`)
- Implements the ELT pattern — load raw data into the cloud first, transform there:
  1. **Extract**: download CSV from GitHub (same wget as the Postgres pipeline)
  2. **Load to GCS**: upload raw CSV to the data lake bucket — no transformation yet
  3. **BigQuery staging**: create staging table, load directly from the GCS URI (`gs://bucket/file.csv`)
  4. **Transform in BigQuery**: `UPDATE` staging to add MD5 unique row ID + file name
  5. **MERGE** into final table (`yellow_trip_data` / `green_trip_data`)
- BigQuery table naming: `project_id.dataset.table_name` (dot notation, not `/`)
- `skipLeadingRows: 1` in the load config drops the CSV header row
- `IF` task still splits yellow/green paths (different column schemas)
- `pluginDefaults` sets GCP project, location, and service account once for all GCP tasks
- **Performance**: BigQuery processed 7M rows of yellow data in ~35 seconds; the same transform on Postgres took hours on a laptop

#### Flow 09 — Scheduled GCP ELT (`09_gcp_taxi_scheduled.yaml`)
- Identical to flow 08 with `Schedule` triggers added: green at 09:00, yellow at 10:00, 1st of month
- `trigger.date | date('yyyy-MM')` derives the correct file from the scheduled fire time — same pattern as Postgres
- Backfilling works identically: Triggers tab → Backfill executions, date range must cover the trigger's scheduled time
- End result: 22M+ rows merged for 3 months of yellow data, all in BigQuery

### Key Takeaways

- **GCS = data lake**: cheap, schema-free object storage; **BigQuery = data warehouse**: SQL engine that queries on top
- ELT is faster than ETL at scale because cloud compute (BigQuery) replaces local Python/SQL transforms
- BigQuery references GCS directly — raw files stay in the lake, the warehouse just queries over them
- KV store for non-sensitive config, Secrets for credentials — never mix the two
- Staging + MERGE is identical in BigQuery as in Postgres — same idempotency guarantees apply

---

## Session: April 24, 2026 (continued)

### AI in Data Engineering (2.5.1–2.5.4)

#### Why AI Matters in Data Engineering (2.5.1)
- Data engineers spend a lot of time on boilerplate: pipeline scaffolding, documentation, schema definitions
- AI can accelerate this, but only if it has **context** — without it, output looks correct but is wrong
- Three modes in Kestra: build-as-code, no-code editor, AI copilot — all interchangeable

#### Context Engineering (2.5.2)
- **Context engineering**: deliberately providing an AI with docs, examples, and schema so its output is accurate
- Demonstration: same prompt to vanilla ChatGPT (no context) produced a Kestra flow with invalid task types and missing auth properties — it would fail immediately
- Key insight: AI is like a new hire who has never seen your stack — give them the docs, don't expect them to guess

#### Kestra AI Copilot (2.5.3)
- Enable by adding to `KESTRA_CONFIGURATION`:
  ```yaml
  ai:
    type: gemini
    gemini:
      model-name: gemini-2.5-flash
      api-key: "{{ envs.GEMINI_API_KEY }}"
  ```
- Get a free Gemini API key from Google AI Studio; export as `GEMINI_API_KEY` env var before starting Docker Compose
- The copilot is context-aware: it knows your current workflow YAML and Kestra's full plugin library
- Generate a complete valid flow from a natural language prompt in one shot
- Iterative: follow-up questions work without re-providing the workflow ("rename the first task to download") — it also updates all references to that task ID automatically
- Contrast to ChatGPT: copilot produced syntactically valid YAML with correct properties and auth wired up

#### Retrieval Augmented Generation — RAG (2.5.4)
- **RAG**: ingest documents → create embeddings → store in a vector/embedding store → AI retrieves relevant embeddings at query time instead of relying on training data
- **Without RAG**: asked AI to list Kestra 1.1 features → confident but hallucinated (listed features that existed for years, not the actual 1.1 highlights)
- **With RAG**: ingested the Kestra 1.1 release notes as embeddings into the Kestra KV store → same question returned exact, accurate feature list
- Analogy: RAG is giving the AI a searchable knowledge base, not just its memory
- In Kestra: use the `ChatCompletion` task with an embedding store reference to enable RAG in a workflow

### Key Takeaways

- AI without context is confidently wrong — always provide docs, examples, or embeddings
- Kestra's AI copilot has built-in context (plugin library + your current flow); generic LLMs do not
- RAG closes the gap between "what the model was trained on" and "what is true right now" for your specific stack
- Use `SECRET_` prefix in Docker Compose for any sensitive value; access with `{{ secret('KEY') }}` in flows

### Next Up

- Module 03: Data Warehouses (BigQuery deep-dive)
