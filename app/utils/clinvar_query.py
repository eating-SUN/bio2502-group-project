import sqlite3

DB_PATH = "data/clinvar/clinvar.db"

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
        elif variant_id.startswith('rs'):
            cursor.execute("SELECT * FROM clinvar WHERE rsid = ?", (variant_id[2:],))
            rows = cursor.fetchall()

        # 情况3：匹配 CHR:POS
        elif ':' in variant_id:
            chrom, pos = variant_id.split(':')
            cursor.execute("SELECT * FROM clinvar WHERE Chromosome = ? AND Start = ?", (chrom, pos))
            rows = cursor.fetchall()

        else:
            rows = []

        conn.close()

        if not rows:
            return None

        row = rows[0]
        (chrom, pos, rsid, ref, alt, CLNDN, CLINSIG) = row

        return{
            'Chromosome': f'chr{chrom}',                                # chr1
            'Pos': pos,                                                 # 10176
            'ID': f'rs{rsid}' if rsid else 'NA',                        # rs3385321
            'Ref': ref if ref else 'NA',                                # AG
            'Alt': alt if alt else 'NA',                                # A
            'ClinvarDiseaseName': CLNDN if CLNDN else 'NA',             # Retinitis_pigmentosa
            'ClinicalSignificance': CLINSIG if CLINSIG else 'Unknown',  # Likely_benign
        }
        
    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return {'variant_id': variant_id, 'clinvar': None}

