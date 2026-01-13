# -*- coding: utf-8 -*-
"""
测试Style模型
"""
from app import create_app
from app.models.style import Style
from app.database import db

app = create_app()
with app.app_context():
    # 检查表结构
    print("Style表的所有列:")
    for col in Style.__table__.columns:
        print(f"  {col.name}: {col.type}")
    
    # 测试查询
    try:
        count = Style.query.filter(Style.is_manual == True).count()
        print(f"\n查询成功，手工风格数量: {count}")
    except Exception as e:
        print(f"\n查询失败: {str(e)}")
        import traceback
        traceback.print_exc()
