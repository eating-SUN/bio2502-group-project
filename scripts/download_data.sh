#!/bin/bash

set -e  # Exit on any error

echo "Creating data directories..."
mkdir -p data/clinvar data/prs data/regulome

echo "Downloading ClinVar data..."
wget -O data/clinvar/variant_summary.csv "https://drive.google.com/uc?export=download&id=1mJTxGRyyqFCJEjcgiDXm1fSmcX8F6tOK"

echo "Downloading PRS data..."
wget -O data/prs/prs_breast_cancer.csv "https://drive.google.com/uc?export=download&id=1obMcLzymHHgyARh98W5X0G95pVpHdj9g"

echo "Downloading RegulomeDB data..."
wget -O data/regulome/regulome_data.csv "https://drive.google.com/uc?export=download&id=10AZqrmK075atRYVSPliIb6LLuHQY7NgZ"

echo "All files downloaded successfully."

