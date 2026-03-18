# Module 1: Docker & Terraform — Notes

## What I Built

- A **Python CLI pipeline** that ingests NYC Yellow Taxi data into PostgreSQL
- A **Dockerfile** using the modern `uv` package manager on Python 3.13-slim
- Local dev environment with **Docker Compose** (Postgres + pgAdmin)

## Key Takeaways

### Docker
- Containers isolate dependencies — no more "works on my machine"
- Use Docker networks to connect services (e.g., Python app → Postgres)
- `docker compose` simplifies multi-container setups

### PostgreSQL
- `to_sql()` with `if_exists='replace'` creates the table schema from the DataFrame
- Chunked inserts prevent memory issues on large datasets
- Nullable integer columns need Pandas `Int64` (capital I), not `int64`

### Terraform
- Infrastructure as Code: define GCP resources declaratively
- `terraform plan` → `terraform apply` workflow
- Service accounts need explicit IAM roles (e.g., `Storage Admin` for GCS access)

### Data Ingestion Patterns
- Always define explicit dtypes — Pandas inference is unreliable on large CSVs
- `chunksize` parameter in `pd.read_csv` returns an iterator instead of loading everything into memory
- Progress bars (`tqdm`) are essential for long-running ingestion jobs