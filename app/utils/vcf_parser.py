import cyvcf2 as vcf

# parse vcf file
def parse(file_path):
    vcf_reader = vcf.Reader(filename=file_path)
    variants = []

    for record in vcf_reader:
        
        alt = ",".join(record.ALT)

        # get genotype
        genotype = record.gt_bases[0] if record.gt_bases else "NA"
        
        variant = {
            'chrom': record.CHROM,
            'pos': record.POS,
            'id': record.ID if record.ID else f"{record.CHROM}:{record.POS}",
            'ref': record.REF,
            'alt': alt,
            'genotype': genotype
        }
        variants.append(variant)
    return variants