# -*- coding: utf-8 -*-
"""
为lut_clusters表添加path字段，用于存储完整的聚类路径
这样可以彻底解决多级子聚类的追溯问题
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database import db
from app.models.lut_cluster import LutCluster
from sqlalchemy import text

def add_path_field():
    """添加path字段并填充数据"""
    app = create_app()
    with app.app_context():
        try:
            # 1. 添加path字段
            print("正在添加path字段...")
            db.session.execute(text("""
                ALTER TABLE lut_clusters 
                ADD COLUMN path VARCHAR(500) NULL COMMENT '完整聚类路径（如"12", "12-6", "12-6-2"）'
            """))
            db.session.commit()
            print("path字段添加成功")
            
            # 2. 添加level字段（层级深度）
            print("正在添加level字段...")
            db.session.execute(text("""
                ALTER TABLE lut_clusters 
                ADD COLUMN level INT NULL COMMENT '层级深度（0表示顶级聚类，1表示一级子聚类，以此类推）'
            """))
            db.session.commit()
            print("level字段添加成功")
            
            # 3. 添加索引
            print("正在添加索引...")
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_path ON lut_clusters(path)
                """))
                db.session.commit()
                print("path索引添加成功")
            except Exception as e:
                print(f"path索引可能已存在: {e}")
                db.session.rollback()
            
            try:
                db.session.execute(text("""
                    CREATE INDEX idx_level ON lut_clusters(level)
                """))
                db.session.commit()
                print("level索引添加成功")
            except Exception as e:
                print(f"level索引可能已存在: {e}")
                db.session.rollback()
            
            # 4. 填充path和level字段
            print("正在填充path和level字段...")
            
            # 先处理顶级聚类（parent_cluster_id为NULL）
            print("处理顶级聚类...")
            top_level_clusters = db.session.execute(text("""
                SELECT DISTINCT cluster_id 
                FROM lut_clusters 
                WHERE parent_cluster_id IS NULL
            """)).fetchall()
            
            for row in top_level_clusters:
                cluster_id = row[0]
                path = str(cluster_id)
                level = 0
                db.session.execute(text("""
                    UPDATE lut_clusters 
                    SET path = :path, level = :level
                    WHERE cluster_id = :cluster_id AND parent_cluster_id IS NULL
                """), {
                    'path': path,
                    'level': level,
                    'cluster_id': cluster_id
                })
            db.session.commit()
            print(f"已处理 {len(top_level_clusters)} 个顶级聚类")
            
            # 然后处理子聚类（按层级深度逐层处理）
            max_level = 10  # 假设最多10层
            for current_level in range(1, max_level + 1):
                # 查找所有level为NULL且parent_cluster_id不为NULL的记录
                sub_clusters = db.session.execute(text("""
                    SELECT DISTINCT cluster_id, parent_cluster_id
                    FROM lut_clusters 
                    WHERE level IS NULL AND parent_cluster_id IS NOT NULL
                """)).fetchall()
                
                if len(sub_clusters) == 0:
                    break
                
                print(f"处理第 {current_level} 层子聚类，共 {len(sub_clusters)} 个...")
                
                for row in sub_clusters:
                    cluster_id = row[0]
                    parent_cluster_id = row[1]
                    
                    # 查找父聚类（优先选择有path的）
                    parent_record = db.session.execute(text("""
                        SELECT path, level
                        FROM lut_clusters 
                        WHERE cluster_id = :parent_cluster_id AND path IS NOT NULL
                        ORDER BY level ASC
                        LIMIT 1
                    """), {
                        'parent_cluster_id': parent_cluster_id
                    }).fetchone()
                    
                    if parent_record:
                        parent_path = parent_record[0]
                        parent_level = parent_record[1] if parent_record[1] is not None else 0
                        path = f"{parent_path}-{cluster_id}"
                        level = parent_level + 1
                    else:
                        # 如果找不到有path的父聚类，尝试查找任意父聚类
                        parent_record = db.session.execute(text("""
                            SELECT path, level, parent_cluster_id
                            FROM lut_clusters 
                            WHERE cluster_id = :parent_cluster_id
                            LIMIT 1
                        """), {
                            'parent_cluster_id': parent_cluster_id
                        }).fetchone()
                        
                        if parent_record and parent_record[0]:
                            # 父聚类有path
                            parent_path = parent_record[0]
                            parent_level = parent_record[1] if parent_record[1] is not None else 0
                            path = f"{parent_path}-{cluster_id}"
                            level = parent_level + 1
                        else:
                            # 父聚类没有path，使用简单格式
                            path = f"{parent_cluster_id}-{cluster_id}"
                            level = current_level
                    
                    # 更新所有匹配的记录
                    db.session.execute(text("""
                        UPDATE lut_clusters 
                        SET path = :path, level = :level
                        WHERE cluster_id = :cluster_id AND parent_cluster_id = :parent_cluster_id
                    """), {
                        'path': path,
                        'level': level,
                        'cluster_id': cluster_id,
                        'parent_cluster_id': parent_cluster_id
                    })
                
                db.session.commit()
                print(f"第 {current_level} 层处理完成")
            
            print("path和level字段填充完成")
            
            # 5. 将path字段设置为NOT NULL（可选，如果确定所有记录都已填充）
            # print("正在将path字段设置为NOT NULL...")
            # db.session.execute(text("""
            #     ALTER TABLE lut_clusters 
            #     MODIFY COLUMN path VARCHAR(500) NOT NULL COMMENT '完整聚类路径（如"12", "12-6", "12-6-2"）'
            # """))
            # db.session.commit()
            # print("path字段设置为NOT NULL成功")
            
            print("迁移完成！")
            
        except Exception as e:
            db.session.rollback()
            print(f"迁移失败: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    add_path_field()
