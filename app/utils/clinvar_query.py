import sqlite3

def normalize_variant_id(variant_id):
    """
    标准化 variant_id 为统一查询格式：
    - rsID → 去掉 rs 前缀
    - chrom:pos → 去掉 chr 前缀，确保 pos 是整数
    """
    if variant_id.startswith('rs'):
        return 'rs', variant_id[2:]
    elif ':' in variant_id:
        chrom, pos = variant_id.split(':')
        if chrom.startswith('chr'):
            chrom = chrom[3:]
        return 'loc', (chrom, int(pos))
    else:
        return 'unknown', variant_id

def query_clinvar(variant_id, db_path, db_type='primary'):
    """
    db_type: 'primary' 表示第一个库（字段包括 chrom, pos, rsid, ref, alt 等）
             'secondary' 表示备用库（字段包括 Chromosome, Start, rsid, ReferenceAlleleVCF, AlternateAlleleVCF 等）
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        id_type, parsed = normalize_variant_id(variant_id)
        rows = []

        if db_type == 'primary':
            if id_type == 'rs':
                cursor.execute("SELECT * FROM clinvar WHERE rsid = ?", (parsed,))
            elif id_type == 'loc':
                chrom, pos = parsed
                cursor.execute("SELECT * FROM clinvar WHERE chrom = ? AND pos = ?", (chrom, pos))
            rows = cursor.fetchall()

            if not rows:
                return None

            # 主库字段顺序为：
            # chrom, pos, rsid, ref, alt, gene, consequence, af_exac, af_tgp, clndn, clnsig
            row = rows[0]
            chrom, pos, rsid, ref, alt, gene, _, _, _, clndn, clnsig = row

            return {
                'Chromosome': f'chr{chrom}',
                'Pos': pos,
                'ID': f'rs{rsid}' if rsid else 'NA',
                'Ref': ref,
                'Alt': alt,
                'Gene': gene,
                'ClinvarDiseaseName': clndn or 'NA',
                'ClinicalSignificance': clnsig or 'Unknown',
            }

        elif db_type == 'secondary':
            if id_type == 'rs':
                cursor.execute("SELECT * FROM clinvar WHERE rsid = ?", (f'rs{parsed}',))
            elif id_type == 'loc':
                chrom, pos = parsed
                cursor.execute("SELECT * FROM clinvar WHERE Chromosome = ? AND Start = ?", (chrom, pos))
            rows = cursor.fetchall()

            if not rows:
                return None

            # 次库字段为：
            # GeneID, ClinicalSignificance, rsid, Chromosome, Start, Stop, ReferenceAlleleVCF, AlternateAlleleVCF
            row = rows[0]
            gene, clnsig, rsid, chrom, start, _, ref, alt = row

            return {
                'Chromosome': f'chr{chrom}',
                'Pos': start,
                'ID': rsid if rsid else 'NA',
                'Ref': ref,
                'Alt': alt,
                'Gene': None,
                'ClinvarDiseaseName': 'NA',
                'ClinicalSignificance': clnsig or 'Unknown',
            }

        else:
            return None

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return None
    finally:
        conn.close()

def query_with_fallback(variant_id):
    try:    
        result = query_clinvar(variant_id, db_path="data/clinvar/clinvar.db", db_type='primary')
        if result:
            return result

        result = query_clinvar(variant_id, db_path="data/clinvar/variant_summary.db", db_type='secondary')
        if result:
            result['Note'] = '来自次级数据库，准确性较低'
            return result

    except Exception as e:
        print(f"[ERROR] 查询失败: {e}")
        return {'variant_id': variant_id, 'clinvar': None}

