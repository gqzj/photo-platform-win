from app.database import db
from datetime import datetime

class PostMedia(db.Model):
    """帖子媒体模型"""
    __tablename__ = 'post_media'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    post_id = db.Column(db.String(100), nullable=False, comment='帖子ID')
    media_type = db.Column(db.String(20), nullable=False, comment='媒体类型：image, video')
    media_url = db.Column(db.String(1000), nullable=False, comment='媒体URL')
    media_local_path = db.Column(db.String(500), comment='本地存储路径')
    thumbnail_url = db.Column(db.String(1000), comment='缩略图URL')
    file_size = db.Column(db.BigInteger, comment='文件大小（字节）')
    duration = db.Column(db.Integer, comment='时长（秒）')
    width = db.Column(db.Integer, comment='宽度')
    height = db.Column(db.Integer, comment='高度')
    sort_order = db.Column(db.Integer, default=0, comment='排序顺序')
    download_status = db.Column(db.String(20), default='pending', comment='下载状态：pending, success, failed')
    download_time = db.Column(db.DateTime, comment='下载时间')
    image_hash = db.Column(db.String(128), comment='图片哈希值')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'media_type': self.media_type,
            'media_url': self.media_url,
            'media_local_path': self.media_local_path,
            'thumbnail_url': self.thumbnail_url,
            'file_size': self.file_size,
            'duration': self.duration,
            'width': self.width,
            'height': self.height,
            'sort_order': self.sort_order,
            'download_status': self.download_status,
            'download_time': self.download_time.strftime('%Y-%m-%d %H:%M:%S') if self.download_time else None,
            'image_hash': self.image_hash,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }

