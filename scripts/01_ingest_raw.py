import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def get_db_engine():
    """从环境变量构建数据库"""
    host = os.getenv('DB_HOST', 'local_host')
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME', 'bi_project')
    user = os.getenv('DB_USER', 'biadmin')
    password = os.getenv('DB_PASSWORD', 'Bi_2026#PgSql!')

    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(conn_str)


def ingest_csv_to_raw(csv_path='data/raw/visit_records.csv',
                      table_name='visit_records'):
    """读取csv并写入raw schema"""
    print(f"正在读取 {csv_path}...")
    df = pd.read_csv(csv_path)

    print(f"原始数据行数：{len(df)}")
    print(f"列名：{list(df.columns)}")

    # 写入raw层（如果表存在则替换，保证可重复运行）
    engine = get_db_engine()

    print(f"正在写入raw.{table_name}...")
    df.to_sql(
        table_name,
        engine,
        schema='raw',
        if_exists='replace',
        index=False,
        method='multi',
        chunksize=1000
    )

    # 验证写入结果
    with engine.connect() as conn:
        result = conn.execute(text(f"select count(*) from raw.{table_name}"))
        count = result.scalar()
        print(f"√ 成功写入raw.{table_name},共{count}行")

    return df


if __name__ == '__main__':
    df = ingest_csv_to_raw()




