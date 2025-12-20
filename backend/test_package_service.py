# -*- coding: utf-8 -*-
"""
测试样本集打包服务
"""
import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_package.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_package_service(sample_set_id):
    """测试打包服务"""
    try:
        # 初始化Flask应用
        from app import create_app
        from app.database import db
        from app.models.sample_set import SampleSet, SampleSetImage
        from app.services.package_service import PackageService
        from app.utils.config_manager import get_package_storage_dir, get_local_image_dir
        
        app = create_app()
        
        with app.app_context():
            logger.info("=" * 60)
            logger.info(f"开始测试样本集打包功能，样本集ID: {sample_set_id}")
            logger.info("=" * 60)
            
            # 检查样本集是否存在
            sample_set = SampleSet.query.get(sample_set_id)
            if not sample_set:
                logger.error(f"样本集不存在: {sample_set_id}")
                return
            
            logger.info(f"样本集信息:")
            logger.info(f"  - ID: {sample_set.id}")
            logger.info(f"  - 名称: {sample_set.name}")
            logger.info(f"  - 描述: {sample_set.description}")
            logger.info(f"  - 图片数量: {sample_set.image_count}")
            logger.info(f"  - 打包状态: {sample_set.package_status}")
            
            # 检查是否有图片
            if sample_set.image_count == 0:
                logger.warning("样本集没有图片，无法打包")
                return
            
            # 获取样本集图片列表
            sample_set_images = SampleSetImage.query.filter_by(sample_set_id=sample_set_id).all()
            logger.info(f"样本集包含 {len(sample_set_images)} 张图片")
            
            # 显示前5张图片信息
            for i, ssi in enumerate(sample_set_images[:5]):
                from app.models.image import Image
                image = Image.query.get(ssi.image_id)
                if image:
                    logger.info(f"  图片 {i+1}: ID={image.id}, path={image.storage_path}")
            
            # 检查配置
            package_storage_dir = get_package_storage_dir()
            storage_base = get_local_image_dir()
            
            logger.info(f"\n配置信息:")
            logger.info(f"  - 打包存储目录: {package_storage_dir}")
            logger.info(f"  - 图片存储目录: {storage_base}")
            logger.info(f"  - 打包存储目录存在: {os.path.exists(package_storage_dir)}")
            logger.info(f"  - 图片存储目录存在: {os.path.exists(storage_base)}")
            
            # 检查前几张图片是否存在
            logger.info(f"\n检查图片文件:")
            checked_count = 0
            missing_count = 0
            for ssi in sample_set_images[:10]:
                from app.models.image import Image
                image = Image.query.get(ssi.image_id)
                if image and image.storage_path:
                    relative_path = image.storage_path.replace('\\', '/').lstrip('./').lstrip('.\\')
                    source_path = os.path.join(storage_base, relative_path)
                    source_path = os.path.normpath(source_path)
                    exists = os.path.exists(source_path) and os.path.isfile(source_path)
                    if exists:
                        checked_count += 1
                    else:
                        missing_count += 1
                        logger.warning(f"  图片不存在: {source_path}")
            
            logger.info(f"  检查了前10张图片，存在: {checked_count}, 不存在: {missing_count}")
            
            # 执行打包
            logger.info(f"\n开始执行打包...")
            service = PackageService()
            result = service.package_sample_set(sample_set_id)
            
            logger.info(f"\n打包结果:")
            logger.info(f"  - 成功: {result.get('success', False)}")
            logger.info(f"  - 消息: {result.get('message', '')}")
            if result.get('success'):
                logger.info(f"  - 压缩包路径: {result.get('package_path', '')}")
                logger.info(f"  - 复制图片数: {result.get('copied_count', 0)}")
                
                # 检查压缩包是否存在
                zip_path = result.get('package_path', '')
                if zip_path and os.path.exists(zip_path):
                    zip_size = os.path.getsize(zip_path)
                    logger.info(f"  - 压缩包大小: {zip_size / 1024 / 1024:.2f} MB")
                else:
                    logger.error(f"  - 压缩包不存在: {zip_path}")
            else:
                logger.error(f"  - 打包失败: {result.get('message', '')}")
            
            # 检查打包状态
            db.session.refresh(sample_set)
            logger.info(f"\n最终状态:")
            logger.info(f"  - 打包状态: {sample_set.package_status}")
            logger.info(f"  - 压缩包路径: {sample_set.package_path}")
            logger.info(f"  - 打包时间: {sample_set.packaged_at}")
            
            logger.info("=" * 60)
            logger.info("测试完成")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='测试样本集打包服务')
    parser.add_argument('sample_set_id', type=int, help='样本集ID')
    args = parser.parse_args()
    
    test_package_service(args.sample_set_id)

