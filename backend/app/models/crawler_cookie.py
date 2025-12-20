from app.database import db
from datetime import datetime

class CrawlerCookie(db.Model):
    """爬虫Cookie模型 - 匹配现有数据库表结构"""
    __tablename__ = 'crawler_cookies'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    platform = db.Column(db.String(100), nullable=False, comment='平台名称（如：xiaohongshu, douyin等）')
    note = db.Column(db.String(500), comment='备注')
    cookie_json = db.Column(db.Text, comment='Cookie JSON值')
    created_at = db.Column(db.DateTime, nullable=False, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, comment='更新时间')
    platform_account = db.Column(db.String(200), comment='平台账号')
    acquire_type = db.Column(db.String(20), nullable=False, comment='获取类型')
    login_method = db.Column(db.String(20), comment='登录方式')
    password = db.Column(db.Text, comment='密码')
    verification_code = db.Column(db.Text, comment='验证码')
    status = db.Column(db.String(20), nullable=False, comment='状态')
    last_error = db.Column(db.Text, comment='最后错误信息')
    fetched_at = db.Column(db.DateTime, comment='抓取时间')
    
    def to_dict(self, include_sensitive=False):
        """
        转换为字典
        :param include_sensitive: 是否包含敏感字段（password, verification_code）
        """
        result = {
            'id': self.id,
            'platform': self.platform,
            'note': self.note,
            'cookie_json': self.cookie_json,
            'platform_account': self.platform_account,
            'acquire_type': self.acquire_type,
            'login_method': self.login_method,
            'status': self.status,
            'last_error': self.last_error,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'fetched_at': self.fetched_at.strftime('%Y-%m-%d %H:%M:%S') if self.fetched_at else None
        }
        
        # 只有在明确要求时才返回敏感字段
        if include_sensitive:
            result['password'] = self.password
            result['verification_code'] = self.verification_code
        
        return result

