# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import tempfile
import traceback
from app.services.image_tagging_service import ImageTaggingService
from app.models.feature import Feature
import json

bp = Blueprint('image_tagging_test', __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/tag', methods=['POST'])
def tag_image():
    """上传图片并进行打标"""
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
        
        # 获取特征ID列表
        feature_ids_str = request.form.get('feature_ids', '')
        if not feature_ids_str:
            return jsonify({'code': 400, 'message': '请选择至少一个特征'}), 400
        
        try:
            feature_ids = [int(id.strip()) for id in feature_ids_str.split(',') if id.strip()]
        except ValueError:
            return jsonify({'code': 400, 'message': '特征ID格式错误'}), 400
        
        if not feature_ids:
            return jsonify({'code': 400, 'message': '请选择至少一个特征'}), 400
        
        # 获取特征信息
        features = Feature.query.filter(Feature.id.in_(feature_ids), Feature.enabled == True).all()
        if not features:
            return jsonify({'code': 400, 'message': '未找到有效的特征'}), 400
        
        # 转换为字典列表
        features_list = [feature.to_dict() for feature in features]
        
        # 保存上传的文件到临时目录
        temp_dir = tempfile.gettempdir()
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, f"tagging_test_{os.urandom(8).hex()}_{filename}")
        
        try:
            file.save(temp_path)
            
            # 初始化打标服务
            tagging_service = ImageTaggingService()
            
            # 进行打标
            result = tagging_service.tag_image(temp_path, features_list)
            
            if result['success']:
                return jsonify({
                    'code': 200,
                    'message': '打标成功',
                    'data': {
                        'filename': filename,
                        'features': features_list,
                        'tagging_result': result['result'],
                        'raw_response': result.get('raw_response', '')
                    }
                })
            else:
                return jsonify({
                    'code': 500,
                    'message': f'打标失败: {result.get("error", "未知错误")}',
                    'data': {
                        'filename': filename,
                        'error': result.get('error', '未知错误')
                    }
                }), 500
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    current_app.logger.warning(f"删除临时文件失败: {temp_path}, 错误: {e}")
                    
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"图片打标失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

