import sqlite3, pathlib

def clear_all_and_shrink(db_path: str):
    """
    1. 删掉所有数据
    2. WAL 合并
    3. VACUUM 收缩文件
    """
    db_path = pathlib.Path(db_path).resolve()
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        # ① 查出所有用户表（排除 sqlite_ 系统表）
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [row[0] for row in cur.fetchall()]
        for tbl in tables:
            cur.execute(f"DELETE FROM {tbl};")   # 如外键约束先 PRAGMA foreign_keys=OFF;
        conn.commit()

        # ② 合并 WAL → 主库
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.commit()

        # ③ 回收空洞，文件瞬间瘦身
        cur.execute("VACUUM;")
        conn.commit()

# 一键调用
clear_all_and_shrink("ids.db")
print("✅ 数据已清空，文件已收缩")