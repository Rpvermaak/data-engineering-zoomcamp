# Data Engineering Zoomcamp 2026

This repository contains my projects, notes, and code for the Data Engineering Zoomcamp provided by DataTalks.Club.

## Project Overview
The goal of this course is to master the data engineering lifecycle by building a production-ready data pipeline. I am learning to manage infrastructure as code, orchestrate workflows, and process large-scale data using both batch and streaming methods.

## Tech Stack
* **Cloud:** Google Cloud Platform (GCP)
* **Infrastructure as Code:** Terraform
* **Containerization:** Docker & Docker Compose
* **Orchestration:** Kestra
* **Data Warehouse:** BigQuery
* **Transformation:** dbt (data build tool)
* **Batch Processing:** Apache Spark (PySpark)
* **Streaming:** Apache Kafka

---

## Repository Structure
* `01-docker-terraform/`: Setting up the environment and local Postgres.
* `02-orchestration/`: Workflow automation with Kestra.
* `03-data-warehouse/`: Data modeling in BigQuery.
* `04-analytics-engineering/`: Transforming data with dbt.
* `05-batch-processing/`: Distributed computing with Spark.
* `06-streaming/`: Real-time data processing.
* `projects/`: Midterm and final capstone projects.

---

## Progress Log
- [x] Week 1: Introduction, Docker & Terraform
- [ ] Week 2: Workflow Orchestration
- [ ] Week 3: Data Warehouse
- [ ] Week 4: Analytics Engineering
- [ ] Week 5: Batch Processing
- [ ] Week 6: Streaming
- [ ] Final Project

---

## Lessons Learned & Troubleshooting
*(Keep notes here of bugs you fixed to demonstrate problem-solving skills)*
* **Docker Networking:** Learned how to connect a Python script to a Postgres container using the internal network name.
* **GCP Permissions:** Resolved 403 Forbidden errors by ensuring the Service Account had the Storage Admin role.

---
