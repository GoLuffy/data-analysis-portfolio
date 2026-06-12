"""
数据质量评估报告
输出：数据画像、缺失值分析、异常值标记
"""

import os 
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def get_db_engine():
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    dbname = os.getenv('DB_NAME', 'bi_project')
    user = os.getenv('DB_USER', 'biadmin')
    password = os.getenv('DB_PASSWROD', 'Bi_2026#PgSql!')
    conn_str = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(conn_str)


def generate_quality_report():
    engine = get_db_engine()

    # 读取raw层数据
    df = pd.read_sql("select * from raw.visit_records", engine)

    print("=" * 60)
    print("数据质量报告")
    print("="*60)

    # 1.基础信息
    print("\n【1.基础信息】")
    print(f"总记录数: {len(df)}")
    print(f"总列数: {len(df.columns)}")
    print(f"日期范围: {df['date'].min()} ~ {df['date'].max()}")

    # 2.缺失值分析
    print("\n【2.缺失值分析】")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({
        '缺失数': missing,
        '缺失率%': missing_pct
    })
    print(missing_df[missing_df['缺失数'] > 0])

    # 3. 业务规则校验
    print("/n【3.业务规则校验】")

    # 规则1：取消订单不应计入完成回访
    cancelled_completed = df[(df['is_cancelled']) &
                             (df['is_completed'])]
    print(f"取消订单但被标记完成：{len(cancelled_completed)} 条")

    # 规则2：未完成的记录不应有响应时长
    incomplete_with_time = df[(~df['is_completed']) &
                              (df['response_minutes'].notna())]
    print(f"未完成但有响应时长：{len(incomplete_with_time)} 条")

    # 规则3：响应时长异常值（超过2小时或小于1分钟）
    time_outliers = df[(df['response_minutes'] > 120) |
                       (df['response_minutes'] < 1)]
    print(f"响应时长异常(>120min或<1min)：{len(time_outliers)} 条")

    # 规则4：满意度评分范围
    invalid_satisfaction = df[(df['satisfaction'].notna()) &
                              ((df['satisfaction'] < 1) |
                               (df['satisfaction'] > 5))]
    print(f"满意度评分超出 1-5 范围：{len(invalid_satisfaction)} 条")

    # 4. 重复值
    print("/n【4.重复值】")
    duplicates = df.duplicated().sum()
    print(f"完全重复记录：{duplicates} 条")

    # 5. 数据类型检查
    print("\n【数据类型检查】")
    print(df.dtypes)

    return df


if __name__ == '__main__':
    generate_quality_report()


