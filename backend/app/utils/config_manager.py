# -*- coding: utf-8 -*-
"""
配置文件管理工具
用于读取和写入config.json文件
"""
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# config.json文件路径（位于backend目录下）
CONFIG_FILE_PATH = Path(__file__).parent.parent.parent / 'config.json'

def get_config():
    """
    读取config.json配置
    
    Returns:
        dict: 配置字典，如果文件不存在则返回默认配置
    """
    try:
        if CONFIG_FILE_PATH.exists():
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        else:
            # 返回默认配置
            default_config = {
                'local_image_dir': './storage/images'
            }
            # 创建默认配置文件
            save_config(default_config)
            return default_config
    except Exception as e:
        logger.error(f"读取配置文件失败: {e}", exc_info=True)
        # 返回默认配置
        return {
            'local_image_dir': './storage/images'
        }

def save_config(config):
    """
    保存配置到config.json
    
    Args:
        config: 配置字典
    
    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保目录存在
        CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存配置
        with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        logger.info(f"配置文件保存成功: {CONFIG_FILE_PATH}")
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}", exc_info=True)
        return False

def get_local_image_dir():
    """
    获取本地图片存储目录（绝对路径）
    
    Returns:
        str: 图片存储目录的绝对路径
    """
    config = get_config()
    local_dir = config.get('local_image_dir', './storage/images')
    
    # 如果是相对路径，转换为绝对路径（相对于backend目录）
    if not os.path.isabs(local_dir):
        backend_dir = CONFIG_FILE_PATH.parent
        local_dir = os.path.abspath(os.path.join(backend_dir, local_dir))
    
    # 确保目录存在
    os.makedirs(local_dir, exist_ok=True)
    
    return local_dir

def get_relative_path(absolute_path):
    """
    将绝对路径转换为相对于配置目录的相对路径
    
    Args:
        absolute_path: 绝对路径
    
    Returns:
        str: 相对路径
    """
    try:
        config = get_config()
        base_dir = config.get('local_image_dir', './storage/images')
        
        # 如果base_dir是相对路径，转换为绝对路径
        if not os.path.isabs(base_dir):
            backend_dir = CONFIG_FILE_PATH.parent
            base_dir = os.path.abspath(os.path.join(backend_dir, base_dir))
        else:
            base_dir = os.path.abspath(base_dir)
        
        absolute_path = os.path.abspath(absolute_path)
        
        # 计算相对路径
        try:
            relative_path = os.path.relpath(absolute_path, base_dir)
            # 统一使用正斜杠
            relative_path = relative_path.replace('\\', '/')
            return relative_path
        except ValueError:
            # 如果路径不在base_dir下，返回原路径
            logger.warning(f"路径 {absolute_path} 不在基础目录 {base_dir} 下")
            return absolute_path
    except Exception as e:
        logger.error(f"计算相对路径失败: {e}", exc_info=True)
        return absolute_path

def get_package_storage_dir():
    """
    获取打包存储目录（绝对路径）
    
    Returns:
        str: 打包存储目录的绝对路径
    """
    config = get_config()
    package_dir = config.get('package_storage_dir', './storage/packages')
    
    # 如果是相对路径，转换为绝对路径（相对于backend目录）
    if not os.path.isabs(package_dir):
        backend_dir = CONFIG_FILE_PATH.parent
        package_dir = os.path.abspath(os.path.join(backend_dir, package_dir))
    
    # 确保目录存在
    os.makedirs(package_dir, exist_ok=True)
    
    return package_dir

