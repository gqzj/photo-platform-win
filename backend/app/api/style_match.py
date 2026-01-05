# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.style import Style, StyleFeatureProfile, StyleImage
from app.models.feature import Feature
from app.models.image_tagging_result_detail import ImageTaggingResultDetail
from app.models.image import Image
from app.models.aesthetic_score import AestheticScore
from app.services.image_tagging_service import ImageTaggingService
from app.models.feature import Feature
import traceback
import json
import tempfile
import os
import requests
from werkzeug.utils import secure_filename

bp = Blueprint('style_match', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/upload-and-analyze', methods=['POST'])
def upload_and_analyze():
    """上传图片并分析特征"""
    try:
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传文件'}), 400
        
        file = request.files['file']
        
        # 检查文件名
        if file.filename == '':
            return jsonify({'code': 400, 'message': '文件名为空'}), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({'code': 400, 'message': '不支持的文件类型，仅支持: ' + ', '.join(ALLOWED_EXTENSIONS)}), 400
        
        # 获取特征ID列表（可选，如果不提供则分析所有启用的特征）
        feature_ids_str = request.form.get('feature_ids', '')
        if feature_ids_str:
            try:
                feature_ids = [int(id.strip()) for id in feature_ids_str.split(',') if id.strip()]
            except ValueError:
                return jsonify({'code': 400, 'message': '特征ID格式错误'}), 400
        else:
            # 如果没有指定特征，使用所有启用的特征
            features = Feature.query.filter_by(enabled=True).all()
            feature_ids = [f.id for f in features]
        
        if not feature_ids:
            return jsonify({'code': 400, 'message': '请选择至少一个特征'}), 400
        
        # 保存上传的文件到临时目录
        temp_dir = tempfile.gettempdir()
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, f"style_match_{os.urandom(8).hex()}_{filename}")
        
        try:
            file.save(temp_path)
            
            # 获取特征信息
            features = Feature.query.filter(Feature.id.in_(feature_ids), Feature.enabled == True).all()
            if not features:
                return jsonify({'code': 400, 'message': '未找到有效的特征'}), 400
            
            # 转换为字典列表
            features_list = [feature.to_dict() for feature in features]
            
            # 初始化打标服务
            tagging_service = ImageTaggingService()
            
            # 进行打标
            result = tagging_service.tag_image(temp_path, features_list)
            
            if result['success']:
                # 转换为字典格式 {feature_id: tagging_value}
                result_dict = {}
                tagging_result = result.get('result', {})
                for feature in features:
                    feature_id = feature.id
                    feature_name = feature.name
                    # 从打标结果中获取该特征的值
                    tagging_value = tagging_result.get(feature_name)
                    if tagging_value:
                        result_dict[feature_id] = tagging_value
                
                # 获取原图的美学评分（调用ArtiMuse接口）
                aesthetic_score = None
                try:
                    with open(temp_path, 'rb') as f:
                        files = {'image': f}
                        aesthetic_response = requests.post(
                            'http://localhost:5001/api/evaluate_score',
                            files=files,
                            timeout=300
                        )
                    if aesthetic_response.status_code == 200:
                        aesthetic_data = aesthetic_response.json()
                        aesthetic_score = aesthetic_data.get('aesthetic_score') or aesthetic_data.get('score')
                except Exception as e:
                    current_app.logger.warning(f"获取美学评分失败: {str(e)}")
                    aesthetic_score = None
                
                return jsonify({
                    'code': 200,
                    'message': '分析成功',
                    'data': {
                        'tagging_results': result_dict,
                        'aesthetic_score': aesthetic_score  # 原图的美学评分
                    }
                })
            else:
                return jsonify({
                    'code': 500,
                    'message': f'分析失败: {result.get("error", "未知错误")}'
                }), 500
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
                    
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"上传并分析图片失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

