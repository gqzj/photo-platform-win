# -*- coding: utf-8 -*-
"""
LUT提取服务
从图片集合中提取LUT文件（方法2）
"""
import numpy as np
from PIL import Image
import os
import logging
from typing import List, Tuple, Optional
from scipy.interpolate import RegularGridInterpolator

logger = logging.getLogger(__name__)

class LutExtractionService:
    """LUT提取服务类"""
    
    def __init__(self):
        self.lut_size = 32  # 标准LUT尺寸
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        加载图片并转换为RGB数组
        
        Args:
            image_path: 图片路径
            
        Returns:
            RGB数组 (height, width, 3)，值范围0-1，如果失败返回None
        """
        try:
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img_array = np.array(img, dtype=np.float32) / 255.0
            return img_array
        except Exception as e:
            logger.error(f"加载图片失败 {image_path}: {e}")
            return None
    
    def extract_lut_from_images(self, image_paths: List[str], output_path: str) -> Tuple[bool, Optional[str]]:
        """
        从图片集合中提取LUT（方法2）
        
        核心思路：
        1. 收集所有图片的色彩分布
        2. 构建输入RGB到输出RGB的映射关系
        3. 生成3D LUT文件
        
        Args:
            image_paths: 图片路径列表
            output_path: 输出LUT文件路径
            
        Returns:
            (成功标志, 错误信息)
        """
        if not image_paths:
            return False, "图片列表为空"
        
        try:
            # 收集所有图片的色彩数据
            all_input_rgb = []
            all_output_rgb = []
            
            logger.info(f"开始处理 {len(image_paths)} 张图片")
            
            for idx, image_path in enumerate(image_paths):
                if not os.path.exists(image_path):
                    logger.warning(f"图片不存在: {image_path}")
                    continue
                
                img_array = self.load_image(image_path)
                if img_array is None:
                    continue
                
                # 采样图片中的像素（避免处理所有像素，提高效率）
                height, width = img_array.shape[:2]
                sample_rate = max(1, min(10, (height * width) // 10000))  # 采样率，最多采样10000个像素
                
                sampled_pixels = img_array[::sample_rate, ::sample_rate, :]
                pixels_flat = sampled_pixels.reshape(-1, 3)
                
                # 方法2：基于图片集合的色彩分布生成LUT
                # 思路：分析图片集合的色彩特征，生成一个能够将标准色彩映射到该风格的LUT
                # 这里我们收集图片的RGB值，后续会通过统计分析生成LUT映射
                all_input_rgb.append(pixels_flat)
                all_output_rgb.append(pixels_flat)
                
                if (idx + 1) % 10 == 0:
                    logger.info(f"已处理 {idx + 1}/{len(image_paths)} 张图片")
            
            if len(all_input_rgb) == 0:
                return False, "没有成功加载任何图片"
            
            # 合并所有像素数据
            input_rgb = np.vstack(all_input_rgb)
            output_rgb = np.vstack(all_output_rgb)
            
            logger.info(f"共收集 {len(input_rgb)} 个像素点")
            
            # 生成3D LUT
            # 方法2：使用色彩映射统计生成LUT
            lut_array = self._generate_lut_from_color_mapping(input_rgb, output_rgb)
            
            # 保存为.cube格式
            self._save_cube_lut(lut_array, output_path)
            
            logger.info(f"LUT提取成功，保存到: {output_path}")
            return True, None
            
        except Exception as e:
            error_msg = f"提取LUT失败: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return False, error_msg
    
    def _generate_lut_from_color_mapping(self, input_rgb: np.ndarray, output_rgb: np.ndarray) -> np.ndarray:
        """
        从色彩映射生成3D LUT
        
        Args:
            input_rgb: 输入RGB数组 (N, 3)
            output_rgb: 输出RGB数组 (N, 3)
            
        Returns:
            3D LUT数组 (lut_size, lut_size, lut_size, 3)
        """
        lut_size = self.lut_size
        
        # 创建LUT网格
        grid_points = np.linspace(0, 1, lut_size)
        r_grid, g_grid, b_grid = np.meshgrid(grid_points, grid_points, grid_points, indexing='ij')
        
        # 将网格点展平
        grid_rgb = np.stack([
            r_grid.flatten(),
            g_grid.flatten(),
            b_grid.flatten()
        ], axis=1)
        
        # 使用插值方法从输入-输出映射生成LUT
        # 方法：对每个网格点，找到最近的输入点，使用其输出值
        # 更精确的方法：使用KNN或插值
        
        lut_values = np.zeros((lut_size, lut_size, lut_size, 3))
        
        # 使用最近邻插值（简单快速）
        # 对于每个网格点，找到最近的输入点
        from scipy.spatial import cKDTree
        
        # 构建KD树用于快速最近邻搜索
        tree = cKDTree(input_rgb)
        
        # 对每个网格点进行插值
        distances, indices = tree.query(grid_rgb, k=min(5, len(input_rgb)))
        
        # 使用加权平均（距离越近权重越大）
        for i, grid_point in enumerate(grid_rgb):
            if isinstance(distances, np.ndarray) and distances.ndim > 1:
                # k > 1的情况
                k_nearest_indices = indices[i]
                k_nearest_distances = distances[i]
            else:
                # k = 1的情况
                k_nearest_indices = [indices[i]]
                k_nearest_distances = [distances[i]]
            
            # 计算权重（距离的倒数）
            weights = 1.0 / (k_nearest_distances + 1e-10)  # 避免除零
            weights = weights / weights.sum()
            
            # 加权平均输出RGB
            weighted_output = np.sum(
                output_rgb[k_nearest_indices] * weights[:, np.newaxis],
                axis=0
            )
            
            # 转换为网格索引
            r_idx = int(grid_point[0] * (lut_size - 1))
            g_idx = int(grid_point[1] * (lut_size - 1))
            b_idx = int(grid_point[2] * (lut_size - 1))
            
            # 确保索引在范围内
            r_idx = np.clip(r_idx, 0, lut_size - 1)
            g_idx = np.clip(g_idx, 0, lut_size - 1)
            b_idx = np.clip(b_idx, 0, lut_size - 1)
            
            lut_values[r_idx, g_idx, b_idx] = weighted_output
        
        # 确保值在0-1范围内
        lut_values = np.clip(lut_values, 0.0, 1.0)
        
        return lut_values
    
    def _save_cube_lut(self, lut_array: np.ndarray, output_path: str):
        """
        保存LUT为.cube格式
        
        Args:
            lut_array: 3D LUT数组 (lut_size, lut_size, lut_size, 3)
            output_path: 输出文件路径
        """
        lut_size = self.lut_size
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # 写入.cube文件头
            f.write("TITLE \"Extracted LUT\"\n")
            f.write(f"LUT_3D_SIZE {lut_size}\n")
            f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
            f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
            f.write("\n")
            
            # 写入LUT数据
            # .cube格式：按B-G-R顺序遍历（最外层B，中间G，最内层R）
            for b in range(lut_size):
                for g in range(lut_size):
                    for r in range(lut_size):
                        # 获取RGB值（注意：lut_array是R-G-B顺序）
                        rgb = lut_array[r, g, b]
                        f.write(f"{rgb[0]:.6f} {rgb[1]:.6f} {rgb[2]:.6f}\n")
