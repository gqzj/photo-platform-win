# -*- coding: utf-8 -*-
"""检查图片文件是否存在"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.image import Image
from app.models.image_recycle import ImageRecycle

app = create_app()
with app.app_context():
    filename = "image_6878ecfd000000001202111f_1.jpg"
    
    # 检查images表
    img = Image.query.filter(Image.filename.like(f'%{filename}%')).first()
    if img:
        print(f"在images表中找到: ID={img.id}, filename={img.filename}, storage_path={img.storage_path}")
        full_path = os.path.join("F:\\ai_platform\\download_images", img.storage_path.replace('/', '\\'))
        print(f"完整路径: {full_path}")
        print(f"文件存在: {os.path.exists(full_path)}")
    else:
        print("在images表中未找到")
    
    # 检查recycle表
    recycle = ImageRecycle.query.filter(ImageRecycle.filename.like(f'%{filename}%')).first()
    if recycle:
        print(f"在recycle表中找到: ID={recycle.id}, filename={recycle.filename}, storage_path={recycle.storage_path}")
        full_path = os.path.join("F:\\ai_platform\\download_images", recycle.storage_path.replace('/', '\\'))
        print(f"完整路径: {full_path}")
        print(f"文件存在: {os.path.exists(full_path)}")
    else:
        print("在recycle表中未找到")

