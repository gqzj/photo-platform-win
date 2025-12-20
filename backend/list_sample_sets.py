# -*- coding: utf-8 -*-
"""
列出所有样本集
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app import create_app
from app.database import db
from app.models.sample_set import SampleSet

app = create_app()

with app.app_context():
    sample_sets = SampleSet.query.all()
    print(f"\n找到 {len(sample_sets)} 个样本集:\n")
    for ss in sample_sets:
        print(f"ID: {ss.id}, 名称: {ss.name}, 图片数量: {ss.image_count}, 打包状态: {ss.package_status}")
    print()

