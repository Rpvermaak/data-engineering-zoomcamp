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

### Terraform Basics — Creating GCP Infrastructure (Video 1.4.1)

**Video**: [Creating GCP Infrastructure with Terraform](https://www.youtube.com/watch?v=Y2ux7gq3Z0o&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=6)

**What we created with `main.tf`:**
1. **Google Cloud Storage Bucket** — for storing data files (with 30-day auto-delete lifecycle rule)
2. **BigQuery Dataset** — for querying data with SQL

**Terraform workflow:**
| Command | Purpose |
|---|---|
| `terraform init` | Downloads provider plugins, initializes working directory |
| `terraform plan` | Previews what will be created/changed/destroyed |
| `terraform apply` | Creates the infrastructure (asks `yes` to confirm) |
| `terraform destroy` | Tears down all resources to avoid costs |

**Authentication — two options:**
1. `gcloud auth application-default login` (if gcloud CLI is installed)
2. `export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-key.json"` (service account key)

**`.gitignore` — critical for security!** Never commit to Git:
- Credentials: `*.pem`, `*.key`, `.env`, `google_credentials.json`
- Terraform state: `.terraform/`, `*.tfstate`, `*.tfvars` (contains sensitive info)
- Lock files: `.terraform.lock.hcl`
- Reference template: [Terraform .gitignore](https://github.com/github/gitignore/blob/main/Terraform.gitignore)

**Course resources:**
- [Terraform overview notes](../../01-docker-terraform/terraform/1_terraform_overview.md)
- [Execution instructions](../../01-docker-terraform/terraform/terraform/README.md)
- [Original `main.tf` on GitHub](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/01-docker-terraform/1_terraform_gcp/terraform/main.tf)
- [HashiCorp GCP getting started](https://learn.hashicorp.com/collections/terraform/gcp-get-started)

### Terraform with Variables (Video 1.4.2)

**Video**: [Terraform Variables](https://youtu.be/PBi0hHjLftk)

**Key improvement over basic setup:** Instead of hardcoding values in `main.tf`, extract them into `variables.tf` and reference them with `var.<name>`.

**How it works:**
- `variables.tf` — defines variables with `description` and `default` values
- `main.tf` — references them as `var.project`, `var.credentials`, `var.location`, etc.
- Credentials are loaded via `file(var.credentials)` in the provider block — no more `export GOOGLE_APPLICATION_CREDENTIALS`

**Variables we defined:**
| Variable | Purpose | Default |
|---|---|---|
| `credentials` | Path to service account JSON key | `./keys/my-creds.json` |
| `project` | GCP project ID | `dezoomcamp-2025-493320` |
| `region` | GCP region | `us-central1` |
| `location` | Resource location | `US` |
| `bq_dataset_name` | BigQuery dataset name | `demo_dataset` |
| `gcs_bucket_name` | GCS bucket name (must be unique) | your unique name |
| `gcs_storage_class` | Storage class | `STANDARD` |

**Why use variables?**
- Avoid repeating values across resources
- Easy to change settings in one place
- Can override defaults at runtime: `terraform apply -var="project=other-project"`
- Keeps sensitive paths (like credentials) separate from infrastructure logic

### Data Ingestion Patterns
- Always define explicit dtypes — Pandas inference is unreliable on large CSVs
- `chunksize` parameter in `pd.read_csv` returns an iterator instead of loading everything into memory
- Progress bars (`tqdm`) are essential for long-running ingestion jobs