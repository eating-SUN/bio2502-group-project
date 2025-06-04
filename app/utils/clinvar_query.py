import sqlite3

DB_PATH = "data/clinvar/clinvar.db"

def query_clinvar(variant_id):
    """
    支持三种查询方式：
    1. 匹配基因名（gene）
    2. 匹配 rsID（rs开头）
    3. 匹配染色体位置（chrom:pos）
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if variant_id.isalpha():  # 简单判断为基因名（全字母）
            cursor.execute("SELECT * FROM clinvar WHERE gene = ?", (variant_id,))
            rows = cursor.fetchall()

        elif variant_id.startswith('rs'):
            rs_num = variant_id[2:]  # 去掉rs前缀
            cursor.execute("SELECT * FROM clinvar WHERE rsid = ?", (rs_num,))
            rows = cursor.fetchall()

        elif ':' in variant_id:
            chrom, pos = variant_id.split(':')
            cursor.execute("SELECT * FROM clinvar WHERE chrom = ? AND pos = ?", (chrom, int(pos)))
            rows = cursor.fetchall()

        else:
            rows = []

        conn.close()

        if not rows:
            return None

        # 取第一条记录
        row = rows[0]
        # 根据表结构拆包
        chrom, pos, rsid, ref, alt, gene, consequence, af_exac, af_tgp, clndn, clnsig = row

        return {
            'Chromosome': f'chr{chrom}' if chrom.isdigit() else chrom,
            'Pos': pos,
            'ID': f'rs{rsid}' if rsid else 'NA',
            'Ref': ref,
            'Alt': alt,
            'Gene': gene,
            'Consequence': consequence,
            'AF_ExAC': af_exac,
            'AF_TGP': af_tgp,
            'ClinvarDiseaseName': clndn if clndn else 'NA',
            'ClinicalSignificance': clnsig if clnsig else 'Unknown'
        }

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return {'variant_id': variant_id, 'clinvar': None}

