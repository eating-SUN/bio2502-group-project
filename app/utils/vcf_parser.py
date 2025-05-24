from cyvcf2 import VCF
from app.utils.gene_to_protein import run_vep, parse_vep_output, get_uniprot_seq, parse_hgvs_protein, mutate_sequence
import os

# parse vcf file
def process_vcf(vcf_path):
    variant_data = []

    # 读取VCF文件
    vcf_reader = VCF(vcf_path)
    vcf_records = list(vcf_reader)

    # 写入标准化VCF文件供VEP使用
    temp_vcf_file = f"{vcf_path}.temp.vcf"
    with open(temp_vcf_file, 'w') as f:
        header = str(vcf_reader.raw_header)
        f.write(header)
        for record in vcf_records:
            f.write(str(record))

    # 调用VEP
    vep_output_file = f"{vcf_path}.vep.txt"
    run_vep(temp_vcf_file, vep_output_file)

    # 解析VEP结果（包含id, protein_id, hgvs_p）
    annotated_variants = parse_vep_output(vep_output_file)

    # 建立变异字典以便根据 rsID 或 CHROM:POS 匹配
    variant_dict = {}
    for record in vcf_records:
        var_id = record.ID if record.ID else f"{record.CHROM}:{record.POS}"
        alt = ",".join(record.ALT)
        genotype = record.gt_bases[0] if record.gt_bases else "NA"
        variant_dict[var_id] = {
            'id': var_id,
            'chrom': record.CHROM,
            'pos': record.POS,
            'ref': record.REF,
            'alt': alt,
            'genotype': genotype
        }

    # 整合注释信息
    for v in annotated_variants:
        var_id = v['id']
        if var_id not in variant_dict:
            continue

        variant_info = variant_dict[var_id]

        seq = get_uniprot_seq(v['protein_id'])
        if not seq:
            continue
        ref_aa, pos, alt_aa = parse_hgvs_protein(v['hgvs_p'])
        if ref_aa is None or pos is None or alt_aa is None:
            continue
        mut_seq = mutate_sequence(seq, pos, alt_aa)

        variant_data.append({
            'variant_info': variant_info,
            'protein_info': {
                'protein_id': v['protein_id'],
                'hgvs_p': v['hgvs_p'],
                'wt_seq': seq,
                'mut_seq': mut_seq
            }
        })

    # 清理临时文件
    os.remove(temp_vcf_file)
    os.remove(vep_output_file)

    return variant_data