# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class SampleSet(db.Model):
    """样本集模型"""
    __tablename__ = 'sample_sets'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = db.Column(db.String(200), nullable=False, comment='样本集名称')
    description = db.Column(db.Text, comment='样本集描述')
    status = db.Column(db.String(50), nullable=False, default='active', comment='状态：active, inactive')
    image_count = db.Column(db.Integer, nullable=False, default=0, comment='图片数量')
    package_status = db.Column(db.String(50), nullable=False, default='unpacked', comment='打包状态：unpacked(未打包), packing(打包中), packed(已打包), failed(打包失败)')
    package_path = db.Column(db.String(500), comment='压缩包存储路径')
    packaged_at = db.Column(db.DateTime, comment='打包完成时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 关联关系
    features = db.relationship('SampleSetFeature', backref='sample_set', lazy='dynamic', cascade='all, delete-orphan')
    images = db.relationship('SampleSetImage', backref='sample_set', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        import json
        features_list = []
        for feature in self.features.all():
            features_list.append(feature.to_dict())
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or '',
            'status': self.status,
            'image_count': self.image_count,
            'package_status': self.package_status,
            'package_path': self.package_path,
            'packaged_at': self.packaged_at.strftime('%Y-%m-%d %H:%M:%S') if self.packaged_at else None,
            'features': features_list,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class SampleSetFeature(db.Model):
    """样本集特征模型"""
    __tablename__ = 'sample_set_features'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_set_id = db.Column(db.Integer, db.ForeignKey('sample_sets.id', ondelete='CASCADE'), nullable=False, comment='样本集ID')
    feature_id = db.Column(db.Integer, db.ForeignKey('features.id', ondelete='CASCADE'), nullable=False, comment='特征ID')
    feature_name = db.Column(db.String(100), nullable=False, comment='特征名称')
    value_range = db.Column(db.Text, comment='特征取值范围JSON')
    value_type = db.Column(db.String(50), nullable=False, default='enum', comment='值类型：enum, range, any')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    # 唯一约束：同一样本集的同一特征只能有一条记录
    __table_args__ = (
        db.UniqueConstraint('sample_set_id', 'feature_id', name='uk_sample_set_feature'),
        {'comment': '样本集特征表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        value_range_data = None
        if self.value_range:
            try:
                value_range_data = json.loads(self.value_range) if isinstance(self.value_range, str) else self.value_range
            except:
                value_range_data = self.value_range
        
        return {
            'id': self.id,
            'sample_set_id': self.sample_set_id,
            'feature_id': self.feature_id,
            'feature_name': self.feature_name,
            'value_range': value_range_data,
            'value_type': self.value_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

class SampleSetImage(db.Model):
    """样本集图片模型"""
    __tablename__ = 'sample_set_images'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sample_set_id = db.Column(db.Integer, db.ForeignKey('sample_sets.id', ondelete='CASCADE'), nullable=False, comment='样本集ID')
    image_id = db.Column(db.Integer, db.ForeignKey('images.id', ondelete='CASCADE'), nullable=False, comment='图片ID')
    matched_features = db.Column(db.Text, comment='匹配的特征JSON')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 唯一约束：同一样本集的同一图片只能有一条记录
    __table_args__ = (
        db.UniqueConstraint('sample_set_id', 'image_id', name='uk_sample_set_image'),
        {'comment': '样本集图片表'}
    )
    
    def to_dict(self):
        """转换为字典"""
        import json
        matched_features_data = None
        if self.matched_features:
            try:
                matched_features_data = json.loads(self.matched_features) if isinstance(self.matched_features, str) else self.matched_features
            except:
                matched_features_data = self.matched_features
        
        return {
            'id': self.id,
            'sample_set_id': self.sample_set_id,
            'image_id': self.image_id,
            'matched_features': matched_features_data,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

