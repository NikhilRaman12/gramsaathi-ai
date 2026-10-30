"""Optional utility to fetch the existing document set from S3."""

from __future__ import annotations

import os
from pathlib import Path

import boto3


BUCKET_NAME = os.getenv("GRAMSAATHI_DOCS_S3_BUCKET", "gramsaathi-rag-docs")
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FILES = [
    "agri-infra-central.pdf",
    "atma-schemes-rd-central.pdf",
    "cibrc_registered_chemicals.pdf",
    "farm mechanization.pdf",
    "GOVERNMENT_SCHEMES_FOR_AGRICULTURE__Revised-26.12.2019.pdf",
    "Important Rural Development Programmes in India.pdf",
    "msp_allcrops.pdf",
    "NHB-pdf.pdf",
    "rurl development analysis.pdf",
    "samman_nidhi_pm.pdf",
]


def download_documents(bucket_name: str = BUCKET_NAME, data_dir: Path = DATA_DIR) -> list[Path]:
    data_dir.mkdir(parents=True, exist_ok=True)
    client = boto3.client("s3")
    downloaded = []
    for name in FILES:
        destination = data_dir / name
        client.download_file(bucket_name, name, str(destination))
        downloaded.append(destination)
        print(f"Downloaded {name} to {destination}")
    return downloaded


if __name__ == "__main__":
    download_documents()
