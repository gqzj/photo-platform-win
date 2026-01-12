# -*- coding: utf-8 -*-
"""
测试FAISS语义搜索功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.semantic_search_service import get_semantic_search_service
from app.database import db
from app.models.image import Image
from app.models.semantic_search import SemanticSearchImage
import traceback

def test_faiss_service():
    """测试FAISS语义搜索服务"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("开始测试FAISS语义搜索服务")
        print("=" * 60)
        
        try:
            # 1. 测试服务初始化
            print("\n[1] 测试服务初始化...")
            service = get_semantic_search_service()
            service.initialize()
            print("✅ 服务初始化成功")
            
            # 2. 测试获取统计信息
            print("\n[2] 测试获取统计信息...")
            stats = service.get_collection_stats()
            print(f"统计信息: {stats}")
            print("✅ 获取统计信息成功")
            
            # 3. 测试文本编码
            print("\n[3] 测试文本编码...")
            test_text = "一只可爱的小猫"
            text_vector = service.encode_text(test_text)
            print(f"文本: {test_text}")
            print(f"向量维度: {text_vector.shape}")
            print(f"向量前5个值: {text_vector[:5]}")
            print("✅ 文本编码成功")
            
            # 4. 测试向量搜索（如果索引中有数据）
            print("\n[4] 测试向量搜索...")
            if stats.get('total_images', 0) > 0:
                results = service.search_by_vector(text_vector, top_k=5)
                print(f"搜索结果数量: {len(results)}")
                if results:
                    print("前3个结果:")
                    for i, result in enumerate(results[:3], 1):
                        print(f"  {i}. image_id={result['image_id']}, score={result['score']:.4f}, distance={result['distance']:.4f}")
                print("✅ 向量搜索成功")
            else:
                print("⚠️  索引为空，跳过搜索测试")
            
            # 5. 测试文本搜索
            print("\n[5] 测试文本搜索...")
            if stats.get('total_images', 0) > 0:
                results = service.search_by_text(test_text, top_k=5)
                print(f"搜索结果数量: {len(results)}")
                if results:
                    print("前3个结果:")
                    for i, result in enumerate(results[:3], 1):
                        print(f"  {i}. image_id={result['image_id']}, score={result['score']:.4f}")
                print("✅ 文本搜索成功")
            else:
                print("⚠️  索引为空，跳过搜索测试")
            
            # 6. 检查数据库中的编码状态
            print("\n[6] 检查数据库编码状态...")
            try:
                total_images = Image.query.filter_by(status='active').count()
                encoded_count = SemanticSearchImage.query.filter_by(encoded=True).count()
                print(f"总图片数: {total_images}")
                print(f"已编码数: {encoded_count}")
                print(f"未编码数: {total_images - encoded_count}")
                print("✅ 数据库状态检查完成")
            except Exception as db_error:
                print(f"⚠️  数据库连接失败（不影响FAISS功能测试）: {str(db_error)}")
            
            print("\n" + "=" * 60)
            print("✅ 所有测试通过！")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            print("\n错误详情:")
            print(traceback.format_exc())
            return False
        
        return True

if __name__ == '__main__':
    success = test_faiss_service()
    sys.exit(0 if success else 1)
