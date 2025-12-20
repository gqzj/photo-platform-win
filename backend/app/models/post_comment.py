from app.database import db
from datetime import datetime

class PostComment(db.Model):
    """帖子评论模型"""
    __tablename__ = 'post_comments'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    comment_id = db.Column(db.String(100), nullable=False, unique=True, comment='评论ID')
    post_id = db.Column(db.String(100), nullable=False, comment='帖子ID')
    parent_comment_id = db.Column(db.String(100), comment='父评论ID')
    user_id = db.Column(db.String(100), comment='用户ID')
    user_name = db.Column(db.String(200), comment='用户名称')
    user_avatar = db.Column(db.String(500), comment='用户头像')
    content = db.Column(db.Text, comment='评论内容')
    like_count = db.Column(db.Integer, default=0, comment='点赞数')
    reply_count = db.Column(db.Integer, default=0, comment='回复数')
    comment_time = db.Column(db.DateTime, comment='评论时间')
    crawl_time = db.Column(db.DateTime, default=datetime.now, comment='抓取时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'post_id': self.post_id,
            'parent_comment_id': self.parent_comment_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_avatar': self.user_avatar,
            'content': self.content,
            'like_count': self.like_count,
            'reply_count': self.reply_count,
            'comment_time': self.comment_time.strftime('%Y-%m-%d %H:%M:%S') if self.comment_time else None,
            'crawl_time': self.crawl_time.strftime('%Y-%m-%d %H:%M:%S') if self.crawl_time else None
        }

