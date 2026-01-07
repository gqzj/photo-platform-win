# -*- coding: utf-8 -*-
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import traceback
import os
import tempfile
import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image

bp = Blueprint('tools', __name__)

# 允许的图片文件扩展名
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path, target_size=(256, 256)):
    """
    图片预处理：读取、灰度化、统一尺寸
    :param image_path: 图片路径
    :param target_size: 目标尺寸 (宽, 高)
    :return: 预处理后的灰度图（uint8格式，0-255）
    """
    # 读取图片（cv2.IMREAD_GRAYSCALE 直接读为灰度图）
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法读取图片：{image_path}，请检查路径是否正确")
    
    # 统一尺寸（插值方式选双线性插值，保证缩放质量）
    img_resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)
    
    # 确保是uint8格式（0-255）
    if img_resized.dtype != np.uint8:
        img_resized = img_resized.astype(np.uint8)
    
    return img_resized

def extract_histogram_feature(img):
    """
    提取灰度直方图特征
    :param img: 预处理后的灰度图（uint8格式，0-255）
    :return: 归一化的直方图特征向量（长度256）
    """
    # 计算直方图：bins=256对应灰度级0-255，range=(0,256)对应uint8格式的像素值
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    # 归一化直方图（消除图片尺寸影响，使用L2归一化）
    # 使用 cv2.normalize(hist, hist) 进行L2归一化（默认方式）
    hist_normalized = cv2.normalize(hist, hist).flatten()
    return hist_normalized

def _calculate_image_similarity(img_path1, img_path2):
    """
    计算两张图片的相似度（基于直方图+余弦相似度）
    :param img_path1: 第一张图片路径
    :param img_path2: 第二张图片路径
    :return: 相似度值（0-1，越接近1越相似）
    """
    # 预处理图片
    img1 = preprocess_image(img_path1)
    img2 = preprocess_image(img_path2)
    
    # 提取特征
    feat1 = extract_histogram_feature(img1)
    feat2 = extract_histogram_feature(img2)
    
    # 计算余弦相似度（reshape为2D数组，适配sklearn接口）
    similarity = cosine_similarity(feat1.reshape(1, -1), feat2.reshape(1, -1))[0][0]
    return float(similarity)

def _calculate_psnr(img_path1, img_path2):
    """
    计算两张图片的PSNR（峰值信噪比）
    :param img_path1: 第一张图片路径
    :param img_path2: 第二张图片路径
    :return: PSNR值（dB，值越大表示越相似，通常>30dB表示质量较好）
    """
    # 读取图片并转换为灰度图
    img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE)
    
    if img1 is None or img2 is None:
        raise ValueError("无法读取图片")
    
    # 确保两张图片尺寸相同
    if img1.shape != img2.shape:
        # 将img2调整为与img1相同的尺寸
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]), interpolation=cv2.INTER_LINEAR)
    
    # 转换为float64类型
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    # 计算均方误差（MSE）
    mse = np.mean((img1 - img2) ** 2)
    
    if mse == 0:
        # 如果MSE为0，说明两张图片完全相同，返回一个很大的值
        return float('inf')
    
    # 计算PSNR（对于8位图像，MAX_I = 255）
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    
    return float(psnr)

