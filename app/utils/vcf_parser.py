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
            print("[ERROR] VCF 文件中无有效变异记录！请检查文件内容。")
            print(f"[DEBUG] VCF文件路径: {vcf_path}")
            print(f"[DEBUG] 文件头部示例: {str(vcf_reader.raw_header[:200])}")  # 输出部分头部信息
            return []

        # 调用 VEP 注释
        print(f"[DEBUG] 准备调用 run_vep，输出文件: {vep_output_file}")
        # 调用 VEP 后增加文件内容检查
        run_vep(vcf_path, vep_output_file)
        if not os.path.exists(vep_output_file):
            print(f"[ERROR] VEP 输出文件未生成！路径: {vep_output_file}")
            return []
        with open(vep_output_file) as f:
            line_count = sum(1 for _ in f)
            if line_count < 2:  # 至少包含标题行和数据行
                print(f"[ERROR] VEP 输出文件为空或格式错误！行数: {line_count}")
                return []
        print(f"[DEBUG] VEP 注释完成，输出文件是否存在: {os.path.exists(vep_output_file)}")

        # 解析 VEP 输出
        annotated_variants = parse_vep_output(vep_output_file)
        if not annotated_variants:
            print("[ERROR] VEP 注释结果为空！可能原因：")
            print("  - VCF文件格式与参考基因组不匹配（如染色体格式为'chr1' vs '1'）")
            print("  - VEP缓存未正确配置（检查缓存目录和版本）")
            print("  - 输入变异位于非编码区域")
            # 输出VEP文件前5行供调试
            with open(vep_output_file) as f:
                print("[DEBUG] VEP输出文件前5行:")
                for i in range(5):
                    print(f.readline().strip())
            return []
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
                print(f"[WARNING] 无法获取 UniProt 序列: {v['protein_id']}")
                print(f"[DEBUG] 尝试访问的URL: https://rest.uniprot.org/uniprotkb/{v['protein_id']}.fasta")
                continue

            ref_aa, pos, alt_aa = parse_hgvs_protein(v['hgvs_p'])
            if None in (ref_aa, pos, alt_aa):
                print(f"[WARNING] 解析失败: HGVS表达式={v['hgvs_p']}")
                print(f"[DEBUG] 原始蛋白质注释: {v}")
                continue

            # 检查突变位置有效性
            if pos < 1 or pos > len(seq):
                print(f"[WARNING] 无效突变位置: 序列长度={len(seq)}, 需求位置={pos}")
                continue

            mut_seq = mutate_sequence(seq, pos, alt_aa)
            if not mut_seq:
                print(f"[WARNING] 突变序列生成失败: pos={pos}, alt_aa={alt_aa}")
                continue

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

