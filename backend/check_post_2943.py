# -*- coding: utf-8 -*-
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db
from app.models.post import Post
from app.models.post_media import PostMedia
from app.utils.config_manager import get_local_image_dir

app = create_app()

with app.app_context():
    post_id = 2943
    
    print(f"检查帖子 ID: {post_id}")
    print("=" * 60)
    
    # 获取帖子
    post = Post.query.get(post_id)
    if not post:
        print(f"[X] 帖子不存在 (ID: {post_id})")
        sys.exit(1)
    
    print(f"[OK] 帖子存在")
    print(f"  Post ID: {post.post_id}")
    print(f"  标题: {post.title}")
    print(f"  作者: {post.author_name}")
    print()
    
    # 获取该帖子的第一张图片
    first_media = PostMedia.query.filter_by(
        post_id=post.post_id,
        media_type='image'
    ).order_by(PostMedia.sort_order).first()
    
    if not first_media:
        print("[X] 该帖子没有图片媒体")
        sys.exit(1)
    
    print(f"[OK] 找到媒体记录")
    print(f"  Media ID: {first_media.id}")
    print(f"  Media Type: {first_media.media_type}")
    print(f"  Media Local Path: {first_media.media_local_path}")
    print(f"  Media URL: {first_media.media_url}")
    print(f"  Sort Order: {first_media.sort_order}")
    print()
    
    if first_media.media_local_path:
        # 检查文件是否存在
        relative_path = first_media.media_local_path.replace('\\', '/')
        storage_base = get_local_image_dir()
        relative_path = relative_path.lstrip('./').lstrip('.\\')
        file_path = os.path.join(storage_base, relative_path)
        file_path = os.path.normpath(file_path)
        
        print(f"路径解析:")
        print(f"  配置的基础目录: {storage_base}")
        print(f"  相对路径: {relative_path}")
        print(f"  完整路径: {file_path}")
        print()
        
        exists = os.path.exists(file_path)
        print(f"文件存在: {'[OK]' if exists else '[X]'}")
        
        if exists:
            file_size = os.path.getsize(file_path)
            print(f"  文件大小: {file_size} 字节")
        else:
            print(f"  [X] 文件不存在!")
            print(f"  请检查路径是否正确")
    else:
        print("[X] media_local_path 为空")

