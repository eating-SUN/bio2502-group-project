import sqlite3

DB_PATH = "data/clinvar/variant_summary.db"

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

        if variant_id.isdigit():
            cursor.execute("SELECT * FROM clinvar WHERE GeneID = ?", (variant_id,))
            rows = cursor.fetchall()

        elif str(variant_id).startswith('rs'):
            cursor.execute("SELECT * FROM clinvar WHERE rsid = ?", (variant_id,))

        elif ':' in str(variant_id):
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
        (GeneID, ClinicalSignificance, rsid, Chromosome, Start, Stop, ReferenceAlleleVCF, AlternateAlleleVCF) = row

        return {
            'Chromosome': Chromosome,
            'Start': Start,
            'Stop': Stop,
            'ID': rsid if rsid else 'NA',
            'Ref': ReferenceAlleleVCF if ReferenceAlleleVCF else 'NA',
            'Alt': AlternateAlleleVCF if AlternateAlleleVCF else 'NA',
            'ClinicalSignificance': ClinicalSignificance if ClinicalSignificance else 'Unknown',
            'Gene': GeneID if GeneID else 'Unknown',
        }

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return {'variant_id': variant_id, 'clinvar': None}

