# -*- coding: utf-8 -*-
"""
特征风格定义模型
用于定义基于特征维度的风格，并生成子风格
"""
from app.database import db
from datetime import datetime
import json

class FeatureStyleDefinition(db.Model):
    """特征风格定义模型"""
    __tablename__ = 'feature_style_definitions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = db.Column(db.String(200), nullable=False, unique=True, comment='风格定义名称')
    description = db.Column(db.Text, comment='风格定义描述')
    dimensions_json = db.Column(db.Text, comment='维度定义JSON，格式：[{"dimension_name": "维度名", "values": ["值1", "值2"]}]')
    status = db.Column(db.String(50), nullable=False, default='active', comment='状态：active, inactive')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    sub_styles = db.relationship('FeatureStyleSubStyle', backref='feature_style_definition', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_sub_styles=False):
        """转换为字典"""
        dimensions_data = []
        if self.dimensions_json:
            try:
                dimensions_data = json.loads(self.dimensions_json) if isinstance(self.dimensions_json, str) else self.dimensions_json
            except:
                dimensions_data = []
        
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'dimensions': dimensions_data,
            'dimensions_json': self.dimensions_json,
            'status': self.status,
            'sub_style_count': self.sub_styles.count() if hasattr(self, 'sub_styles') else 0,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_sub_styles:
            result['sub_styles'] = [sub_style.to_dict() for sub_style in self.sub_styles.all()]
        
        return result


class FeatureStyleSubStyle(db.Model):
    """特征风格子风格模型"""
    __tablename__ = 'feature_style_sub_styles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    feature_style_definition_id = db.Column(db.Integer, db.ForeignKey('feature_style_definitions.id', ondelete='CASCADE'), nullable=False, comment='特征风格定义ID')
    name = db.Column(db.String(200), nullable=False, comment='子风格名称')
    dimension_values_json = db.Column(db.Text, comment='维度值组合JSON，格式：{"维度名1": "值1", "维度名2": "值2"}')
    description = db.Column(db.Text, comment='子风格描述')
    image_count = db.Column(db.Integer, nullable=False, default=0, comment='图片数量')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    images = db.relationship('FeatureStyleSubStyleImage', backref='sub_style', lazy='dynamic', cascade='all, delete-orphan')
    
    __table_args__ = (
        db.UniqueConstraint('feature_style_definition_id', 'name', name='uk_feature_style_sub_style'),
        db.Index('idx_feature_style_definition', 'feature_style_definition_id'),
    )
    
    def to_dict(self, include_images=False):
        """转换为字典"""
        dimension_values_data = {}
        if self.dimension_values_json:
            try:
                dimension_values_data = json.loads(self.dimension_values_json) if isinstance(self.dimension_values_json, str) else self.dimension_values_json
            except:
                dimension_values_data = {}
        
        result = {
            'id': self.id,
            'feature_style_definition_id': self.feature_style_definition_id,
            'name': self.name,
            'dimension_values': dimension_values_data,
            'dimension_values_json': self.dimension_values_json,
            'description': self.description or '',
            'image_count': self.image_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
        
        if include_images:
            result['images'] = [img.to_dict() for img in self.images.all()]
        
        return result


class FeatureStyleSubStyleImage(db.Model):
    """特征风格子风格图片模型"""
    __tablename__ = 'feature_style_sub_style_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sub_style_id = db.Column(db.Integer, db.ForeignKey('feature_style_sub_styles.id', ondelete='CASCADE'), nullable=False, comment='子风格ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, comment='图片ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 关联关系
    image = db.relationship('Image', backref='feature_style_sub_style_images')
    
    __table_args__ = (
        db.UniqueConstraint('sub_style_id', 'image_id', name='uk_sub_style_image'),
        db.Index('idx_sub_style', 'sub_style_id'),
        db.Index('idx_image', 'image_id'),
    )
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'id': self.id,
            'sub_style_id': self.sub_style_id,
            'image_id': self.image_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        
        if self.image:
            result['image'] = self.image.to_dict()
        
        return result
