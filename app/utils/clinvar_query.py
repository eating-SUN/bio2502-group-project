import sqlite3

DB_PATH = "data/clinvar/variant_summary.db"

def query_clinvar(variant_id):
    """
    支持三种查询方式：
    1. 直接匹配 GeneID
    2. 匹配 rsID（如 rs121908936）
    3. 匹配染色体位置（如 1:66926）
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 情况1：匹配 GeneID
        if variant_id.isdigit():
            cursor.execute("SELECT * FROM clinvar WHERE GeneID = ?", (variant_id,))
            rows = cursor.fetchall()

        # 情况2：匹配 rsID
        elif str(variant_id).startswith('rs'):
            cursor.execute("SELECT * FROM clinvar WHERE rsid = ?", (variant_id,))
            rows = cursor.fetchall()

        # 情况3：匹配 CHR:POS
        elif ':' in str(variant_id):
            chrom, pos = variant_id.split(':')
            cursor.execute("SELECT * FROM clinvar WHERE Chromosome = ? AND Start = ?", (chrom, pos))
            rows = cursor.fetchall()

        else:
            rows = []

        conn.close()

        if not rows:
            return {'variant_id': variant_id, 'clinvar': None}

        row = rows[0]
        (GeneID, ClinicalSignificance, rsid, Chromosome, Start, Stop, ReferenceAlleleVCF, AlternateAlleleVCF) = row

        return {
            'variant_id': variant_id,
            'clinvar': {
                'Chromosome': Chromosome,
                'Start': Start,
                'Stop': Stop,
                'ID': rsid if rsid else 'NA',
                'Ref': ReferenceAlleleVCF if ReferenceAlleleVCF else 'NA',
                'Alt': AlternateAlleleVCF if AlternateAlleleVCF else 'NA',
                'ClinicalSignificance': ClinicalSignificance if ClinicalSignificance else 'Unknown',
                'Gene': GeneID if GeneID else 'Unknown',
            }
        }

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return {'variant_id': variant_id, 'clinvar': None}

