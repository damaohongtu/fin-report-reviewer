"""
A股财报数据导入工具
从Excel文件导入财报数据到PostgreSQL数据库（ashare schema）
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, List, Optional
from pathlib import Path
import logging
from dotenv import load_dotenv
import os
import sys
from urllib.parse import urlparse
from tqdm import tqdm

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialDataImporter:
    """A股财报数据导入器"""
    
    # 基础字段映射：Excel字段名 -> 数据库字段名
    BASE_FIELD_MAPPING = {
        'Stkcd': 'stkcd',
        'ShortName': 'short_name',
        'Accper': 'accper',
        'Typrep': 'typrep',
        'IfCorrect': 'if_correct',
        'DeclareDate': 'declare_date',
    }
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初始化导入器
        
        Args:
            database_url: 数据库URL，格式：postgresql://user:password@host:port/database
                        如果不提供，则从环境变量读取
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("未找到数据库配置，请设置 DATABASE_URL 环境变量")
        
        self.conn = None
        self._parse_db_config()
    
    def _parse_db_config(self):
        """解析数据库配置"""
        parsed = urlparse(self.database_url)
        self.db_config = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password
        }
        logger.info(f"数据库配置: {self.db_config['user']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}")
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            logger.info("✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            logger.info("数据库连接已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
    
    def map_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        映射Excel列名到数据库字段名
        
        Args:
            df: 原始DataFrame
            
        Returns:
            列名已映射的DataFrame
        """
        column_mapping = self.BASE_FIELD_MAPPING.copy()
        
        # 对于财务指标字段（如A001101000, B001100000等），统一转为小写
        for col in df.columns:
            if col not in column_mapping:
                # 如果不在预定义映射中，转为小写
                column_mapping[col] = col.lower()
        
        # 重命名列
        df_mapped = df.rename(columns=column_mapping)
        
        logger.info(f"📋 列名映射完成，共 {len(df.columns)} 列")
        logger.debug(f"映射示例: {list(column_mapping.items())[:5]}")
        
        return df_mapped
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理
        
        Args:
            df: 原始DataFrame
            
        Returns:
            处理后的DataFrame
        """
        df_clean = df.copy()
        
        # 处理股票代码（补齐为6位）
        if 'stkcd' in df_clean.columns:
            df_clean['stkcd'] = df_clean['stkcd'].astype(str).str.zfill(6)
            logger.info(f"📋 股票代码格式化完成（补齐为6位）")
        
        # 处理日期字段
        if 'accper' in df_clean.columns:
            df_clean['accper'] = pd.to_datetime(df_clean['accper'], errors='coerce')
            logger.info(f"📅 日期字段处理完成")
        
        # 处理数值字段（将NaN转为None，以便插入NULL到数据库）
        numeric_cols = df_clean.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            df_clean[col] = df_clean[col].where(pd.notna(df_clean[col]), None)
        
        # 处理字符串字段（去除首尾空格）
        string_cols = df_clean.select_dtypes(include=['object']).columns
        for col in string_cols:
            if col not in ['accper']:  # 排除日期字段
                df_clean[col] = df_clean[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
        
        logger.info(f"🔧 数据预处理完成，共 {len(df_clean):,} 行")
        return df_clean
    
    def import_balance_sheet(self, excel_file: str, sheet_name: str = 'Sheet1'):
        """
        导入资产负债表
        
        Args:
            excel_file: Excel文件路径
            sheet_name: sheet名称
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 开始导入资产负债表: {excel_file}")
        logger.info(f"{'='*60}")
        
        # 读取Excel
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        logger.info(f"📖 读取Excel完成，共 {len(df)} 行, {len(df.columns)} 列")
        
        # 映射列名
        df_mapped = self.map_column_names(df)
        
        # 数据预处理
        df_clean = self.prepare_data(df_mapped)
        
        # 插入数据库
        self._batch_insert(df_clean, 'ashare.a_share_balance_sheet', 
                          primary_keys=['stkcd', 'accper', 'typrep'])
        
        logger.info(f"✅ 资产负债表导入完成\n")
    
    def import_income_statement(self, excel_file: str, sheet_name: str = 'Sheet1'):
        """
        导入利润表
        
        Args:
            excel_file: Excel文件路径
            sheet_name: sheet名称
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 开始导入利润表: {excel_file}")
        logger.info(f"{'='*60}")
        
        # 读取Excel
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        logger.info(f"📖 读取Excel完成，共 {len(df)} 行, {len(df.columns)} 列")
        
        # 映射列名
        df_mapped = self.map_column_names(df)
        
        # 数据预处理
        df_clean = self.prepare_data(df_mapped)
        
        # 插入数据库
        self._batch_insert(df_clean, 'ashare.a_share_income_statement',
                          primary_keys=['stkcd', 'accper', 'typrep'])
        
        logger.info(f"✅ 利润表导入完成\n")
    
    def import_cashflow_statement(self, excel_file: str, sheet_name: str = 'Sheet1'):
        """
        导入现金流量表
        
        Args:
            excel_file: Excel文件路径
            sheet_name: sheet名称
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 开始导入现金流量表: {excel_file}")
        logger.info(f"{'='*60}")
        
        # 读取Excel
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        logger.info(f"📖 读取Excel完成，共 {len(df)} 行, {len(df.columns)} 列")
        
        # 映射列名
        df_mapped = self.map_column_names(df)
        
        # 数据预处理
        df_clean = self.prepare_data(df_mapped)
        
        # 插入数据库
        self._batch_insert(df_clean, 'ashare.a_share_cashflow_statement',
                          primary_keys=['stkcd', 'accper', 'typrep'])
        
        logger.info(f"✅ 现金流量表导入完成\n")
    
    def _batch_insert(self, df: pd.DataFrame, table_name: str, 
                     primary_keys: List[str], batch_size: int = 500):
        """
        批量插入数据（支持冲突更新，优化大数据集处理）
        
        Args:
            df: 要插入的DataFrame
            table_name: 表名（包含schema）
            primary_keys: 主键字段列表
            batch_size: 批次大小（默认500，适合大数据集）
        """
        if df.empty:
            logger.warning("⚠️  DataFrame为空，跳过插入")
            return
        
        # 获取列名
        columns = df.columns.tolist()
        
        # 生成SQL
        placeholders = ', '.join(['%s'] * len(columns))
        columns_str = ', '.join(columns)
        
        # 使用ON CONFLICT处理主键冲突（更新数据）
        update_columns = [col for col in columns if col not in primary_keys and col not in ['created_at']]
        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])
        
        conflict_keys = ', '.join(primary_keys)
        
        sql = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT ({conflict_keys}) 
            DO UPDATE SET {update_str}, updated_at = CURRENT_TIMESTAMP
        """
        
        # 准备数据
        total_rows = len(df)
        logger.info(f"💾 准备插入 {total_rows:,} 条记录...")
        
        # 分批处理
        cursor = self.conn.cursor()
        success_count = 0
        error_count = 0
        
        try:
            # 分批处理数据（带进度条）
            for i in tqdm(range(0, total_rows, batch_size), 
                         desc="插入进度", 
                         unit="batch",
                         ncols=100):
                
                # 获取当前批次的数据
                batch_df = df.iloc[i:i+batch_size]
                batch_data = [tuple(x) for x in batch_df.to_numpy()]
                
                try:
                    # 插入当前批次
                    execute_batch(cursor, sql, batch_data, page_size=batch_size)
                    self.conn.commit()  # 每批次commit一次
                    success_count += len(batch_data)
                    
                except Exception as e:
                    self.conn.rollback()
                    error_count += len(batch_data)
                    logger.error(f"❌ 批次 {i//batch_size + 1} 插入失败: {str(e)[:100]}")
                    continue
            
            logger.info(f"✅ 成功插入/更新 {success_count:,} 条记录到 {table_name}")
            if error_count > 0:
                logger.warning(f"⚠️  {error_count:,} 条记录插入失败")
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 插入数据失败: {e}")
            raise
        finally:
            cursor.close()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='A股财报数据导入工具')
    parser.add_argument('--table', '-t', required=True, 
                       choices=['balance_sheet', 'income_statement', 'cashflow_statement', 'all'],
                       help='要导入的表类型')
    parser.add_argument('--file', '-f', required=True,
                       help='Excel文件路径')
    parser.add_argument('--sheet', '-s', default='Sheet1',
                       help='Excel工作表名称（默认：Sheet1）')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    if not Path(args.file).exists():
        logger.error(f"❌ 文件不存在: {args.file}")
        sys.exit(1)
    
    # 执行导入
    try:
        with FinancialDataImporter() as importer:
            if args.table == 'balance_sheet' or args.table == 'all':
                importer.import_balance_sheet(args.file, args.sheet)
            
            if args.table == 'income_statement' or args.table == 'all':
                importer.import_income_statement(args.file, args.sheet)
            
            if args.table == 'cashflow_statement' or args.table == 'all':
                importer.import_cashflow_statement(args.file, args.sheet)
        
        logger.info("\n" + "="*60)
        logger.info("🎉 所有数据导入完成！")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"\n❌ 导入过程中发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

