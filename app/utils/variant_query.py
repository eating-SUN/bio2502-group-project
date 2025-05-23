import pandas as pd

# Load ClinVar data
clinvar_df = pd.read_csv('data/clinvar/variant_summary.csv')

def query_clinvar(rsid):
    match = clinvar_df[clinvar_df['RS# (dbSNP)'] == rsid]
    if match.empty:
        return {'rsid': rsid, 'info' : 'not found'}
    return match.iloc[0].to_dict()


# Load gene to protein data
def get_protein_sequence(rsid):
    protein_df = pd.read_csv('data/gene_to_protein.csv')
    match = protein_df[protein_df['rsid'] == rsid]
    if match.empty:
        return None
    return {
        'before': match.iloc[0]['wildtype_sequence'],
        'after': match.iloc[0]['mutated_sequence']
    }