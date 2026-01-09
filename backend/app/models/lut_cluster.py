# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime

class LutCluster(db.Model):
    """LUT聚类模型"""
    __tablename__ = 'lut_clusters'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cluster_id = db.Column(db.Integer, nullable=False, comment='聚类ID（0, 1, 2, ...）')
    parent_cluster_id = db.Column(db.Integer, nullable=True, comment='父聚类ID（NULL表示顶级聚类）')
    path = db.Column(db.String(500), nullable=True, comment='完整聚类路径（如"12", "12-6", "12-6-2"）')
    level = db.Column(db.Integer, nullable=True, comment='层级深度（0表示顶级聚类，1表示一级子聚类，以此类推）')
    cluster_name = db.Column(db.String(100), comment='聚类名称（可选）')
    lut_file_id = db.Column(db.Integer, db.ForeignKey('lut_files.id', ondelete='CASCADE'), nullable=False, comment='LUT文件ID')
    distance_to_center = db.Column(db.Float, nullable=True, comment='到聚类中心的距离')
    distilled = db.Column(db.Boolean, default=False, nullable=False, comment='是否被蒸馏（True: 已蒸馏，不再显示）')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    
    # 关联关系
    lut_file = db.relationship('LutFile', backref='clusters')
    
    __table_args__ = (
        db.Index('idx_cluster_id', 'cluster_id'),
        db.Index('idx_parent_cluster_id', 'parent_cluster_id'),
        db.Index('idx_lut_file_id', 'lut_file_id'),
        db.Index('idx_path', 'path'),  # path字段索引
        db.Index('idx_level', 'level'),  # level字段索引
    )
    
    def to_dict(self):
        # 生成显示用的聚类编号
        # 优先使用path字段，如果没有则使用parent_cluster_id-cluster_id格式
        if self.path:
            display_cluster_id = self.path
        else:
            display_cluster_id = str(self.cluster_id)
            if self.parent_cluster_id is not None:
                display_cluster_id = f"{self.parent_cluster_id}-{self.cluster_id}"
        
        return {
            'id': self.id,
            'cluster_id': self.cluster_id,
            'parent_cluster_id': self.parent_cluster_id,
            'path': self.path,  # 新增：完整路径
            'level': self.level,  # 新增：层级深度
            'display_cluster_id': display_cluster_id,  # 显示用的聚类编号
            'cluster_name': self.cluster_name,
            'lut_file_id': self.lut_file_id,
            'distance_to_center': self.distance_to_center,
            'distilled': self.distilled,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

