# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
import os
import tempfile
import traceback
from app.services.image_analysis_service import ImageAnalysisService

bp = Blueprint('image_cleaning_test', __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/analyze', methods=['POST'])
def analyze_image():
    """上传并分析图片"""
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
        
        # 获取要检测的特征（可选，默认检测所有特征）
        filter_features = request.form.get('filter_features', 'no_face,multiple_faces,contains_text,blurry')
        if isinstance(filter_features, str):
            filter_features = [f.strip() for f in filter_features.split(',') if f.strip()]
        
        # 保存上传的文件到临时目录
        temp_dir = tempfile.gettempdir()
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, f"cleaning_test_{os.urandom(8).hex()}_{filename}")
        
        try:
            file.save(temp_path)
            
            # 初始化分析服务
            analysis_service = ImageAnalysisService()
            
            # 分析图片
            result = analysis_service.analyze_image(temp_path, filter_features)
            
            # 获取详细信息
            details = result.get('details', {})
            matched_features = result.get('matched_features', [])
            
            # 转换 face_locations 为可序列化的格式（numpy 数组需要转换为列表）
            face_locations = details.get('face_locations', [])
            face_locations_serializable = []
            for loc in face_locations:
                if isinstance(loc, (list, tuple)):
                    # 确保每个坐标都是 Python 原生类型
                    face_locations_serializable.append([int(x) for x in loc])
                else:
                    face_locations_serializable.append(loc)
            
            # 转换 person_locations 为可序列化的格式
            person_locations = details.get('person_locations', [])
            person_locations_serializable = []
            for loc in person_locations:
                if isinstance(loc, (list, tuple)):
                    person_locations_serializable.append([int(x) for x in loc])
                else:
                    person_locations_serializable.append(loc)
            
            # 转换 text_locations 为可序列化的格式
            text_locations = details.get('text_locations', [])
            text_locations_serializable = []
            for loc in text_locations:
                if isinstance(loc, (list, tuple)):
                    text_locations_serializable.append([int(x) for x in loc])
                else:
                    text_locations_serializable.append(loc)
            
            # 构建返回结果，确保所有值都是 Python 原生类型
            analysis_result = {
                'matched_features': matched_features,
                'face_count': int(details.get('face_count', 0)),
                'face_locations': face_locations_serializable,
                'person_count': int(details.get('person_count', 0)),
                'person_locations': person_locations_serializable,
                'has_text': bool(details.get('has_text', False)),
                'text_locations': text_locations_serializable,
                'is_blur': bool(details.get('is_blur', False)),
                'blur_value': float(details.get('blur_value', 0.0))
            }
            
            # 特征映射（中文）
            feature_map = {
                'no_face': '无人脸',
                'multiple_faces': '多人脸',
                'no_person': '无人物',
                'multiple_persons': '多人物',
                'contains_text': '包含文字',
                'blurry': '图片模糊'
            }
            
            # 构建特征描述
            matched_features_cn = [feature_map.get(f, f) for f in matched_features]
            
            return jsonify({
                'code': 200,
                'message': '分析成功',
                'data': {
                    'filename': filename,
                    'analysis_result': analysis_result,
                    'matched_features_cn': matched_features_cn,
                    'summary': {
                        'face_count': analysis_result['face_count'],
                        'face_status': '无人脸' if analysis_result['face_count'] == 0 else f"{analysis_result['face_count']}张人脸",
                        'person_count': analysis_result['person_count'],
                        'person_status': '无人物' if analysis_result['person_count'] == 0 else f"{analysis_result['person_count']}个人物",
                        'text_status': '包含文字' if analysis_result['has_text'] else '不包含文字',
                        'blur_status': f"模糊 (值: {analysis_result['blur_value']:.2f})" if analysis_result['is_blur'] else f"清晰 (值: {analysis_result['blur_value']:.2f})"
                    }
                }
            })
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    current_app.logger.warning(f"删除临时文件失败: {temp_path}, 错误: {e}")
                    
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"图片分析失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500

