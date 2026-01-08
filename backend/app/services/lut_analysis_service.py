# -*- coding: utf-8 -*-
"""
LUT文件分析服务
用于分析LUT文件并生成标签
"""
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)

class LutAnalysisService:
    """LUT分析服务类"""
    
    def __init__(self):
        pass
    
    def rgb2hsv(self, rgb):
        """将RGB数组转换为HSV数组（轻量版，无额外依赖）"""
        r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
        max_rgb = np.max(rgb, axis=1)
        min_rgb = np.min(rgb, axis=1)
        delta = max_rgb - min_rgb

        # 计算色调H（0~360）
        h = np.zeros_like(max_rgb, dtype=np.float64)
        mask_r = (max_rgb == r) & (delta > 0)
        h[mask_r] = 60 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6)
        mask_g = (max_rgb == g) & (delta > 0)
        h[mask_g] = 60 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2)
        mask_b = (max_rgb == b) & (delta > 0)
        h[mask_b] = 60 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4)

        # 计算饱和度S（0~1）
        s = np.where(max_rgb > 0, delta / max_rgb, 0.0)

        # 计算明度V（0~1）
        v = max_rgb

        return np.stack([h, s, v], axis=1)
    
    def read_cube_lut(self, file_path):
        """读取.cube文件，提取RGB映射数据和LUT尺寸"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [line.strip() for line in f if line.strip()]

            rgb_data = []
            lut_size = None

            for line in lines:
                # 跳过注释行
                if line.startswith('#'):
                    continue
                # 提取LUT尺寸
                if line.startswith('LUT_3D_SIZE'):
                    lut_size = int(line.split()[-1])
                    continue
                # 提取RGB数据（浮点数，0.0~1.0）
                try:
                    parts = line.split()
                    if len(parts) >= 3:
                        r, g, b = map(float, parts[:3])
                        rgb_data.append([r, g, b])
                except:
                    continue

            # 转换为numpy数组
            rgb_array = np.array(rgb_data, dtype=np.float64)
            return rgb_array, lut_size

        except Exception as e:
            logger.error(f"读取文件失败 {file_path}：{e}")
            return None, None
    
    def analyze_lut(self, file_path, check_interrupted=None):
        """
        分析LUT文件，返回标签信息
        
        Args:
            file_path: LUT文件路径
            check_interrupted: 可选的检查中断回调函数，如果返回True则立即中断分析
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("分析被用户中断")
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        # 读取LUT数据
        rgb_array, lut_size = self.read_cube_lut(file_path)
        
        if check_interrupted and check_interrupted():
            raise InterruptedError("分析被用户中断")
        
        if rgb_array is None or len(rgb_array) == 0:
            logger.warning(f"无法解析LUT文件: {file_path}")
            return {
                'tone': None,
                'saturation': None,
                'contrast': None,
                'h_mean': None,
                's_mean': None,
                's_var': None,
                'v_var': None,
                'contrast_rgb': None
            }
        
        if check_interrupted and check_interrupted():
            raise InterruptedError("分析被用户中断")
        
        # 转换为HSV
        hsv_array = self.rgb2hsv(rgb_array)
        
        if check_interrupted and check_interrupted():
            raise InterruptedError("分析被用户中断")
        
        h_mean = float(np.mean(hsv_array[:, 0]))  # 色调均值
        s_mean = float(np.mean(hsv_array[:, 1]))  # 饱和度均值
        s_var = float(np.var(hsv_array[:, 1]))    # 饱和度方差
        v_var = float(np.var(hsv_array[:, 2]))     # 明度方差

        # 计算对比度（RGB极值差）
        rgb_max = float(np.max(rgb_array))
        rgb_min = float(np.min(rgb_array))
        contrast_rgb = rgb_max - rgb_min
        
        if check_interrupted and check_interrupted():
            raise InterruptedError("分析被用户中断")

        # 判断色调（暖/冷/中性）
        tone = "中性调"
        if (0 <= h_mean <= 30) or (330 <= h_mean <= 360):
            tone = "暖调"
        elif 180 <= h_mean <= 240:
            tone = "冷调"

        # 判断饱和度（高/中/低）
        saturation = "中饱和"
        if s_mean < 0.2:
            saturation = "低饱和"
        elif s_mean > 0.6:
            # 饱和度波动大，归为中饱和
            saturation = "高饱和" if s_var <= 0.1 else "中饱和"

        # 判断对比度（高/中/低）
        contrast = "中对比"
        if contrast_rgb < 0.5 and v_var < 0.01:
            contrast = "低对比"
        elif contrast_rgb > 0.8 and v_var > 0.05:
            contrast = "高对比"

        return {
            'tone': tone,
            'saturation': saturation,
            'contrast': contrast,
            'h_mean': h_mean,
            's_mean': s_mean,
            's_var': s_var,
            'v_var': v_var,
            'contrast_rgb': contrast_rgb
        }
    
    def analyze_image(self, image_path, check_interrupted=None):
        """
        分析图片，返回标签信息（用于分析应用LUT后的结果图）
        
        Args:
            image_path: 图片文件路径
            check_interrupted: 可选的检查中断回调函数，如果返回True则立即中断分析
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("分析被用户中断")
        
        if not os.path.exists(image_path):
            logger.error(f"文件不存在: {image_path}")
            return None
        
        try:
            from PIL import Image
            import numpy as np
            
            # 加载图片
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 转换为numpy数组
            rgb_array = np.array(img, dtype=np.float64) / 255.0
            # 将2D数组转换为1D数组（每个像素一行）
            rgb_array = rgb_array.reshape(-1, 3)
            
            if check_interrupted and check_interrupted():
                raise InterruptedError("分析被用户中断")
            
            # 转换为HSV
            hsv_array = self.rgb2hsv(rgb_array)
            
            if check_interrupted and check_interrupted():
                raise InterruptedError("分析被用户中断")
            
            h_mean = float(np.mean(hsv_array[:, 0]))  # 色调均值
            s_mean = float(np.mean(hsv_array[:, 1]))  # 饱和度均值
            s_var = float(np.var(hsv_array[:, 1]))    # 饱和度方差
            v_var = float(np.var(hsv_array[:, 2]))     # 明度方差

            # 计算对比度（RGB极值差）
            rgb_max = float(np.max(rgb_array))
            rgb_min = float(np.min(rgb_array))
            contrast_rgb = rgb_max - rgb_min
            
            if check_interrupted and check_interrupted():
                raise InterruptedError("分析被用户中断")

            # 判断色调（暖/冷/中性）
            tone = "中性调"
            if (0 <= h_mean <= 30) or (330 <= h_mean <= 360):
                tone = "暖调"
            elif 180 <= h_mean <= 240:
                tone = "冷调"

            # 判断饱和度（高/中/低）
            saturation = "中饱和"
            if s_mean < 0.2:
                saturation = "低饱和"
            elif s_mean > 0.6:
                # 饱和度波动大，归为中饱和
                saturation = "高饱和" if s_var <= 0.1 else "中饱和"

            # 判断对比度（高/中/低）
            contrast = "中对比"
            if contrast_rgb < 0.5 and v_var < 0.01:
                contrast = "低对比"
            elif contrast_rgb > 0.8 and v_var > 0.05:
                contrast = "高对比"

            return {
                'tone': tone,
                'saturation': saturation,
                'contrast': contrast,
                'h_mean': h_mean,
                's_mean': s_mean,
                's_var': s_var,
                'v_var': v_var,
                'contrast_rgb': contrast_rgb
            }
        except Exception as e:
            logger.error(f"分析图片失败 {image_path}: {e}")
            return None
    
    def extract_7d_features(self, file_path, check_interrupted=None):
        """
        提取LUT文件的7维特征：HSV均值(3)+RGB方差(3)+全局对比度(1)
        
        Args:
            file_path: LUT文件路径
            check_interrupted: 可选的检查中断回调函数
        
        Returns:
            7维特征向量: [h_mean, s_mean, v_mean, r_var, g_var, b_var, contrast_rgb]
            如果失败返回None
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("特征提取被用户中断")
        
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        # 读取LUT数据
        rgb_array, lut_size = self.read_cube_lut(file_path)
        
        if check_interrupted and check_interrupted():
            raise InterruptedError("特征提取被用户中断")
        
        if rgb_array is None or len(rgb_array) == 0:
            logger.warning(f"无法解析LUT文件: {file_path}")
            return None
        
        # 转换为HSV
        hsv_array = self.rgb2hsv(rgb_array)
        
        if check_interrupted and check_interrupted():
            raise InterruptedError("特征提取被用户中断")
        
        # HSV均值（3维）
        h_mean = float(np.mean(hsv_array[:, 0]))
        s_mean = float(np.mean(hsv_array[:, 1]))
        v_mean = float(np.mean(hsv_array[:, 2]))
        
        # RGB方差（3维）
        r_var = float(np.var(rgb_array[:, 0]))
        g_var = float(np.var(rgb_array[:, 1]))
        b_var = float(np.var(rgb_array[:, 2]))
        
        # 全局对比度（1维）
        rgb_max = float(np.max(rgb_array))
        rgb_min = float(np.min(rgb_array))
        contrast_rgb = rgb_max - rgb_min
        
        # 返回7维特征向量
        features = [h_mean, s_mean, v_mean, r_var, g_var, b_var, contrast_rgb]
        
        logger.debug(f"提取7维特征: {features}")
        return features
    
    def extract_image_features(self, lut_file_path, standard_image_path, check_interrupted=None):
        """
        提取图像特征映射特征：将LUT应用到标准测试图，然后提取结果图的特征
        
        Args:
            lut_file_path: LUT文件路径
            standard_image_path: 标准测试图路径（standard.png）
            check_interrupted: 可选的检查中断回调函数
        
        Returns:
            特征向量（包含RGB直方图、HSV直方图等）或None
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("特征提取被用户中断")
        
        try:
            from app.services.lut_application_service import LutApplicationService
            import tempfile
            
            # 创建临时文件保存应用LUT后的图片
            temp_dir = tempfile.gettempdir()
            temp_output = os.path.join(temp_dir, f"lut_temp_{os.path.basename(lut_file_path)}.jpg")
            
            # 应用LUT到标准测试图
            lut_service = LutApplicationService()
            success, error_msg = lut_service.apply_lut_to_image(
                standard_image_path,
                lut_file_path,
                temp_output
            )
            
            if not success:
                logger.error(f"应用LUT失败: {error_msg}")
                return None
            
            if check_interrupted and check_interrupted():
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                raise InterruptedError("特征提取被用户中断")
            
            # 加载应用LUT后的图片
            from PIL import Image
            img = Image.open(temp_output)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 转换为numpy数组
            img_array = np.array(img, dtype=np.float64) / 255.0
            height, width = img_array.shape[:2]
            
            # 将2D数组转换为1D数组（每个像素一行）
            rgb_array = img_array.reshape(-1, 3)
            
            if check_interrupted and check_interrupted():
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                raise InterruptedError("特征提取被用户中断")
            
            # 转换为HSV
            hsv_array = self.rgb2hsv(rgb_array)
            
            if check_interrupted and check_interrupted():
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                raise InterruptedError("特征提取被用户中断")
            
            # 提取特征
            features = []
            
            # 1. RGB直方图特征（每个通道16个bins，共48维）
            r_hist, _ = np.histogram(rgb_array[:, 0], bins=16, range=(0, 1))
            g_hist, _ = np.histogram(rgb_array[:, 1], bins=16, range=(0, 1))
            b_hist, _ = np.histogram(rgb_array[:, 2], bins=16, range=(0, 1))
            # 归一化直方图
            r_hist = r_hist.astype(np.float64) / (height * width)
            g_hist = g_hist.astype(np.float64) / (height * width)
            b_hist = b_hist.astype(np.float64) / (height * width)
            features.extend(r_hist.tolist())
            features.extend(g_hist.tolist())
            features.extend(b_hist.tolist())
            
            # 2. HSV直方图特征（H: 18个bins, S: 8个bins, V: 8个bins，共34维）
            h_hist, _ = np.histogram(hsv_array[:, 0], bins=18, range=(0, 360))
            s_hist, _ = np.histogram(hsv_array[:, 1], bins=8, range=(0, 1))
            v_hist, _ = np.histogram(hsv_array[:, 2], bins=8, range=(0, 1))
            # 归一化直方图
            h_hist = h_hist.astype(np.float64) / (height * width)
            s_hist = s_hist.astype(np.float64) / (height * width)
            v_hist = v_hist.astype(np.float64) / (height * width)
            features.extend(h_hist.tolist())
            features.extend(s_hist.tolist())
            features.extend(v_hist.tolist())
            
            # 3. 统计特征（HSV均值、方差，共6维）
            h_mean = float(np.mean(hsv_array[:, 0]))
            s_mean = float(np.mean(hsv_array[:, 1]))
            v_mean = float(np.mean(hsv_array[:, 2]))
            h_var = float(np.var(hsv_array[:, 0]))
            s_var = float(np.var(hsv_array[:, 1]))
            v_var = float(np.var(hsv_array[:, 2]))
            features.extend([h_mean, s_mean, v_mean, h_var, s_var, v_var])
            
            # 4. RGB统计特征（均值、方差，共6维）
            r_mean = float(np.mean(rgb_array[:, 0]))
            g_mean = float(np.mean(rgb_array[:, 1]))
            b_mean = float(np.mean(rgb_array[:, 2]))
            r_var = float(np.var(rgb_array[:, 0]))
            g_var = float(np.var(rgb_array[:, 1]))
            b_var = float(np.var(rgb_array[:, 2]))
            features.extend([r_mean, g_mean, b_mean, r_var, g_var, b_var])
            
            # 5. 对比度特征（1维）
            rgb_max = float(np.max(rgb_array))
            rgb_min = float(np.min(rgb_array))
            contrast = rgb_max - rgb_min
            features.append(contrast)
            
            # 总共：48 + 34 + 6 + 6 + 1 = 95维特征
            
            # 清理临时文件
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
            logger.debug(f"提取图像特征映射特征: {len(features)}维")
            return features
            
        except InterruptedError:
            # 清理临时文件
            if 'temp_output' in locals() and os.path.exists(temp_output):
                os.remove(temp_output)
            raise
        except Exception as e:
            logger.error(f"提取图像特征映射特征失败 {lut_file_path}: {e}")
            # 清理临时文件
            if 'temp_output' in locals() and os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except:
                    pass
            return None
    
    def calculate_image_similarity_matrix(self, image_paths, check_interrupted=None):
        """
        计算多张图片之间的相似度矩阵（基于灰度直方图特征）
        
        Args:
            image_paths: 图片路径列表
            check_interrupted: 可选的检查中断回调函数
        
        Returns:
            相似度矩阵（numpy数组），值越大表示越相似
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("相似度计算被用户中断")
        
        try:
            import cv2
            from sklearn.metrics.pairwise import cosine_similarity
            
            n = len(image_paths)
            similarity_matrix = np.zeros((n, n))
            
            def preprocess_image_for_similarity(image_path, target_size=(256, 256)):
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
                hist_normalized = cv2.normalize(hist, hist).flatten()
                return hist_normalized
            
            # 提取每张图片的特征向量
            features_list = []
            for i, img_path in enumerate(image_paths):
                if check_interrupted and check_interrupted():
                    raise InterruptedError("相似度计算被用户中断")
                
                if not os.path.exists(img_path):
                    logger.warning(f"图片不存在: {img_path}")
                    # 使用零向量作为占位符
                    features_list.append(np.zeros(256))  # 256维灰度直方图特征
                    continue
                
                try:
                    # 预处理图片（灰度化、统一尺寸）
                    img = preprocess_image_for_similarity(img_path)
                    # 提取灰度直方图特征
                    features = extract_histogram_feature(img)
                    features_list.append(features)
                    
                except Exception as e:
                    logger.error(f"提取图片特征失败 {img_path}: {e}")
                    features_list.append(np.zeros(256))
            
            # 计算相似度矩阵（使用余弦相似度）
            features_array = np.array(features_list)
            similarity_matrix = cosine_similarity(features_array)
            
            logger.debug(f"计算相似度矩阵完成: {similarity_matrix.shape}")
            return similarity_matrix
            
        except InterruptedError:
            raise
        except Exception as e:
            logger.error(f"计算相似度矩阵失败: {e}")
            return None
    
    def calculate_ssim_similarity_matrix(self, image_paths, check_interrupted=None):
        """
        计算多张图片之间的SSIM相似度矩阵（优化版本：先统一预处理所有图片）
        
        Args:
            image_paths: 图片路径列表
            check_interrupted: 可选的检查中断回调函数
        
        Returns:
            相似度矩阵（numpy数组），值越大表示越相似（0-1范围）
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("相似度计算被用户中断")
        
        try:
            import cv2
            
            n = len(image_paths)
            similarity_matrix = np.eye(n)  # 对角线为1（自己与自己的相似度为1）
            
            # 优化：先统一预处理所有图片，避免重复读取和resize
            logger.info(f"开始预处理 {n} 张图片...")
            processed_images = []
            target_size = (256, 256)  # 统一尺寸，加快计算速度
            
            for i, img_path in enumerate(image_paths):
                if check_interrupted and check_interrupted():
                    raise InterruptedError("相似度计算被用户中断")
                
                try:
                    # 读取图片并转换为灰度图
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        logger.warning(f"无法读取图片: {img_path}")
                        processed_images.append(None)
                        continue
                    
                    # 统一尺寸（加快后续计算）
                    img_resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)
                    processed_images.append(img_resized)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"已预处理 {i + 1}/{n} 张图片")
                except Exception as e:
                    logger.warning(f"预处理图片失败 {img_path}: {e}")
                    processed_images.append(None)
            
            logger.info(f"图片预处理完成，开始计算SSIM相似度矩阵...")
            
            def calculate_ssim_pair(img1, img2):
                """计算两张已预处理图片的SSIM值"""
                if img1 is None or img2 is None:
                    return 0.0
                
                # 尝试使用scikit-image库（更快）
                try:
                    from skimage.metrics import structural_similarity as ssim_func
                    ssim_value = ssim_func(img1, img2, data_range=255)
                    return float(ssim_value)
                except (ImportError, Exception):
                    # 如果没有scikit-image或计算失败，使用简化实现
                    img1_f = img1.astype(np.float64)
                    img2_f = img2.astype(np.float64)
                    
                    # SSIM的简化计算（使用高斯窗口）
                    C1 = (0.01 * 255) ** 2
                    C2 = (0.03 * 255) ** 2
                    
                    # 计算均值
                    mu1 = cv2.GaussianBlur(img1_f, (11, 11), 1.5)
                    mu2 = cv2.GaussianBlur(img2_f, (11, 11), 1.5)
                    
                    mu1_sq = mu1 ** 2
                    mu2_sq = mu2 ** 2
                    mu1_mu2 = mu1 * mu2
                    
                    # 计算方差和协方差
                    sigma1_sq = cv2.GaussianBlur(img1_f * img1_f, (11, 11), 1.5) - mu1_sq
                    sigma2_sq = cv2.GaussianBlur(img2_f * img2_f, (11, 11), 1.5) - mu2_sq
                    sigma12 = cv2.GaussianBlur(img1_f * img2_f, (11, 11), 1.5) - mu1_mu2
                    
                    # 计算SSIM
                    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
                    ssim_value = np.mean(ssim_map)
                    
                    return float(ssim_value)
            
            # 计算所有图片对之间的SSIM值
            total_pairs = n * (n - 1) // 2
            processed_pairs = 0
            
            for i in range(n):
                if check_interrupted and check_interrupted():
                    raise InterruptedError("相似度计算被用户中断")
                
                for j in range(i + 1, n):
                    if check_interrupted and check_interrupted():
                        raise InterruptedError("相似度计算被用户中断")
                    
                    try:
                        ssim_value = calculate_ssim_pair(processed_images[i], processed_images[j])
                        similarity_matrix[i, j] = ssim_value
                        similarity_matrix[j, i] = ssim_value  # 对称矩阵
                        
                        processed_pairs += 1
                        # 每计算10%的进度输出一次日志
                        if processed_pairs % max(1, total_pairs // 10) == 0:
                            progress = (processed_pairs / total_pairs) * 100
                            logger.info(f"SSIM计算进度: {processed_pairs}/{total_pairs} ({progress:.1f}%)")
                    except Exception as e:
                        logger.warning(f"计算SSIM失败 (图片{i}, 图片{j}): {e}")
                        similarity_matrix[i, j] = 0.0
                        similarity_matrix[j, i] = 0.0
            
            logger.info(f"计算SSIM相似度矩阵完成: {similarity_matrix.shape}")
            return similarity_matrix
            
        except InterruptedError:
            raise
        except Exception as e:
            logger.error(f"计算SSIM相似度矩阵失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def calculate_euclidean_distance_matrix(self, image_paths, check_interrupted=None):
        """
        计算多张图片之间的欧氏距离矩阵（基于像素值）
        
        Args:
            image_paths: 图片路径列表
            check_interrupted: 可选的检查中断回调函数
        
        Returns:
            距离矩阵（numpy数组），值越小表示越相似
        """
        if check_interrupted and check_interrupted():
            raise InterruptedError("距离计算被用户中断")
        
        try:
            import cv2
            
            n = len(image_paths)
            distance_matrix = np.zeros((n, n))  # 初始化距离矩阵
            
            # 优化：先统一预处理所有图片，避免重复读取和resize
            logger.info(f"开始预处理 {n} 张图片（欧氏距离）...")
            processed_images = []
            target_size = (256, 256)  # 统一尺寸，加快计算速度
            
            for i, img_path in enumerate(image_paths):
                if check_interrupted and check_interrupted():
                    raise InterruptedError("距离计算被用户中断")
                
                try:
                    # 读取图片（RGB，不转换为灰度）
                    img = cv2.imread(img_path)
                    if img is None:
                        logger.warning(f"无法读取图片: {img_path}")
                        processed_images.append(None)
                        continue
                    
                    # 统一尺寸（加快后续计算）
                    img_resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)
                    processed_images.append(img_resized)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"已预处理 {i + 1}/{n} 张图片")
                except Exception as e:
                    logger.warning(f"预处理图片失败 {img_path}: {e}")
                    processed_images.append(None)
            
            logger.info(f"图片预处理完成，开始计算欧氏距离矩阵（向量化计算）...")
            
            # 过滤掉无效图片，并记录有效索引
            valid_indices = []
            valid_images = []
            for i, img in enumerate(processed_images):
                if img is not None:
                    valid_indices.append(i)
                    valid_images.append(img)
            
            if len(valid_images) == 0:
                logger.error("没有有效的图片可以计算距离")
                return None
            
            # 将所有有效图片转换为向量（展平）
            # 使用float32而不是float64以加快计算速度
            image_vectors = []
            for img in valid_images:
                img_flat = img.astype(np.float32).flatten()
                image_vectors.append(img_flat)
            
            # 转换为numpy数组（每行是一个图片向量）
            image_array = np.array(image_vectors)  # shape: (n_valid, height * width * channels)
            
            logger.info(f"开始向量化计算欧氏距离矩阵（{len(valid_images)} 张有效图片）...")
            
            # 使用向量化计算所有对之间的欧氏距离
            # 方法：使用numpy的广播机制
            # distance[i,j] = sqrt(sum((image_array[i] - image_array[j])^2))
            # 可以优化为：distance[i,j] = sqrt(sum((image_array[i] - image_array[j])^2))
            # 使用 (a-b)^2 = a^2 + b^2 - 2ab 的展开形式可以进一步优化
            
            # 计算每张图片的平方和（用于优化）
            squared_norms = np.sum(image_array ** 2, axis=1)  # shape: (n_valid,)
            
            # 使用向量化计算距离矩阵
            # distance[i,j] = sqrt(sum((image_array[i] - image_array[j])^2))
            # = sqrt(sum(image_array[i]^2) + sum(image_array[j]^2) - 2*sum(image_array[i]*image_array[j]))
            # = sqrt(squared_norms[i] + squared_norms[j] - 2*dot(image_array[i], image_array[j]))
            
            # 计算点积矩阵
            dot_product_matrix = np.dot(image_array, image_array.T)  # shape: (n_valid, n_valid)
            
            # 使用广播计算距离矩阵
            # 对于每对(i,j)，计算 sqrt(squared_norms[i] + squared_norms[j] - 2*dot_product_matrix[i,j])
            squared_norms_expanded_i = squared_norms[:, np.newaxis]  # shape: (n_valid, 1)
            squared_norms_expanded_j = squared_norms[np.newaxis, :]  # shape: (1, n_valid)
            
            # 计算距离的平方
            distance_squared = squared_norms_expanded_i + squared_norms_expanded_j - 2 * dot_product_matrix
            
            # 处理数值误差（可能产生负值）
            distance_squared = np.maximum(distance_squared, 0)
            
            # 计算距离（开平方根）
            valid_distance_matrix = np.sqrt(distance_squared)
            
            # 将结果填充到完整的距离矩阵中
            for idx_i, i in enumerate(valid_indices):
                for idx_j, j in enumerate(valid_indices):
                    if i == j:
                        distance_matrix[i, j] = 0.0
                    else:
                        distance_matrix[i, j] = float(valid_distance_matrix[idx_i, idx_j])
            
            # 对于无效图片，设置距离为无穷大
            for i in range(n):
                if i not in valid_indices:
                    for j in range(n):
                        if j != i:
                            distance_matrix[i, j] = float('inf')
                            distance_matrix[j, i] = float('inf')
            
            logger.info(f"计算欧氏距离矩阵完成: {distance_matrix.shape}")
            return distance_matrix
            
        except InterruptedError:
            raise
        except Exception as e:
            logger.error(f"计算欧氏距离矩阵失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

