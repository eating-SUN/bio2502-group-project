import pandas as pd

# Load ClinVar data
clinvar_df = pd.read_csv('data/clinvar/variant_summary.csv')

def query_clinvar(rsid):
    match = clinvar_df[clinvar_df['RS# (dbSNP)'] == rsid]
    if match.empty:
        return {'rsid': rsid, 'info' : 'not found'}
    return match.iloc[0].to_dict()