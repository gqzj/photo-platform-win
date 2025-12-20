# -*- coding: utf-8 -*-
"""检查帖子媒体数据"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.post import Post
from app.models.post_media import PostMedia
from app.utils.config_manager import get_local_image_dir

app = create_app()

with app.app_context():
    post_id = 2944
    
    print(f"检查帖子 ID: {post_id}")
    print("=" * 60)
    
    # 检查帖子是否存在
    post = Post.query.get(post_id)
    if not post:
        print(f"[X] 帖子不存在 (ID: {post_id})")
    else:
        print(f"[OK] 帖子存在")
        print(f"  Post ID: {post.id}")
        print(f"  Post ID (platform): {post.post_id}")
        if post.title:
            try:
                print(f"  Title: {post.title}")
            except:
                print(f"  Title: (contains special characters)")
        print()
        
        # 检查媒体记录
        media_list = PostMedia.query.filter_by(
            post_id=post.post_id,
            media_type='image'
        ).order_by(PostMedia.sort_order).all()
        
        print(f"Media count: {len(media_list)}")
        print()
        
        if len(media_list) == 0:
            print("[X] No image media records")
        else:
            print("Media details:")
            for idx, media in enumerate(media_list):
                print(f"\n[{idx + 1}] Media ID: {media.id}")
                print(f"    Sort Order: {media.sort_order}")
                print(f"    Media Type: {media.media_type}")
                print(f"    Media URL: {media.media_url}")
                print(f"    Media Local Path: {media.media_local_path}")
                print(f"    Download Status: {media.download_status}")
                
                if media.media_local_path:
                    # 检查文件是否存在
                    relative_path = media.media_local_path.replace('\\', '/')
                    storage_base = get_local_image_dir()
                    relative_path = relative_path.lstrip('./').lstrip('.\\')
                    file_path = os.path.join(storage_base, relative_path)
                    file_path = os.path.normpath(file_path)
                    
                    print(f"    解析后路径: {file_path}")
                    exists = os.path.exists(file_path)
                    print(f"    文件存在: {'[OK]' if exists else '[X]'}")
                    
                    if not exists:
                        print(f"    [X] 文件不存在！")
                        print(f"    基础目录: {storage_base}")
                        print(f"    相对路径: {relative_path}")
            
            # 获取第一张图片（按sort_order排序）
            first_media = PostMedia.query.filter_by(
                post_id=post.post_id,
                media_type='image'
            ).order_by(PostMedia.sort_order).first()
            
            if first_media:
                print("\n" + "=" * 60)
                print("First image (sorted by sort_order):")
                print(f"  Media ID: {first_media.id}")
                print(f"  Sort Order: {first_media.sort_order}")
                print(f"  Media Local Path: {first_media.media_local_path}")
                
                if first_media.media_local_path:
                    relative_path = first_media.media_local_path.replace('\\', '/')
                    storage_base = get_local_image_dir()
                    relative_path = relative_path.lstrip('./').lstrip('.\\')
                    file_path = os.path.join(storage_base, relative_path)
                    file_path = os.path.normpath(file_path)
                    
                    print(f"  解析后路径: {file_path}")
                    exists = os.path.exists(file_path)
                    print(f"  文件存在: {'[OK]' if exists else '[X]'}")

