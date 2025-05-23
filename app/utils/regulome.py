import pandas as pd

reg_df = pd.read_csv('data/regulome/regulome_data.csv')

# RegulomeDB score query 
def query_score(position):
    chrom = position['chrom']
    start = position['start']
    end = position['end']
    match = reg_df[(reg_df['chrom'] == chrom) & (reg_df['start'] == start) & (reg_df['end'] == end)]
    
    if match.empty:
        return 'Not Found'
    
    row = match.iloc[0]
    return {
        'chrom': row['chrom'],
        'start': row['start'],
        'end': row['end'],
        'rsid': row['rsid'],
        'ranking': row['ranking'],
        'probability_score': row['probability_score'],
    }
