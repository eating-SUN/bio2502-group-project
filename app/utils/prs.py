import pandas as pd

def compute_prs(variants):
    """
    calculate PRS score for variants based on PRS file
    """
    prs_df = pd.read_csv("data/prs/pgs000001.csv")
    prs_df = prs_df.dropna(subset=['rsID', 'effect_allele', 'effect_weight'])

    score = 0.0
    matched_snps = 0

    variant_dict = {v['id']: v for v in variants}

    for _, row in prs_df.iterrows():
        rsid = row['rsID']
        effect_allele = row['effect_allele']
        weight = row['effect_weight']

        if rsid in variant_dict:
            genotype = variant_dict[rsid]['genotype']
            # count the number of occurrences of the effect allele 
            dosage = genotype.count(effect_allele)
            score += dosage * weight
            matched_snps += 1

    return round(score, 4), matched_snps


def classify_risk(score, thresholds=[-1.0, 0.0, 1.0]):
    """
    classify risk based on PRS score and thresholds
    """
    if score < thresholds[0]:
        return "low risk"
    elif score < thresholds[1]:
        return "medium risk"
    elif score < thresholds[2]:
        return "high risk"
    else:
        return "extreme risk"



