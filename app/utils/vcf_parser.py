import cyvcf2 as vcf
from app.utils.gene_to_protein import run_vep, parse_vep_output, get_uniprot_seq, parse_hgvs_protein, mutate_sequence
import os


# parse vcf file
def process_vcf(vcf_path):
    variant_data = []

    # 创建临时VCF文件
    temp_vcf_file = f"{vcf_path}.temp.vcf"
    with open(temp_vcf_file, 'w') as temp_vcf:
        vcf_reader = vcf.Reader(filename=vcf_path)
        vcf_writer = vcf.Writer(temp_vcf, vcf_reader)

        for record in vcf_reader: 
            alt = ",".join(record.ALT)
            genotype = record.gt_bases[0] if record.gt_bases else "NA"
            
            variant_info = {
                'id': record.ID if record.ID else f"{record.CHROM}:{record.POS}",
                'chrom': record.CHROM,
                'pos': record.POS,
                'ref': record.REF,
                'alt': alt,
                'genotype': genotype
            }

            # 将解析后的变异信息写入临时VCF文件
            vcf_writer.write_record(record)
        vcf_writer.close()

    # 调用VEP
    vep_output_file = f"{vcf_path}.vep.txt"
    run_vep(temp_vcf_file, vep_output_file)

    # 解析VEP结果
    annotated_variants = parse_vep_output(vep_output_file)

    for v in annotated_variants:
        seq = get_uniprot_seq(v['protein_id'])
        if not seq:
            continue
        ref_aa, pos, alt_aa = parse_hgvs_protein(v['hgvs_p'])
        if ref_aa is None or pos is None or alt_aa is None:
            continue
        mut_seq = mutate_sequence(seq, pos, alt_aa)
        variant_data.append({'variant_info':variant_info})
        variant_data.append({'protein_info':{
            'protein_id': v['protein_id'],
            'hgvs_p': v['hgvs_p'],
            'wt_seq': seq,
            'mut_seq': mut_seq
        }})

    # 清理临时文件
    os.remove(temp_vcf_file)
    os.remove(vep_output_file)

    return variant_data