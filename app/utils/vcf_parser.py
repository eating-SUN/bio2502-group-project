from cyvcf2 import VCF
from app.utils.gene_to_protein import run_vep, parse_vep_output, get_uniprot_seq, parse_hgvs_protein, mutate_sequence
import os
import traceback

def process_vcf(vcf_path):
    vep_output_file = f"{vcf_path}.tsv"
    variant_data = []

    try:
        print("[DEBUG] 输入文件路径：", vcf_path)
        print("[DEBUG] 输入文件是否存在：", os.path.exists(vcf_path))
        print("[DEBUG] 输入文件大小：", os.path.getsize(vcf_path))

        # 读取VCF文件
        vcf_reader = VCF(vcf_path)
        vcf_records = list(vcf_reader)

        if not vcf_records:
            print("[WARNING] VCF 文件中无有效变异记录，跳过注释")
            return []

        # 调用 VEP 注释
        print(f"[DEBUG] 准备调用 run_vep，输出文件: {vep_output_file}")
        run_vep(vcf_path, vep_output_file)
        print(f"[DEBUG] VEP 注释完成，输出文件是否存在: {os.path.exists(vep_output_file)}")

        # 解析 VEP 输出
        annotated_variants = parse_vep_output(vep_output_file)
        print(f"[DEBUG] 解析 VEP 结果，变异注释数量: {len(annotated_variants)}")
        for v in annotated_variants[:3]:
            print("[DEBUG] 注释示例:", v)

        # 建立 VCF 记录字典
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

        # 整合蛋白质信息
        for v in annotated_variants:
            var_id = v['id']
            if var_id not in variant_dict:
                print(f"[WARNING] 找不到 VCF 中的变异记录: {var_id}")
                continue

            variant_info = variant_dict[var_id]
            seq = get_uniprot_seq(v['protein_id'])
            if not seq:
                print(f"[WARNING] 找不到 UniProt 序列: {v['protein_id']}")
                continue

            ref_aa, pos, alt_aa = parse_hgvs_protein(v['hgvs_p'])
            if ref_aa is None or pos is None or alt_aa is None:
                print(f"[WARNING] 无法解析 HGVS 表达式: {v['hgvs_p']}")
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

        return variant_data

    except Exception as e:
        print("[ERROR] process_vcf 处理出错:", e)
        traceback.print_exc()
        raise

    finally:
        try:
            if os.path.exists(vep_output_file):
                os.remove(vep_output_file)
                print(f"[DEBUG] 删除临时文件: {vep_output_file}")
        except Exception as e:
            print(f"[WARNING] 删除文件失败 {vep_output_file}: {e}")

