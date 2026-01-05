# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class Style(db.Model):
    """风格定义模型"""
    __tablename__ = 'styles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = db.Column(db.String(200), nullable=False, unique=True, comment='风格名称')
    description = db.Column(db.Text, comment='风格描述')
    sample_set_id = db.Column(db.Integer, db.ForeignKey('sample_sets.id', ondelete='SET NULL'), comment='关联的样本集ID')
    status = db.Column(db.String(50), nullable=False, default='active', comment='状态：active, inactive')
    image_count = db.Column(db.Integer, nullable=False, default=0, comment='图片数量')
    processed_image_count = db.Column(db.Integer, nullable=False, default=0, comment='已处理图片数（美学评分）')
    total_image_count = db.Column(db.Integer, nullable=False, default=0, comment='图片总数（美学评分）')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    images = db.relationship('StyleImage', backref='style', lazy='dynamic', cascade='all, delete-orphan')
    feature_profiles = db.relationship('StyleFeatureProfile', backref='style', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_images=False, include_profiles=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'sample_set_id': self.sample_set_id,
            'status': self.status,
            'image_count': self.image_count,
            'processed_image_count': self.processed_image_count,
            'total_image_count': self.total_image_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_images:
            result['images'] = [img.to_dict() for img in self.images.all()]
        
        if include_profiles:
            result['feature_profiles'] = [profile.to_dict() for profile in self.feature_profiles.all()]
        
        return result


class StyleImage(db.Model):
    """风格图片模型"""
    __tablename__ = 'style_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, comment='风格ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, comment='图片ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 关联关系
    image = db.relationship('Image', backref='style_images')
    
    __table_args__ = (
        db.UniqueConstraint('style_id', 'image_id', name='uk_style_image'),
    )
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'id': self.id,
            'style_id': self.style_id,
            'image_id': self.image_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        
        if self.image:
            result['image'] = self.image.to_dict()
        
        return result


class StyleFeatureProfile(db.Model):
    """风格特征画像模型"""
    __tablename__ = 'style_feature_profiles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    style_id = db.Column(db.Integer, db.ForeignKey('styles.id', ondelete='CASCADE'), nullable=False, comment='风格ID')
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id', ondelete='CASCADE'), nullable=False, comment='特征ID')
    feature_name = db.Column(db.String(100), nullable=False, comment='特征名称')
    distribution_json = db.Column(db.Text, comment='特征分布JSON，存储每个特征值的数量')
    is_selected = db.Column(db.Boolean, nullable=False, default=False, comment='是否选中进入画像')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    feature = db.relationship('Feature', backref='style_feature_profiles')
    
    __table_args__ = (
        db.UniqueConstraint('style_id', 'feature_id', name='uk_style_feature'),
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        distribution_data = None
        if self.distribution_json:
            try:
                distribution_data = json.loads(self.distribution_json) if isinstance(self.distribution_json, str) else self.distribution_json
            except:
                distribution_data = None
        
        return {
            'id': self.id,
            'style_id': self.style_id,
            'feature_id': self.feature_id,
            'feature_name': self.feature_name,
            'distribution_json': self.distribution_json,
            'distribution': distribution_data,
            'is_selected': self.is_selected,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

