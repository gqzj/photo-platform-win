from app.database import db
from datetime import datetime
from app.models.feature import Feature

class FeatureGroup(db.Model):
    """特征组模型"""
    __tablename__ = 'feature_groups'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, unique=True, comment='特征组名称')
    description = db.Column(db.Text, comment='特征组描述')
    enabled = db.Column(db.Boolean, nullable=False, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    features = db.relationship(
        'Feature',
        secondary='feature_group_features',
        lazy='subquery',
        backref=db.backref('feature_groups', lazy=True)
    )
    
    def to_dict(self, include_features=True):
        """转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'enabled': self.enabled,
            'status': 'active' if self.enabled else 'inactive',  # 兼容前端
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_features:
            result['features'] = [feature.to_dict() for feature in self.features]
            result['feature_count'] = len(self.features)
        
        return result


class FeatureGroupFeature(db.Model):
    """特征组-特征关联模型"""
    __tablename__ = 'feature_group_features'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feature_group_id = db.Column(db.Integer, db.ForeignKey('feature_groups.id', ondelete='CASCADE'), nullable=False, comment='特征组ID')
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id', ondelete='CASCADE'), nullable=False, comment='特征ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 关联关系
    feature_group = db.relationship('FeatureGroup', backref='feature_group_features')
    feature = db.relationship('Feature', backref='feature_group_features')
    
    __table_args__ = (
        db.UniqueConstraint('feature_group_id', 'feature_id', name='uk_group_feature'),
    )

