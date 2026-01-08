# -*- coding: utf-8 -*-
from app.database import db
from datetime import datetime
import json

class LutClusterSnapshot(db.Model):
    """LUT聚类快照模型"""
    __tablename__ = 'lut_cluster_snapshots'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键ID')
    name = db.Column(db.String(200), nullable=False, comment='快照名称')
    description = db.Column(db.Text, comment='快照描述')
    metric = db.Column(db.String(50), nullable=False, comment='聚类指标')
    metric_name = db.Column(db.String(100), comment='聚类指标名称')
    algorithm = db.Column(db.String(50), nullable=False, comment='聚类算法')
    algorithm_name = db.Column(db.String(100), comment='聚类算法名称')
    n_clusters = db.Column(db.Integer, nullable=False, comment='聚类数')
    cluster_data_json = db.Column(db.Text, comment='聚类数据JSON（包含每个聚类的文件列表和统计信息）')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment='更新时间')
    
    def to_dict(self):
        cluster_data = None
        if self.cluster_data_json:
            try:
                cluster_data = json.loads(self.cluster_data_json)
            except:
                pass
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'metric': self.metric,
            'metric_name': self.metric_name,
            'algorithm': self.algorithm,
            'algorithm_name': self.algorithm_name,
            'n_clusters': self.n_clusters,
            'cluster_data': cluster_data,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
