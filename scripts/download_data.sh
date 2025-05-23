#!/bin/bash

set -e  # Exit on any error

echo "Creating data directories..."
mkdir -p data/clinvar data/dbNSFP5 data/prs data/regulome

echo "Downloading ClinVar data..."
wget -O data/clinvar/variant_summary.csv "https://drive.google.com/uc?export=download&id=1mJTxGRyyqFCJEjcgiDXm1fSmcX8F6tOK"

echo "Downloading dbNSFP5 data..."
wget -O data/dbNSFP5/gene_to_protein.csv "https://drive.google.com/uc?export=download&id=1oGe8v6WvDvZ60ImR0SZsrLH2aReg1vBI"

echo "Downloading PRS data..."
wget -O data/prs/pgs000001.csv "https://drive.google.com/uc?export=download&id=1oTm_NigaPUw4zHejuK6rtqyOnF35Kd0j"

echo "Downloading RegulomeDB data..."
wget -O data/regulome/regulome_data.csv "https://drive.google.com/uc?export=download&id=10AZqrmK075atRYVSPliIb6LLuHQY7NgZ"

echo "All files downloaded successfully."
