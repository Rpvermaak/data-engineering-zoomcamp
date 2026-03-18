#!/usr/bin/env python3
"""
Fetches YouTube transcripts for all Data Engineering Zoomcamp modules
and consolidates them into per-module markdown files.
"""

import re
import sys
import time
from urllib.parse import urlparse, parse_qs

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, IpBlocked
except ImportError:
    print("ERROR: youtube_transcript_api not installed. Run: pip3 install youtube-transcript-api")
    sys.exit(1)

try:
    import browser_cookie3
    import requests
    HAS_COOKIES = True
except ImportError:
    HAS_COOKIES = False

# ─────────────────────────────────────────────────────────────────────────────
# VIDEO DATA: organized by module
# Format: (title, url)
# ─────────────────────────────────────────────────────────────────────────────

MODULES = {
    "Module_01_Docker_Terraform": {
        "title": "Module 1: Containerization and Infrastructure as Code (Docker & Terraform)",
        "videos": [
            ("Introduction to the Course", "https://www.youtube.com/watch?v=JgspdlKXS-w"),
            ("Docker + Postgres Workshop", "https://www.youtube.com/watch?v=lP8xXebHmuE"),
            ("SQL Refresher", "https://youtu.be/QEcps_iskgg"),
            ("Introduction to GCP (Google Cloud Platform)", "https://youtu.be/18jIzE41fJ4"),
            ("Introduction to Terraform: Concepts and Overview", "https://youtu.be/s2bOYDCKl_M"),
            ("Terraform Basics: Simple One-File Terraform Deployment", "https://youtu.be/Y2ux7gq3Z0o"),
            ("Terraform Deployment with a Variables File", "https://youtu.be/PBi0hHjLftk"),
            ("2024 Module-01 Walkthrough (ellacharmed)", "https://youtu.be/VUZshlVAnk4"),
            ("2024 Module-01 Environment Setup (ellacharmed)", "https://youtu.be/Zce_Hd37NGs"),
            ("2026 Tutorial: Setting Up Environment for Homework Week 1", "https://youtu.be/_iqCWi_UoOc"),
        ]
    },
    "Module_02_Workflow_Orchestration": {
        "title": "Module 2: Workflow Orchestration (Kestra)",
        "videos": [
            ("2.1.1 - What is Workflow Orchestration?", "https://youtu.be/-JLnp-iLins"),
            ("2.1.2 - What is Kestra?", "https://youtu.be/ZvVN_NmB_1s"),
            ("2.2.1 - Installing Kestra", "https://youtu.be/wgPxC4UjoLM"),
            ("2.2.2 - Kestra Concepts", "https://youtu.be/MNOKVx8780E"),
            ("2.2.3 - Orchestrate Python Code with Kestra", "https://youtu.be/VAHm0R_XjqI"),
            ("2.3.1 - Create an ETL Pipeline with Postgres in Kestra", "https://youtu.be/-KmwrCqRhic"),
            ("2.3.2 - Load Taxi Data to Local Postgres", "https://youtu.be/Z9ZmmwtXDcU"),
            ("2.3.3 - Scheduling and Backfills in Kestra", "https://youtu.be/1pu_C_oOAMA"),
            ("2.4.1 - ETL vs ELT", "https://youtu.be/E04yurp1tSU"),
            ("2.4.2 - Setup Google Cloud Platform", "https://youtu.be/TLGFAOHpOYM"),
            ("2.4.3 - ETL Pipeline with GCS and BigQuery in Kestra", "https://youtu.be/52u9X_bfTAo"),
            ("2.4.4 - GCP Workflow: Schedule and Backfills", "https://youtu.be/b-6KhfWfk2M"),
            ("2.5.1 - Using AI for Data Engineering", "https://youtu.be/GHPtRDAv044"),
            ("2.5.2 - Context Engineering with ChatGPT", "https://youtu.be/LmnfjGKwnVU"),
            ("2.5.3 - AI Copilot in Kestra", "https://youtu.be/3IbjHfC8bMg"),
            ("2.5.4 - Retrieval Augmented Generation (RAG)", "https://youtu.be/XuPDQ1UcNyI"),
        ]
    },
    "Module_03_Data_Warehouse": {
        "title": "Module 3: Data Warehouse (BigQuery)",
        "videos": [
            ("Data Warehouse Fundamentals", "https://youtu.be/jrHljAoD6nM"),
            ("BigQuery Setup", "https://youtu.be/-CqXf7vhhDs"),
            ("Cloud Storage to BigQuery", "https://youtu.be/k81mLJVX08w"),
            ("BigQuery Best Practices", "https://youtu.be/eduHi1inM4s"),
            ("BigQuery Partitioning and Clustering", "https://youtu.be/B-WtpB0PuG4"),
            ("BigQuery Machine Learning", "https://youtu.be/BjARzEWaznU"),
        ]
    },
    "Module_04_Analytics_Engineering": {
        "title": "Module 4: Analytics Engineering (dbt)",
        "videos": [
            ("Introduction to Analytics Engineering", "https://www.youtube.com/watch?v=HxMIsPrIyGQ"),
            ("Introduction to Data Modeling", "https://www.youtube.com/watch?v=uF76d5EmdtU"),
            ("What is dbt?", "https://www.youtube.com/watch?v=gsKuETFJr54"),
            ("Differences Between dbt Core and dbt Cloud", "https://www.youtube.com/watch?v=auzcdLRyEIk"),
            ("Project Setup: BigQuery + dbt Platform", "https://www.youtube.com/watch?v=GFbwlrt6f54"),
            ("Project Setup: DuckDB + dbt Core", "https://www.youtube.com/watch?v=GoFAbJYfvlw"),
            ("dbt Project Structure", "https://www.youtube.com/watch?v=2dYDS4OQbT0"),
            ("dbt Sources", "https://www.youtube.com/watch?v=7CrrXazV_8k"),
            ("dbt Models", "https://www.youtube.com/watch?v=JQYz-8sl1aQ"),
            ("dbt Seeds and Macros", "https://www.youtube.com/watch?v=lT4fmTDEqVk"),
            ("dbt Tests", "https://www.youtube.com/watch?v=bvZ-rJm7uMU"),
            ("dbt Documentation", "https://www.youtube.com/watch?v=UqoWyMjcqrA"),
            ("dbt Packages", "https://www.youtube.com/watch?v=KfhUA9Kfp8Y"),
            ("dbt Commands", "https://www.youtube.com/watch?v=t4OeWHW3SsA"),
        ]
    },
    "Module_05_Data_Platforms": {
        "title": "Module 5: Data Platforms (Bruin)",
        "videos": [
            ("Module 5 Introduction", "https://youtu.be/f6vg7lGqZx0"),
            ("Getting Started with Bruin", "https://youtu.be/JJwHKSidX_c"),
            ("NYC Taxi Pipeline with Bruin", "https://youtu.be/q0k_iz9kWsI"),
            ("Bruin MCP (Model Context Protocol)", "https://youtu.be/224xH7h8OaQ"),
            ("Bruin Cloud", "https://youtu.be/uBqjLEwF8rc"),
            ("Bruin Core Concepts: Projects", "https://www.youtube.com/watch?v=YWDjnSxbBtY"),
            ("Bruin Core Concepts: Pipelines", "https://www.youtube.com/watch?v=uzp_DiR4Sok"),
            ("Bruin Core Concepts: Assets", "https://www.youtube.com/watch?v=ZElY5SoqrwI"),
            ("Bruin Core Concepts: Variables", "https://www.youtube.com/watch?v=XCx0nDmhhxA"),
            ("Bruin Core Concepts: Commands", "https://www.youtube.com/watch?v=3nykPEs_V7E"),
        ]
    },
    "Module_06_Batch_Processing": {
        "title": "Module 6: Batch Processing (Apache Spark)",
        "videos": [
            ("Introduction to Batch Processing", "https://youtu.be/dcHe5Fl3MF8"),
            ("Spark Architecture Overview", "https://youtu.be/FhaqbEOuQ8U"),
            ("Spark SQL Introduction", "https://youtu.be/hqUbB9c8sKg"),
            ("Spark RDDs", "https://youtu.be/r_Sf6fCB40c"),
            ("Spark DataFrames", "https://youtu.be/ti3aC1m3rE8"),
            ("Spark GroupBy and Joins", "https://youtu.be/CI3P4tAtru4"),
            ("Spark DataFrame Operations", "https://youtu.be/uAlp2VuZZPY"),
            ("Spark SQL Queries", "https://youtu.be/68CipcZt7ZA"),
            ("Spark Data Partitioning", "https://youtu.be/9qrDsY_2COo"),
            ("Spark External Sorting", "https://youtu.be/lu7TrqAWuH4"),
            ("Running Spark on GCP", "https://youtu.be/Bdu-xIrF3OM"),
            ("Spark Local Setup", "https://youtu.be/k3uB2K99roI"),
            ("Spark on Dataproc", "https://youtu.be/Yyz293hBVcQ"),
            ("Spark Optimization", "https://youtu.be/HXBwSlXo5IA"),
            ("Spark Testing", "https://youtu.be/osAiAYahvh8"),
            ("Spark Extras", "https://youtu.be/HIm2BOj8C0Q"),
        ]
    },
    "Module_07_Streaming": {
        "title": "Module 7: Streaming (Kafka)",
        "videos": [
            ("7.0.1 - Introduction to Streaming", "https://youtu.be/hfvju3iOIP0"),
            ("7.0.2 - What is Stream Processing?", "https://youtu.be/WxTxKGcfA-k"),
            ("7.3 - What is Kafka?", "https://youtu.be/zPLZUDPi4AY"),
            ("7.4 - Confluent Cloud", "https://youtu.be/ZnEZFEYKppw"),
            ("7.5 - Kafka Producer and Consumer", "https://youtu.be/aegTuyxX7Yg"),
            ("7.6 - Kafka Configuration", "https://youtu.be/SXQtWyRpMKs"),
            ("7.7 - Kafka Stream Basics", "https://youtu.be/dUyA_63eRb0"),
            ("7.8 - Kafka Stream Join", "https://youtu.be/NcpKlujh34Y"),
            ("7.9 - Kafka Stream Testing", "https://youtu.be/TNx5rmLY8Pk"),
            ("7.10 - Kafka Stream Windowing", "https://youtu.be/r1OuLdwxbRc"),
            ("7.11 - Kafka ksqlDB and Connect", "https://youtu.be/DziQ4a4tn9Y"),
            ("7.12 - Kafka Schema Registry", "https://youtu.be/tBY_hBuyzwI"),
            ("Streaming Workshop: Live Session", "https://www.youtube.com/live/YDUgFeHQzJU"),
            ("2025 Stream with Zach Wilson", "https://www.youtube.com/watch?v=P2loELMUUeI"),
        ]
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def extract_video_id(url: str) -> str | None:
    """Extract the YouTube video ID from various URL formats."""
    # Handle youtu.be short links (strip query params and fragments)
    if "youtu.be/" in url:
        path = url.split("youtu.be/")[1]
        # Strip everything after ? or & or #
        video_id = re.split(r'[?&#]', path)[0]
        return video_id if video_id else None

    # Handle youtube.com/watch?v=...
    if "youtube.com/watch" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return params.get("v", [None])[0]

    # Handle youtube.com/live/VIDEO_ID
    if "youtube.com/live/" in url:
        path = url.split("youtube.com/live/")[1]
        video_id = re.split(r'[?&#]', path)[0]
        return video_id if video_id else None

    return None


FILLER_PATTERN = re.compile(
    r'\b(um+|uh+|ah+|hmm+|eh+|err+|okay so|you know|like i said|right\?|alright)\b',
    re.IGNORECASE
)

def clean_transcript(text: str) -> str:
    """Remove filler words, collapse whitespace, and tidy punctuation."""
    # Remove filler words
    text = FILLER_PATTERN.sub('', text)
    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)
    # Collapse lines that are just punctuation leftovers
    lines = [l.strip() for l in text.split('\n')]
    lines = [l for l in lines if l and l not in ('.', ',', ' ')]
    return '\n'.join(lines)


def _make_api():
    """Create API instance, using browser cookies if available to avoid IP blocks."""
    if HAS_COOKIES:
        try:
            cj = browser_cookie3.chrome(domain_name='.youtube.com')
            session = requests.Session()
            session.cookies = cj
            print("  [Using Chrome cookies for authentication]")
            return YouTubeTranscriptApi(http_client=session)
        except Exception:
            pass
    return YouTubeTranscriptApi()

_api = _make_api()


def fetch_transcript(video_id: str) -> tuple[str, str]:
    """
    Fetch transcript for a video ID.
    Returns (transcript_text, language_used).
    Raises IpBlocked, NoTranscriptFound, or VideoUnavailable.
    """
    transcript_list = _api.list(video_id)

    def _try_fetch(transcript_obj):
        """Fetch and join transcript text, re-raising IpBlocked."""
        try:
            entries = transcript_obj.fetch()
            return ' '.join(e.text for e in entries)
        except IpBlocked:
            raise  # always propagate IP blocks
        except Exception:
            return None

    # Try manually created English transcript first
    try:
        t = transcript_list.find_manually_created_transcript(['en'])
        text = _try_fetch(t)
        if text:
            return text, 'en-manual'
    except IpBlocked:
        raise
    except Exception:
        pass

    # Try auto-generated English
    try:
        t = transcript_list.find_generated_transcript(['en'])
        text = _try_fetch(t)
        if text:
            return text, 'en-auto'
    except IpBlocked:
        raise
    except Exception:
        pass

    # Try any available language and translate to English
    try:
        lang_codes = [tr.language_code for tr in transcript_list]
        t = transcript_list.find_generated_transcript(lang_codes)
        text = _try_fetch(t.translate('en'))
        if text:
            return text, 'translated'
    except IpBlocked:
        raise
    except Exception:
        pass

    raise NoTranscriptFound(video_id, [], {})


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

OUTPUT_DIR = "/Users/rubenvernaak/Desktop/ Data Analytics/data-engineering-zoomcamp"

def process_module(module_key: str, module_data: dict) -> None:
    module_title = module_data["title"]
    videos = module_data["videos"]
    output_path = f"{OUTPUT_DIR}/{module_key}_Consolidated_Transcripts.md"

    print(f"\n{'='*70}")
    print(f"Processing: {module_title}")
    print(f"{'='*70}")

    sections = []
    failed = []

    for title, url in videos:
        video_id = extract_video_id(url)
        if not video_id:
            print(f"  [SKIP] Could not extract video ID from: {url}")
            failed.append((title, url, "Could not extract video ID"))
            continue

        print(f"  Fetching: {title} ({video_id})", end=" ... ", flush=True)

        success = False
        for attempt in range(3):  # up to 3 retries for IP blocks
            try:
                raw_text, lang = fetch_transcript(video_id)
                clean_text = clean_transcript(raw_text)
                word_count = len(clean_text.split())
                print(f"OK ({lang}, {word_count} words)")
                sections.append(f"# {title}\n\n{clean_text}\n")
                time.sleep(10)  # longer delay to avoid IP blocks
                success = True
                break
            except IpBlocked:
                wait = 120 * (attempt + 1)
                print(f"IP blocked, waiting {wait}s before retry {attempt+1}/3...", end=" ", flush=True)
                time.sleep(wait)
            except (TranscriptsDisabled, NoTranscriptFound):
                print(f"FAILED (no transcript available)")
                failed.append((title, url, "No transcript available"))
                break
            except VideoUnavailable:
                print(f"FAILED (video unavailable)")
                failed.append((title, url, "Video unavailable"))
                break
            except Exception as e:
                print(f"FAILED ({type(e).__name__}: {e})")
                failed.append((title, url, str(e)))
                break
        if not success and (title, url, "No transcript available") not in failed and \
           (title, url, "Video unavailable") not in failed:
            # Failed all retries due to IP block
            print(f"FAILED (IP blocked after retries)")
            failed.append((title, url, "IP blocked"))

    # Build the markdown document
    header = f"# {module_title}\n\n"
    header += f"*Consolidated transcripts for NotebookLM — {len(sections)} of {len(videos)} videos transcribed.*\n\n"
    if failed:
        header += "## Videos Without Transcripts\n\n"
        for t, u, reason in failed:
            header += f"- **{t}** — {reason} ([link]({u}))\n"
        header += "\n---\n\n"

    body = "\n---\n\n".join(sections)
    content = header + body

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n  Saved → {output_path}")
    print(f"  Success: {len(sections)}/{len(videos)} | Failed: {len(failed)}")


if __name__ == "__main__":
    # Allow filtering to specific modules via CLI args
    target_modules = sys.argv[1:] if len(sys.argv) > 1 else list(MODULES.keys())

    for key in target_modules:
        if key not in MODULES:
            print(f"Unknown module: {key}")
            continue
        process_module(key, MODULES[key])

    print("\n\nAll done!")
