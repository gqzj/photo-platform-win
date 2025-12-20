from app.database import db
from datetime import datetime

class Post(db.Model):
    """帖子模型"""
    __tablename__ = 'posts'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    post_id = db.Column(db.String(100), nullable=False, unique=True, comment='帖子ID')
    title = db.Column(db.String(500), comment='标题')
    content = db.Column(db.Text, comment='内容')
    author_id = db.Column(db.String(100), comment='作者ID')
    author_name = db.Column(db.String(200), comment='作者名称')
    author_follower_count = db.Column(db.String(255), default='0', comment='作者粉丝数')
    author_like_collect_count = db.Column(db.String(255), default='0', comment='作者获赞与收藏数')
    like_count = db.Column(db.String(255), default='0', comment='点赞数')
    comment_count = db.Column(db.String(255), default='0', comment='评论数')
    collect_count = db.Column(db.String(255), default='0', comment='收藏数')
    post_type = db.Column(db.String(20), default='normal', comment='帖子类型')
    tags = db.Column(db.JSON, comment='标签')
    search_keyword = db.Column(db.String(500), comment='搜索关键词')
    publish_time = db.Column(db.DateTime, comment='发布时间')
    crawl_time = db.Column(db.DateTime, default=datetime.now, comment='抓取时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'title': self.title,
            'content': self.content,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'author_follower_count': self.author_follower_count,
            'author_like_collect_count': self.author_like_collect_count,
            'like_count': self.like_count,
            'comment_count': self.comment_count,
            'collect_count': self.collect_count,
            'post_type': self.post_type,
            'tags': self.tags,
            'search_keyword': self.search_keyword,
            'publish_time': self.publish_time.strftime('%Y-%m-%d %H:%M:%S') if self.publish_time else None,
            'crawl_time': self.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if self.crawl_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

