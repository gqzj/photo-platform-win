# -*- coding: utf-8 -*-
"""
LUT应用服务
用于将LUT文件应用到图片上
"""
import os
import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class LutApplicationService:
    """LUT应用服务类"""
    
    def __init__(self):
        pass
    
    def load_lut_cube(self, lut_path: str) -> Optional[np.ndarray]:
        """
        加载.cube格式的LUT文件
        
        Args:
            lut_path: LUT文件路径
            
        Returns:
            3D LUT数组 (size, size, size, 3) 或 None
        """
        try:
            with open(lut_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 查找LUT_3D_SIZE
            lut_size = None
            data_start = None
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('LUT_3D_SIZE'):
                    lut_size = int(line.split()[1])
                elif line.startswith('0.') or line.startswith('1.') or (line[0].isdigit() and '.' in line):
                    if data_start is None:
                        data_start = i
                    break
            
            if lut_size is None:
                logger.error(f"未找到LUT_3D_SIZE: {lut_path}")
                return None
            
            # 读取LUT数据
            lut_data = []
            for i in range(data_start, len(lines)):
                line = lines[i].strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        r = float(parts[0])
                        g = float(parts[1])
                        b = float(parts[2])
                        lut_data.append([r, g, b])
                    except ValueError:
                        continue
            
            if len(lut_data) != lut_size ** 3:
                logger.warning(f"LUT数据量不匹配: 期望 {lut_size ** 3}, 实际 {len(lut_data)}")
            
            # 转换为numpy数组并reshape
            # .cube格式的数据顺序：最外层是B，中间是G，最内层是R
            # 数据格式：B循环最外层，G循环中间，R循环最内层
            # 所以reshape为 (lut_size, lut_size, lut_size, 3)，索引时用 [b, g, r]
            lut_array = np.array(lut_data, dtype=np.float32)
            lut_array = lut_array.reshape((lut_size, lut_size, lut_size, 3))
            
            logger.info(f"LUT数组形状: {lut_array.shape}, LUT大小: {lut_size}")
            
            return lut_array
            
        except Exception as e:
            logger.error(f"加载LUT文件失败 {lut_path}: {e}")
            return None
    
    def apply_lut_to_image(self, image_path: str, lut_path: str, output_path: str) -> Tuple[bool, Optional[str]]:
        """
        将LUT应用到图片
        
        Args:
            image_path: 输入图片路径
            lut_path: LUT文件路径
            output_path: 输出图片路径
            
        Returns:
            (成功标志, 错误信息)
        """
        try:
            logger.info(f"开始应用LUT: image_path={image_path}, lut_path={lut_path}, output_path={output_path}")
            
            # 检查输入文件是否存在
            if not os.path.exists(image_path):
                error_msg = f"输入图片不存在: {image_path}"
                logger.error(error_msg)
                return False, error_msg
            
            if not os.path.exists(lut_path):
                error_msg = f"LUT文件不存在: {lut_path}"
                logger.error(error_msg)
                return False, error_msg
            
            # 加载图片
            img = Image.open(image_path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            logger.info(f"图片尺寸: {img.size}, 模式: {img.mode}")
            
            img_array = np.array(img, dtype=np.float32) / 255.0
            
            # 获取LUT文件扩展名
            lut_ext = os.path.splitext(lut_path)[1].lower()
            
            # 加载LUT
            if lut_ext == '.cube':
                lut_array = self.load_lut_cube(lut_path)
            else:
                return False, f"不支持的LUT格式: {lut_ext}"
            
            if lut_array is None:
                return False, "加载LUT文件失败"
            
            lut_size = lut_array.shape[0]
            
            # 应用LUT（使用向量化操作）
            height, width = img_array.shape[:2]
            
            # 将RGB值映射到LUT索引
            # .cube格式的LUT索引顺序是B-G-R（最外层B，中间G，最内层R）
            r_indices = (img_array[:, :, 0] * (lut_size - 1)).astype(np.int32)
            g_indices = (img_array[:, :, 1] * (lut_size - 1)).astype(np.int32)
            b_indices = (img_array[:, :, 2] * (lut_size - 1)).astype(np.int32)
            
            # 确保索引在范围内
            r_indices = np.clip(r_indices, 0, lut_size - 1)
            g_indices = np.clip(g_indices, 0, lut_size - 1)
            b_indices = np.clip(b_indices, 0, lut_size - 1)
            
            # 使用高级索引获取LUT值
            # 注意：.cube格式的LUT数组索引顺序是 [b, g, r]，而不是 [r, g, b]
            output_array = lut_array[b_indices, g_indices, r_indices]
            
            logger.info(f"应用LUT: 输入形状 {img_array.shape}, 输出形状 {output_array.shape}")
            
            # 将值限制在0-1范围内并转换为0-255
            output_array = np.clip(output_array, 0, 1)
            output_array = (output_array * 255).astype(np.uint8)
            
            # 保存图片
            output_img = Image.fromarray(output_array)
            output_img.save(output_path, quality=95)
            
            return True, None
            
        except Exception as e:
            logger.error(f"应用LUT失败: {e}")
            return False, str(e)

