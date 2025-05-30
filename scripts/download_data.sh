#!/bin/bash

set -e  # Exit on any error

echo "Creating data directories..."
mkdir -p data/clinvar data/prs data/regulome

echo "Downloading ClinVar data..."
wget -O data/clinvar/variant_summary.db "https://drive.google.com/uc?export=download&id=12FP1iDKnnPTwzVGui_AVLN_mvG4DHDhX"

echo "Downloading PRS data..."
wget -O data/prs/prs_brca.db "https://drive.google.com/uc?export=download&id=1CSKb8HSuLYyZ9CzJ2lLvFih16AkXNz4-"

echo "Downloading RegulomeDB data..."
wget -O data/regulome/regulome_data.csv "https://drive.google.com/uc?export=download&id=10AZqrmK075atRYVSPliIb6LLuHQY7NgZ"

echo "All files downloaded successfully."

