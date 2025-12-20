# -*- coding: utf-8 -*-
"""
设置API
用于管理应用配置（存储在config.json中）
"""
from flask import Blueprint, request, jsonify, current_app
from app.utils.config_manager import get_config, save_config, get_local_image_dir, get_package_storage_dir
import os
import traceback

bp = Blueprint('settings', __name__)

@bp.route('/directory', methods=['GET'])
def get_directory_settings():
    """获取目录设置"""
    try:
        config = get_config()
        local_image_dir = config.get('local_image_dir', './storage/images')
        
        # 返回绝对路径和相对路径
        absolute_path = get_local_image_dir()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'local_image_dir': local_image_dir,  # 用户设置的路径（可能是相对或绝对）
                'absolute_path': absolute_path,  # 解析后的绝对路径
                'exists': os.path.exists(absolute_path)  # 目录是否存在
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取目录设置失败: {error_detail}")
        return jsonify({
            'code': 500,
            'message': f'获取目录设置失败: {str(e)}',
            'detail': error_detail
        }), 500

@bp.route('/directory', methods=['PUT'])
def update_directory_settings():
    """更新目录设置"""
    try:
        data = request.get_json()
        local_image_dir = data.get('local_image_dir')
        
        if not local_image_dir:
            return jsonify({
                'code': 400,
                'message': '目录路径不能为空'
            }), 400
        
        # 去除首尾空格
        local_image_dir = local_image_dir.strip()
        
        # 验证路径格式（基本验证）
        if not local_image_dir:
            return jsonify({
                'code': 400,
                'message': '目录路径不能为空'
            }), 400
        
        # 读取当前配置
        config = get_config()
        config['local_image_dir'] = local_image_dir
        
        # 保存配置
        if save_config(config):
            # 验证新路径
            absolute_path = get_local_image_dir()
            
            return jsonify({
                'code': 200,
                'message': '目录设置更新成功',
                'data': {
                    'local_image_dir': local_image_dir,
                    'absolute_path': absolute_path,
                    'exists': os.path.exists(absolute_path)
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': '保存配置失败'
            }), 500
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新目录设置失败: {error_detail}")
        return jsonify({
            'code': 500,
            'message': f'更新目录设置失败: {str(e)}',
            'detail': error_detail
        }), 500

@bp.route('/package-directory', methods=['GET'])
def get_package_directory_settings():
    """获取打包目录设置"""
    try:
        config = get_config()
        package_storage_dir = config.get('package_storage_dir', './storage/packages')
        
        # 返回绝对路径和相对路径
        absolute_path = get_package_storage_dir()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'package_storage_dir': package_storage_dir,  # 用户设置的路径（可能是相对或绝对）
                'absolute_path': absolute_path,  # 解析后的绝对路径
                'exists': os.path.exists(absolute_path)  # 目录是否存在
            }
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"获取打包目录设置失败: {error_detail}")
        return jsonify({
            'code': 500,
            'message': f'获取打包目录设置失败: {str(e)}',
            'detail': error_detail
        }), 500

@bp.route('/package-directory', methods=['PUT'])
def update_package_directory_settings():
    """更新打包目录设置"""
    try:
        data = request.get_json()
        package_storage_dir = data.get('package_storage_dir')
        
        if not package_storage_dir:
            return jsonify({
                'code': 400,
                'message': '目录路径不能为空'
            }), 400
        
        # 去除首尾空格
        package_storage_dir = package_storage_dir.strip()
        
        # 验证路径格式（基本验证）
        if not package_storage_dir:
            return jsonify({
                'code': 400,
                'message': '目录路径不能为空'
            }), 400
        
        # 读取当前配置
        config = get_config()
        config['package_storage_dir'] = package_storage_dir
        
        # 保存配置
        if save_config(config):
            # 验证新路径
            absolute_path = get_package_storage_dir()
            
            return jsonify({
                'code': 200,
                'message': '打包目录设置更新成功',
                'data': {
                    'package_storage_dir': package_storage_dir,
                    'absolute_path': absolute_path,
                    'exists': os.path.exists(absolute_path)
                }
            })
        else:
            return jsonify({
                'code': 500,
                'message': '保存配置失败'
            }), 500
            
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"更新打包目录设置失败: {error_detail}")
        return jsonify({
            'code': 500,
            'message': f'更新打包目录设置失败: {str(e)}',
            'detail': error_detail
        }), 500

