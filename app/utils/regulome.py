import sqlite3

def query_score(position, db_path='./data/regulome/regulome.db'):
    try:
        rsid = position.get('rsid')
        chrom = position.get('chrom')
        start = position.get('start')
        end = position.get('end')

        key = rsid if rsid else f"{chrom}:{start}-{end}"
        print(f"[INFO][query_score] 查询位点 {key} 的 RegulomeDB 注释...")

        # 在当前线程中打开数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if rsid:
            cursor.execute("SELECT chrom, start, end, rsid, ranking, score FROM regulome WHERE rsid = ?", (rsid,))
        elif None not in (chrom, start, end):
            cursor.execute(
                "SELECT chrom, start, end, rsid, ranking, score FROM regulome WHERE chrom = ? AND start = ? AND end = ?",
                (chrom, start, end)
            )
        else:
            print(f"[WARNING][query_score] 位点信息不完整: {position}")
            return 'Invalid input'

        row = cursor.fetchone()
        conn.close()

        if not row:
            print(f"[INFO][query_score] RegulomeDB 无匹配记录: {key}")
            return 'Not Found'

        score_info = {
            'chrom': row[0],
            'start': row[1],
            'end': row[2],
            'rsid': row[3],
            'ranking': row[4],
            'probability_score': row[5]
        }
        print(f"[INFO][query_score] 成功找到 {key} 的注释: {score_info}")
        return score_info

    except Exception as e:
        print(f"[ERROR][query_score] 查询失败: {e}")
        return 'Error'