def _calculate_ssim(img_path1, img_path2):
    """
    计算两张图片的SSIM（结构相似性指数）
    :param img_path1: 第一张图片路径
    :param img_path2: 第二张图片路径
    :return: SSIM值（0-1，越接近1越相似）
    """
    # 读取图片并转换为灰度图
    img1 = cv2.imread(img_path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img_path2, cv2.IMREAD_GRAYSCALE)
    
    if img1 is None or img2 is None:
        raise ValueError("无法读取图片")
    
    # 确保两张图片尺寸相同
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]), interpolation=cv2.INTER_LINEAR)
    
    # 尝试使用scikit-image库
    try:
        from skimage.metrics import structural_similarity as ssim_func
        # 计算SSIM
        ssim_value = ssim_func(img1, img2, data_range=255)
        return float(ssim_value)
    except (ImportError, Exception) as e:
        # 如果没有scikit-image或计算失败，使用简化实现
        # 转换为float64类型
        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)
        
        # SSIM的简化计算（使用高斯窗口）
        # 常量
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        
        # 计算均值
        mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        # 计算方差和协方差
        sigma1_sq = cv2.GaussianBlur(img1 * img1, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2 * img2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
        
        # 计算SSIM
        ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
        ssim_value = np.mean(ssim_map)
        
        return float(ssim_value)

@bp.route('/image-similarity', methods=['POST'])
def calculate_image_similarity():
    """计算两张图片的相似度"""
    try:
        if 'image1' not in request.files or 'image2' not in request.files:
            return jsonify({'code': 400, 'message': '请上传两张图片'}), 400
        
        file1 = request.files['image1']
        file2 = request.files['image2']
        
        if file1.filename == '' or file2.filename == '':
            return jsonify({'code': 400, 'message': '图片文件不能为空'}), 400
        
        if not allowed_file(file1.filename) or not allowed_file(file2.filename):
            return jsonify({'code': 400, 'message': '不支持的图片格式，仅支持: jpg, jpeg, png, gif, bmp, webp'}), 400
        
        # 获取计算方法参数（默认为histogram）
        method = request.form.get('method', 'histogram')
        if method not in ['histogram', 'psnr', 'ssim']:
            return jsonify({'code': 400, 'message': '不支持的计算方法，支持的方法：histogram（灰度直方图）、psnr（峰值信噪比）、ssim（结构相似性）'}), 400
        
        # 创建临时文件保存上传的图片
        temp_dir = tempfile.gettempdir()
        temp_file1 = os.path.join(temp_dir, f"similarity_test_{os.urandom(8).hex()}_{secure_filename(file1.filename)}")
        temp_file2 = os.path.join(temp_dir, f"similarity_test_{os.urandom(8).hex()}_{secure_filename(file2.filename)}")
        
        try:
            # 保存上传的图片
            file1.save(temp_file1)
            file2.save(temp_file2)
            
            # 验证图片是否有效
            try:
                img1 = Image.open(temp_file1)
                img1.verify()
                img2 = Image.open(temp_file2)
                img2.verify()
            except Exception as e:
                return jsonify({'code': 400, 'message': f'无效的图片文件: {str(e)}'}), 400
            
            # 重新打开图片（verify后需要重新打开，用于获取图片信息）
            img1 = Image.open(temp_file1)
            img2 = Image.open(temp_file2)
            
            # 根据方法计算相似度
            try:
                if method == 'histogram':
                    similarity = _calculate_image_similarity(temp_file1, temp_file2)
                    similarity_percent = similarity * 100
                    result_value = similarity
                    result_percent = round(similarity_percent, 2)
                    method_name = '灰度直方图（余弦相似度）'
                elif method == 'psnr':
                    psnr_value = _calculate_psnr(temp_file1, temp_file2)
                    # PSNR值转换为0-1范围（假设>50dB为1，<20dB为0）
                    if psnr_value == float('inf'):
                        similarity = 1.0
                        similarity_percent = 100.0
                    else:
                        # 将PSNR值映射到0-1范围（30dB约为0.5，50dB约为1.0）
                        similarity = min(1.0, max(0.0, (psnr_value - 20) / 30))
                        similarity_percent = similarity * 100
                    result_value = psnr_value
                    result_percent = round(psnr_value, 2) if psnr_value != float('inf') else float('inf')
                    method_name = 'PSNR（峰值信噪比）'
                elif method == 'ssim':
                    ssim_value = _calculate_ssim(temp_file1, temp_file2)
                    similarity = ssim_value
                    similarity_percent = ssim_value * 100
                    result_value = ssim_value
                    result_percent = round(similarity_percent, 2)
                    method_name = 'SSIM（结构相似性）'
            except Exception as e:
                current_app.logger.error(f"计算相似度失败: {str(e)}")
                return jsonify({'code': 500, 'message': f'计算相似度失败: {str(e)}'}), 500
            
            # 获取图片信息
            img1_info = {
                'filename': file1.filename,
                'size': img1.size,
                'mode': img1.mode
            }
            img2_info = {
                'filename': file2.filename,
                'size': img2.size,
                'mode': img2.mode
            }
            
            return jsonify({
                'code': 200,
                'message': '计算成功',
                'data': {
                    'method': method,
                    'method_name': method_name,
                    'similarity': similarity,
                    'similarity_percent': round(similarity_percent, 2),
                    'result_value': result_value,
                    'result_percent': result_percent,
                    'image1': img1_info,
                    'image2': img2_info
                }
            })
            
        finally:
            # 清理临时文件
            try:
                if os.path.exists(temp_file1):
                    os.remove(temp_file1)
                if os.path.exists(temp_file2):
                    os.remove(temp_file2)
            except:
                pass
                
    except Exception as e:
        error_detail = traceback.format_exc()
        current_app.logger.error(f"计算图片相似度失败: {error_detail}")
        return jsonify({'code': 500, 'message': str(e), 'detail': error_detail}), 500
