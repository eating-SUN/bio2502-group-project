from Bio.SeqUtils.ProtParam import ProteinAnalysis

def calculate_protein_features(seq_before, seq_after):
    """
    This function calculates the protein features of the two sequences before and after mutation.
    """
    
    ana_before = ProteinAnalysis(seq_before)
    ana_after = ProteinAnalysis(seq_after)

    properties = {
        'molecular_weight_change': round(ana_after.molecular_weight() - ana_before.molecular_weight(), 2),
        'aromaticity_change': round(ana_after.aromaticity() - ana_before.aromaticity(), 4),
        'instability_index_change': round(ana_after.instability_index() - ana_before.instability_index(), 2),
        'gravy_change': round(ana_after.gravy() - ana_before.gravy(), 4),
        'isoelectric_point_change': round(ana_after.isoelectric_point() - ana_before.isoelectric_point(), 2),
    }

    return properties