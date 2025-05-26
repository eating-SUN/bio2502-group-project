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
            print(f"[DEBUG] VCF文件路径: {vcf_path}")
            print(f"[DEBUG] 文件头部示例: {str(vcf_reader.raw_header[:200])}")  # 输出部分头部信息
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

        # 调用 VEP 注释
        print(f"[DEBUG] 调用 VEP 注释，输出文件: {vep_output_file}")
        run_vep(vcf_path, vep_output_file)
        print(f"[DEBUG] VEP 注释完成，文件存在: {os.path.exists(vep_output_file)}")

        # 解析 VEP 注释结果
        annotated_variants = parse_vep_output(vep_output_file)
        print(f"[DEBUG] 解析 VEP 注释结果，共获得 {len(annotated_variants)} 条注释")

        protein_variant_ids = set()
        protein_info_dict = {}

        for i, v in enumerate(annotated_variants):
            var_id = v['id']
            if var_id not in variant_dict:
                print(f"[WARNING] VEP 注释 ID 未在 VCF 中找到: {var_id}")
                continue

            hgvs_p = v.get('hgvs_p')
            if not hgvs_p:
                print(f"[DEBUG] 变异 {var_id} 不涉及蛋白质变异")
                continue

            protein_id = v.get('protein_id')
            print(f"[DEBUG] 处理蛋白变异 {var_id}, HGVS: {hgvs_p}, 蛋白: {protein_id}")

            seq = get_uniprot_seq(protein_id)
            if not seq:
                print(f"[WARNING] 无法获取 UniProt 序列: {protein_id}")
                print(f"[DEBUG] 尝试访问的URL: https://rest.uniprot.org/uniprotkb/{v['protein_id']}.fasta")
                continue

            ref_aa, pos, alt_aa = parse_hgvs_protein(hgvs_p)
            if None in (ref_aa, pos, alt_aa):
                print(f"[WARNING] HGVS 解析失败: {hgvs_p}")
                continue
            
            # 检查突变位置有效性
            if pos < 1 or pos > len(seq):
                print(f"[WARNING] 无效突变位置: 序列长度={len(seq)}, 需求位置={pos}")
                continue

            mut_seq = mutate_sequence(seq, pos, alt_aa)
            if not mut_seq:
                print(f"[WARNING] 突变序列生成失败: pos={pos}, alt_aa={alt_aa}")
                continue
            
            print(f"[DEBUG] 序列突变成功: {ref_aa}{pos}{alt_aa} @ {protein_id}")

            protein_info_dict[var_id] = {
                'protein_id': protein_id,
                'hgvs_p': hgvs_p,
                'wt_seq': seq,
                'mut_seq': mut_seq
            }
            protein_variant_ids.add(var_id)

        # 合并蛋白信息与原始变异
        print(f"[DEBUG] 整合信息，共 {len(variant_dict)} 条变异，蛋白变异 {len(protein_info_dict)} 条")
        for var_id, info in variant_dict.items():
            entry = {'variant_info': info}
            if var_id in protein_info_dict:
                entry['protein_info'] = protein_info_dict[var_id]
            variants.append(entry)

        print(f"[DEBUG] 整合完成，返回 {len(variants)} 条变异记录")
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
