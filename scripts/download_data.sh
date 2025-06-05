#!/bin/bash

set -e  # Exit on any error

pip install gdown

echo "Creating data directories..."
mkdir -p data/clinvar data/prs data/regulome
gdown https://drive.google.com/uc?id=1Ee-76vU3IrT8QDBHjNgWvKeLDonuP2LO -O data/clinvar/clinvar.db
gdown https://drive.google.com/uc?id=1CSKb8HSuLYyZ9CzJ2lLvFih16AkXNz4- -O data/prs/prs_brca.db
gdown https://drive.google.com/uc?id=1eQShzYlODp34iaczvL5WFBmrJ3169iOW -O data/regulome/regulome.db

echo "All files downloaded successfully."

