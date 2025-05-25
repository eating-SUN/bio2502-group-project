from cyvcf2 import VCF
from app.utils.gene_to_protein import run_vep, parse_vep_output, get_uniprot_seq, parse_hgvs_protein, mutate_sequence
import os
import re

def process_vcf(vcf_path):
    variant_data = []

    # 读取VCF文件
    vcf_reader = VCF(vcf_path)
    vcf_records = list(vcf_reader)

    # 从所有记录收集染色体名
    chroms = set(record.CHROM for record in vcf_records)

    # 读取原始头部
    header_lines = vcf_reader.raw_header.strip().split('\n')

    # 替换PL字段为Number=G
    raw_header = vcf_reader.raw_header
    raw_header = re.sub(r'##FORMAT=<ID=PL,Number=[^,]+,', '##FORMAT=<ID=PL,Number=G,', raw_header)
    header_lines = raw_header.strip().split('\n')

    # 找出已有contig
    existing_contigs = set()
    for line in header_lines:
        if line.startswith('##contig='):
            start = line.find('ID=')
            if start != -1:
                end = line.find(',', start)
                if end == -1:
                    end = line.find('>', start)
                if end != -1:
                    existing_contigs.add(line[start+3:end])

    # 插入缺失的contig声明，放在倒数第二行（#CHROM前）
    contig_lines = []
    for chrom in chroms:
        if chrom not in existing_contigs:
            # 这里长度你可以用真实长度，示例用2.5亿
            contig_lines.append(f'##contig=<ID={chrom},length=250000000>')

    # 找到#CHROM标题行索引
    chrom_header_idx = next(i for i, l in enumerate(header_lines) if l.startswith('#CHROM'))
    # 在#CHROM之前插入contig声明
    header_lines = header_lines[:chrom_header_idx] + contig_lines + header_lines[chrom_header_idx:]

    temp_vcf_file = f"{vcf_path}.temp.vcf"
    with open(temp_vcf_file, 'w') as f:
        for line in header_lines:
            f.write(line + '\n')

        # 写入每条变异记录
        for record in vcf_records:
            f.write(str(record) + '\n')

    # 调用VEP注释
    vep_output_file = f"{vcf_path}.vep.txt"
    run_vep(temp_vcf_file, vep_output_file)

    # 解析VEP输出文件，得到注释信息列表（包含id, protein_id, hgvs_p）
    annotated_variants = parse_vep_output(vep_output_file)

    # 构建字典用于快速查找原始变异信息，key为rsID或"CHROM:POS"
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

    # 整合注释和蛋白信息
    for v in annotated_variants:
        var_id = v['id']
        if var_id not in variant_dict:
            # 如果VEP注释ID不在原始变异中，跳过
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
    try:
        os.remove(temp_vcf_file)
    except OSError:
        pass
    try:
        os.remove(vep_output_file)
    except OSError:
        pass

    return variant_data