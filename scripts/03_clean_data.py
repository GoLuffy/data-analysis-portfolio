"""
数据清洗脚本
输入：raw.visit_records
输出：cleaned_visit_records
清洗规则：
1.取消订单不计入完成回访
2.未完成记录清除响应时长和满意度
3.响应时长异常值标记为null（待人工确认）
4.统一数据类型
5.添加清洗时间戳
"""
import os 
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def get_db_engine():
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME', 'bi_project')
    user = os.getenv('DB_USER', 'biadmin')
    password = os.getenv('DB_PASSWORD', '')
    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(conn_str)


def clean_data():
    engine = get_db_engine()

    # 读取原始数据
    print("正在读取 raw.visit_records ...")
    df = pd.read_sql("select * from raw.visit_records", engine)
    raw_count = len(df)

    # 清洗步骤 1：处理取消订单
    # 取消订单的is_completed 强制改为false
    df.loc[df['is_completed'], 'is_completed'] = False

    # 清洗步骤 2：未完成记录清除响应时长、解决状态、满意度
    incomplete_mask = ~df['is_completed']
    df.loc[incomplete_mask, 'response_minutes'] = None
    df.loc[incomplete_mask, 'is_resolved'] = None
    df.loc[incomplete_mask, 'satisfaction'] = None

    # 清洗步骤 3：响应时长异常值处理（>120分钟或<1分钟）
    # 标记为Null，保留原始值在备注字段（阶段二实现）
    time_mask = (df['response_minutes'] > 120) | (df['response_minutes'] < 1)
    df.loc[time_mask, 'response_minutes'] = None

    # 清洗步骤 4：统一数据类型
    df['date'] = pd.to_datetime(df['date']).dt.date
    df['planned_time'] = pd.to_datetime(df['planned_time']).dt.date
    df['is_completed'] = df['is_completed'].astype(bool)
    df['is_resolved'] = df['is_resolved'].astype('boolean')
    df['is_cancelled'] = df['is_cancelled'].astype(bool)
    df['satisfaction'] = df['satisfaction'].astype('Int64')

    # 清洗步骤 5：添加清洗时间戳
    df['etl_timestamp'] = datetime.now()

    # 清洗步骤 6：去重复（基于customer_id 和 planned_time)
    before_deldup = len(df)
    df = df.drop_duplicates(subset=['customer_id', 'planned_time'], keep='first')
    after_deldup = len(df)

    # 写入clean 层
    print("正在写入 cleaned.visit_records ...")
    df.to_sql(
        'visit_records',
        engine,
        schema='cleaned',
        if_exists='replace',
        index=False,
        method='multi',
        chunksize=1000
    )

    # 验证
    with engine.connect() as Conn:
        result = Conn.execute(text("select count(*) from cleaned.visit_records"))
        clean_count = result.scalar()

    print("\n" + "="*60)
    print("清洗报告")
    print("="*60)
    print(f"原始数据数：{raw_count}")
    print(f"去重删除：{before_deldup - after_deldup}")
    print(f"清洗后记录数: {clean_count}")
    print(f"数据留存率：{clean_count/raw_count*100:.1f}%")

    return df


if __name__ == '__main__':
    clean_data()