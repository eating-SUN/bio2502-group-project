from cyvcf2 import VCF
from app.utils.gene_to_protein import run_vep, parse_vep_output, get_uniprot_seq, parse_hgvs_protein, mutate_sequence
import os
import traceback

def process_vcf(vcf_path):
    vep_output_file = f"{vcf_path}.tsv"
    variants = []

    try:
        print(f"[DEBUG] 读取 VCF 文件: {vcf_path}")
        vcf_reader = VCF(vcf_path)
        vcf_records = list(vcf_reader)
        print(f"[DEBUG] 读取到 {len(vcf_records)} 条变异记录")

        if not vcf_records:
            print("[WARNING] VCF 文件中无变异记录")
            return []

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

        print(f"[DEBUG] 构建 VCF 变异字典，共 {len(variant_dict)} 条")

        # Step 2: 调用 VEP
        print(f"[DEBUG] 调用 VEP 注释，输出文件: {vep_output_file}")
        run_vep(vcf_path, vep_output_file)
        print(f"[DEBUG] VEP 注释完成，文件存在: {os.path.exists(vep_output_file)}")

        # Step 3: 解析 VEP 输出
        annotated_variants = parse_vep_output(vep_output_file)
        print(f"[DEBUG] 解析 VEP 注释结果，共获得 {len(annotated_variants)} 条注释")

        protein_info_dict = {}
        for v in annotated_variants:
            var_id = v['id']
            if var_id not in variant_dict:
                print(f"[WARNING] VEP 注释 ID 未在 VCF 中找到: {var_id}")
                continue

            hgvs_p = v.get('hgvs_p')
            protein_id = v.get('protein_id')
            if not hgvs_p or not protein_id:
                continue

            seq = get_uniprot_seq(protein_id)
            if not seq:
                print(f"[WARNING] 无法获取 UniProt 序列: {protein_id}")
                continue

            ref_aa, pos, alt_aa = parse_hgvs_protein(hgvs_p)
            if None in (ref_aa, pos, alt_aa):
                print(f"[WARNING] HGVS 解析失败: {hgvs_p}")
                continue

            if pos < 1 or pos > len(seq):
                print(f"[WARNING] 无效突变位置: 序列长度={len(seq)}, 位置={pos}")
                continue

            mut_seq = mutate_sequence(seq, pos, alt_aa)
            if not mut_seq:
                print(f"[WARNING] 突变序列生成失败: {hgvs_p}")
                continue

            protein_info_dict[var_id] = {
                'protein_id': protein_id,
                'hgvs_p': hgvs_p,
                'wt_seq': seq,
                'mut_seq': mut_seq
            }

        # Step 4: 整合变异信息
        for var_id, info in variant_dict.items():
            entry = {'variant_info': info}
            if var_id in protein_info_dict:
                entry['protein_info'] = protein_info_dict[var_id]
            variants.append(entry)

        print(f"[DEBUG] 整合完成，返回 {len(variants)} 条变异记录（含蛋白变异 {len(protein_info_dict)} 条）")
        return variants

    except Exception as e:
        print(f"[ERROR] 处理 VCF 出错: {e}")
        traceback.print_exc()
        raise

    finally:
        if os.path.exists(vep_output_file):
            try:
                os.remove(vep_output_file)
                print(f"[DEBUG] 删除临时文件: {vep_output_file}")
            except Exception as e:
                print(f"[WARNING] 无法删除临时文件 {vep_output_file}: {e}")