@bp.route('/calculate-match', methods=['POST'])
def calculate_match():
    """计算图片与风格的匹配度"""
    try:
        data = request.get_json()
        
        # 获取参数
        image_tagging_results = data.get('tagging_results', {})  # {feature_id: tagging_value}
        style_ids = data.get('style_ids', [])  # 要匹配的风格ID列表
        feature_weights = data.get('feature_weights', {})  # {feature_id: weight}
        use_aesthetic_score = data.get('use_aesthetic_score', False)  # 是否使用美学评分
        aesthetic_weight = float(data.get('aesthetic_weight', 0.4))  # 美学评分权重（0-1）
        original_aesthetic_score = data.get('original_aesthetic_score')  # 原图的美学评分（0-100）
        
        if not image_tagging_results:
            return jsonify({'code': 400, 'message': '图片特征分析结果不能为空'}), 400
        
        if not style_ids:
            return jsonify({'code': 400, 'message': '请选择至少一个风格'}), 400
        
        # 获取风格列表
        styles = Style.query.filter(Style.id.in_(style_ids)).all()
        if not styles:
            return jsonify({'code': 400, 'message': '未找到有效的风格'}), 400
        
        match_results = []
        
        for style in styles:
            # 获取风格的特征画像
            profiles = StyleFeatureProfile.query.filter_by(style_id=style.id).all()
            
            if not profiles:
                # 如果没有特征画像，跳过该风格
                continue
            
            # 计算匹配度
            total_match_score = 0.0
            total_weight = 0.0
            feature_matches = []  # 存储每个特征的匹配度
            
            for profile in profiles:
                feature_id = profile.feature_id
                
                # 获取该特征的权重（默认为1）
                weight = feature_weights.get(str(feature_id), feature_weights.get(feature_id, 1.0))
                
                # 获取图片中该特征的值
                image_feature_value = image_tagging_results.get(str(feature_id)) or image_tagging_results.get(feature_id)
                
                if not image_feature_value:
                    # 图片中没有该特征的值，跳过
                    continue
                
                # 解析特征分布
                distribution = None
                if profile.distribution_json:
                    try:
                        distribution = json.loads(profile.distribution_json) if isinstance(profile.distribution_json, str) else profile.distribution_json
                    except:
                        distribution = None
                
                if not distribution:
                    continue
                
                # 在分布中查找匹配的特征值
                matched_percentage = 0.0
                for dist_item in distribution:
                    if dist_item.get('value') == image_feature_value:
                        matched_percentage = dist_item.get('percentage', 0.0)
                        break
                
                # 计算该特征的匹配度：百分比 × 权重
                feature_match_score = matched_percentage * weight
                total_match_score += feature_match_score
                total_weight += weight
                
                feature_matches.append({
                    'feature_id': feature_id,
                    'feature_name': profile.feature_name,
                    'feature_value': image_feature_value,
                    'matched_percentage': matched_percentage,
                    'weight': weight,
                    'match_score': feature_match_score
                })
            
            # 归一化特征匹配分数（确保在0-1范围内）
            feature_normalized_score = (total_match_score / (total_weight * 100)) if total_weight > 0 else 0.0
            feature_normalized_score = max(0.0, min(1.0, feature_normalized_score))  # 限制在0-1范围内
            
            # 如果使用美学评分，计算最终匹配度
            if use_aesthetic_score and original_aesthetic_score is not None:
                # 将美学评分归一化到0-1范围（原图美学评分是0-100）
                aesthetic_normalized = float(original_aesthetic_score) / 100.0
                aesthetic_normalized = max(0.0, min(1.0, aesthetic_normalized))
                
                # 计算最终匹配度：特征匹配度 * (1 - 美学权重) + 美学评分归一化值 * 美学权重
                normalized_score = feature_normalized_score * (1.0 - aesthetic_weight) + aesthetic_normalized * aesthetic_weight
            else:
                normalized_score = feature_normalized_score
            
            # 转换为0-100范围用于显示和返回
            normalized_score_display = normalized_score * 100.0
            normalized_score_display = max(0.0, min(100.0, normalized_score_display))
            
            # 按匹配度排序，获取最高的三个特征
            feature_matches.sort(key=lambda x: x['match_score'], reverse=True)
            top_features = feature_matches[:3]
            
            # 计算风格图片集中每张图片的匹配度
            style_image_matches = []
            style_images = StyleImage.query.filter_by(style_id=style.id).all()
            
            for style_image in style_images:
                if not style_image.image:
                    continue
                
                image_id = style_image.image_id
                
                # 获取该图片的打标结果
                image_tagging_details = ImageTaggingResultDetail.query.filter_by(
                    image_id=image_id
                ).all()
                
                if not image_tagging_details:
                    continue
                
                # 构建图片特征值字典
                image_feature_values = {}
                for detail in image_tagging_details:
                    feature_id = detail.feature_id
                    tagging_value = detail.tagging_value
                    if tagging_value:
                        image_feature_values[feature_id] = tagging_value
                
                # 计算该图片的匹配度（使用相同的算法）
                image_total_match_score = 0.0
                image_total_weight = 0.0
                
                for profile in profiles:
                    feature_id = profile.feature_id
                    
                    # 获取该特征的权重
                    weight = feature_weights.get(str(feature_id), feature_weights.get(feature_id, 1.0))
                    
                    # 获取图片中该特征的值
                    image_feature_value = image_feature_values.get(feature_id)
                    
                    if not image_feature_value:
                        continue
                    
                    # 解析特征分布
                    distribution = None
                    if profile.distribution_json:
                        try:
                            distribution = json.loads(profile.distribution_json) if isinstance(profile.distribution_json, str) else profile.distribution_json
                        except:
                            distribution = None
                    
                    if not distribution:
                        continue
                    
                    # 在分布中查找匹配的特征值
                    matched_percentage = 0.0
                    for dist_item in distribution:
                        if dist_item.get('value') == image_feature_value:
                            matched_percentage = dist_item.get('percentage', 0.0)
                            break
                    
                    # 计算该特征的匹配度：百分比 × 权重
                    feature_match_score = matched_percentage * weight
                    image_total_match_score += feature_match_score
                    image_total_weight += weight
                
                # 归一化特征匹配分数（确保在0-1范围内）
                image_feature_normalized_score = (image_total_match_score / (image_total_weight * 100)) if image_total_weight > 0 else 0.0
                image_feature_normalized_score = max(0.0, min(1.0, image_feature_normalized_score))  # 限制在0-1范围内
                
                # 如果使用美学评分，需要获取该图片的美学评分
                if use_aesthetic_score:
                    # 查询该图片在该风格中的美学评分（获取最新的）
                    image_aesthetic_score_obj = AestheticScore.query.filter_by(
                        style_id=style.id,
                        image_id=image_id
                    ).order_by(AestheticScore.created_at.desc()).first()
                    
                    if image_aesthetic_score_obj and image_aesthetic_score_obj.score is not None:
                        # 将图片美学评分归一化到0-1范围（美学评分是0-100）
                        image_aesthetic_normalized = float(image_aesthetic_score_obj.score) / 100.0
                        image_aesthetic_normalized = max(0.0, min(1.0, image_aesthetic_normalized))
                        
                        # 计算最终匹配度：特征匹配度 * (1 - 美学权重) + 美学评分归一化值 * 美学权重
                        image_normalized_score = image_feature_normalized_score * (1.0 - aesthetic_weight) + image_aesthetic_normalized * aesthetic_weight
                    else:
                        # 如果没有美学评分，只使用特征匹配度
                        image_normalized_score = image_feature_normalized_score
                else:
                    image_normalized_score = image_feature_normalized_score
                
                # 转换为0-100范围用于显示
                image_normalized_score_display = image_normalized_score * 100.0
                image_normalized_score_display = max(0.0, min(100.0, image_normalized_score_display))
                
                style_image_matches.append({
                    'image_id': image_id,
                    'image': style_image.image.to_dict(),
                    'match_score': round(image_normalized_score_display / 100.0, 4)  # 返回0-1范围的值
                })
            
            # 按匹配分数排序，获取最高的三张图片
            style_image_matches.sort(key=lambda x: x['match_score'], reverse=True)
            top_images = style_image_matches[:3]
            
            match_results.append({
                'style_id': style.id,
                'style_name': style.name,
                'match_score': round(normalized_score_display / 100.0, 4),  # 返回0-1范围的值
                'total_match_score': round(total_match_score, 2),
                'total_weight': round(total_weight, 2),
                'top_features': [
                    {
                        'feature_name': f['feature_name'],
                        'feature_value': f['feature_value'],
                        'matched_percentage': round(f['matched_percentage'], 2),
                        'match_score': round(f['match_score'], 2)
                    }
                    for f in top_features
                ],
                'top_images': [
                    {
                        'image_id': img['image_id'],
                        'image': img['image'],
                        'match_score': img['match_score']
                    }
                    for img in top_images
                ]
            })
        
        # 按匹配分数排序
        match_results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify({
            'code': 200,
            'message': '计算成功',
            'data': {
                'results': match_results
            }
        })
        
    except Exception as e:
        db.session.rollback()
        error_detail = traceback.format_exc()
        current_app.logger.error(f"计算匹配度失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

