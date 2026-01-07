# -*- coding: utf-8 -*-
"""
创建lut_applied_image_preferences表的脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.lut_applied_image_preference import LutAppliedImagePreference
import traceback

def create_table():
    """创建表"""
    app = create_app()
    with app.app_context():
        try:
            # 创建表
            db.create_all()
            print("表创建成功：lut_applied_image_preferences")
        except Exception as e:
            print(f"创建表失败: {traceback.format_exc()}")
            raise

if __name__ == '__main__':
    print("=" * 60)
    print("开始创建lut_applied_image_preferences表")
    print("=" * 60)
    create_table()
    print("\n创建完成！")
