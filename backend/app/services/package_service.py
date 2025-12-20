# -*- coding: utf-8 -*-
"""
样本集打包服务
用于将样本集的图片和特征打包成压缩包
"""
import os
import json
import shutil
import zipfile
import logging
from datetime import datetime
from typing import Dict
from app.database import db
from app.models.sample_set import SampleSet, SampleSetFeature, SampleSetImage
from app.models.image import Image
from app.models.image_tagging_result import ImageTaggingResult
from app.models.feature import Feature
from app.utils.config_manager import get_local_image_dir, get_package_storage_dir

logger = logging.getLogger(__name__)

class PackageService:
    """样本集打包服务类"""
    
    def package_sample_set(self, sample_set_id: int) -> Dict:
        """
        打包样本集
        
        Args:
            sample_set_id: 样本集ID
            
        Returns:
            Dict: 打包结果
        """
        try:
            # 获取样本集
            sample_set = SampleSet.query.get(sample_set_id)
            if not sample_set:
                return {
                    'success': False,
                    'message': f'样本集不存在: {sample_set_id}'
                }
            
            # 检查样本集是否有图片
            if sample_set.image_count == 0:
                return {
                    'success': False,
                    'message': '样本集没有图片，无法打包'
                }
            
            # 更新打包状态为打包中
            sample_set.package_status = 'packing'
            db.session.commit()
            
            # 创建临时目录
            package_storage_dir = get_package_storage_dir()
            logger.info(f"打包存储目录: {package_storage_dir}")
            temp_dir = os.path.join(package_storage_dir, f'temp_{sample_set_id}_{int(datetime.now().timestamp())}')
            logger.info(f"创建临时目录: {temp_dir}")
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # 创建样本集目录
                sample_set_dir = os.path.join(temp_dir, f'sample_set_{sample_set_id}')
                logger.info(f"创建样本集目录: {sample_set_dir}")
                os.makedirs(sample_set_dir, exist_ok=True)
                
                # 创建images目录
                images_dir = os.path.join(sample_set_dir, 'images')
                logger.info(f"创建图片目录: {images_dir}")
                os.makedirs(images_dir, exist_ok=True)
                
                # 获取样本集的所有图片
                sample_set_images = SampleSetImage.query.filter_by(sample_set_id=sample_set_id).all()
                logger.info(f"获取到 {len(sample_set_images)} 张图片")
                
                # 获取图片存储基础目录
                storage_base = get_local_image_dir()
                logger.info(f"图片存储基础目录: {storage_base}")
                
                # 图片特征映射（用于生成JSON）
                image_features_map = {}
                
                # 复制图片文件
                copied_count = 0
                skipped_count = 0
                error_count = 0
                for idx, sample_set_image in enumerate(sample_set_images):
                    image = Image.query.get(sample_set_image.image_id)
                    if not image or not image.storage_path:
                        skipped_count += 1
                        logger.warning(f"图片 {idx+1}: 图片记录不存在或storage_path为空")
                        continue
                    
                    # 规范化图片路径
                    relative_path = image.storage_path.replace('\\', '/').lstrip('./').lstrip('.\\')
                    source_path = os.path.join(storage_base, relative_path)
                    source_path = os.path.normpath(source_path)
                    
                    if not os.path.exists(source_path) or not os.path.isfile(source_path):
                        skipped_count += 1
                        logger.warning(f"图片 {idx+1} (ID={image.id}): 文件不存在: {source_path}")
                        continue
                    
                    # 生成目标文件名（使用image_id作为文件名，保留扩展名）
                    file_ext = os.path.splitext(image.storage_path)[1] or '.jpg'
                    target_filename = f'image_{image.id}{file_ext}'
                    target_path = os.path.join(images_dir, target_filename)
                    
                    # 复制文件
                    try:
                        shutil.copy2(source_path, target_path)
                        copied_count += 1
                        if copied_count <= 5 or copied_count % 100 == 0:
                            logger.info(f"已复制 {copied_count} 张图片: {target_filename}")
                        
                        # 收集图片特征信息
                        image_features_map[image.id] = {
                            'image_id': image.id,
                            'filename': image.filename,
                            'keyword': image.keyword,
                            'storage_path': image.storage_path,
                            'features': {}
                        }
                    except Exception as e:
                        error_count += 1
                        logger.error(f"复制图片文件失败 (ID={image.id}): {source_path} -> {target_path}, 错误: {e}")
                        continue
                
                logger.info(f"图片复制完成: 成功={copied_count}, 跳过={skipped_count}, 错误={error_count}")
                
                # 获取样本集的特征配置
                features = SampleSetFeature.query.filter_by(sample_set_id=sample_set_id).all()
                feature_map = {f.feature_id: f for f in features}
                
                # 获取所有图片的打标结果
                image_ids = list(image_features_map.keys())
                if image_ids:
                    tagging_results = ImageTaggingResult.query.filter(
                        ImageTaggingResult.image_id.in_(image_ids),
                        ImageTaggingResult.feature_id.in_([f.feature_id for f in features])
                    ).all()
                    
                    # 按图片ID和特征ID分组，取最新的打标结果
                    from sqlalchemy import func
                    subquery = db.session.query(
                        ImageTaggingResult.image_id,
                        ImageTaggingResult.feature_id,
                        func.max(ImageTaggingResult.updated_at).label('max_updated_at')
                    ).filter(
                        ImageTaggingResult.image_id.in_(image_ids),
                        ImageTaggingResult.feature_id.in_([f.feature_id for f in features])
                    ).group_by(
                        ImageTaggingResult.image_id,
                        ImageTaggingResult.feature_id
                    ).subquery()
                    
                    latest_results = db.session.query(ImageTaggingResult).join(
                        subquery,
                        db.and_(
                            ImageTaggingResult.image_id == subquery.c.image_id,
                            ImageTaggingResult.feature_id == subquery.c.feature_id,
                            ImageTaggingResult.updated_at == subquery.c.max_updated_at
                        )
                    ).all()
                    
                    # 填充图片特征信息
                    for result in latest_results:
                        image_id = result.image_id
                        feature_id = result.feature_id
                        if image_id in image_features_map:
                            feature = feature_map.get(feature_id)
                            if feature:
                                image_features_map[image_id]['features'][feature.feature_name] = result.tagging_value
                
                # 生成图片特征JSON文件
                features_json_path = os.path.join(sample_set_dir, 'image_features.json')
                logger.info(f"生成图片特征JSON文件: {features_json_path}")
                with open(features_json_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'sample_set_id': sample_set_id,
                        'sample_set_name': sample_set.name,
                        'sample_set_description': sample_set.description,
                        'package_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'image_count': copied_count,
                        'images': list(image_features_map.values())
                    }, f, ensure_ascii=False, indent=2)
                logger.info(f"图片特征JSON文件已生成，包含 {len(image_features_map)} 张图片的特征信息")
                
                # 生成样本集配置JSON文件
                config_json_path = os.path.join(sample_set_dir, 'sample_set_config.json')
                logger.info(f"生成样本集配置JSON文件: {config_json_path}")
                config_data = {
                    'sample_set_id': sample_set.id,
                    'sample_set_name': sample_set.name,
                    'sample_set_description': sample_set.description,
                    'features': []
                }
                
                for feature in features:
                    feature_obj = Feature.query.get(feature.feature_id)
                    value_range = None
                    if feature.value_range:
                        try:
                            value_range = json.loads(feature.value_range) if isinstance(feature.value_range, str) else feature.value_range
                        except:
                            pass
                    
                    config_data['features'].append({
                        'feature_id': feature.feature_id,
                        'feature_name': feature.feature_name,
                        'value_type': feature.value_type,
                        'value_range': value_range
                    })
                
                with open(config_json_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=2)
                logger.info(f"样本集配置JSON文件已生成，包含 {len(config_data['features'])} 个特征配置")
                
                # 创建压缩包
                zip_filename = f'sample_set_{sample_set_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
                zip_path = os.path.join(package_storage_dir, zip_filename)
                logger.info(f"开始创建压缩包: {zip_path}")
                
                file_count = 0
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # 添加所有文件到压缩包
                    for root, dirs, files in os.walk(sample_set_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
                            file_count += 1
                
                logger.info(f"压缩包创建完成，包含 {file_count} 个文件")
                logger.info(f"临时目录: {temp_dir}")
                
                # 删除临时目录
                logger.info(f"删除临时目录: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"临时目录已删除")
                
                # 更新样本集打包状态（需要重新查询，因为可能在不同会话中）
                sample_set = SampleSet.query.get(sample_set_id)
                if sample_set:
                    sample_set.package_status = 'packed'
                    sample_set.package_path = zip_path
                    sample_set.packaged_at = datetime.now()
                    db.session.commit()
                    logger.info(f"样本集打包完成: sample_set_id={sample_set_id}, zip_path={zip_path}, copied_count={copied_count}")
                else:
                    logger.error(f"更新打包状态失败: 样本集不存在 {sample_set_id}")
                
                return {
                    'success': True,
                    'message': '打包完成',
                    'package_path': zip_path,
                    'copied_count': copied_count
                }
                
            except Exception as e:
                logger.error(f"打包过程中发生错误: {e}", exc_info=True)
                # 保留临时目录以便调试（注释掉删除操作）
                if os.path.exists(temp_dir):
                    logger.warning(f"保留临时目录以便调试: {temp_dir}")
                    # shutil.rmtree(temp_dir, ignore_errors=True)
                
                # 更新打包状态为失败（需要重新查询）
                try:
                    sample_set = SampleSet.query.get(sample_set_id)
                    if sample_set:
                        sample_set.package_status = 'failed'
                        db.session.commit()
                except Exception as db_error:
                    logger.error(f"更新打包状态失败: {db_error}", exc_info=True)
                
                raise e
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"打包样本集失败 {sample_set_id}: {e}", exc_info=True)
            
            # 确保更新打包状态
            try:
                sample_set = SampleSet.query.get(sample_set_id)
                if sample_set:
                    sample_set.package_status = 'failed'
                    db.session.commit()
            except:
                pass
            
            return {
                'success': False,
                'message': f'打包样本集失败: {str(e)}'
            }

