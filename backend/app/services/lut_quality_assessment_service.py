# -*- coding: utf-8 -*-
"""
LUT质量评估服务
用于评估LUT文件的质量，包括色彩误差和平滑度
"""
import numpy as np
import os
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class LutQualityAssessmentService:
    """LUT质量评估服务类"""
    
    def __init__(self):
        pass
    
    def read_cube_lut(self, file_path: str) -> Tuple[Optional[np.ndarray], Optional[int]]:
        """
        读取.cube格式的LUT文件
        
        Args:
            file_path: LUT文件路径
            
        Returns:
            (RGB数组, LUT尺寸) 或 (None, None)
        """
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            lines = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    logger.info(f"使用编码 {encoding} 成功读取LUT文件")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"使用编码 {encoding} 读取失败: {e}")
                    continue
            
            if lines is None:
                logger.error(f"无法读取LUT文件（尝试了所有编码）: {file_path}")
                return None, None
            
            rgb_data = []
            lut_size = None
            
            for line in lines:
                line = line.strip()
                # 跳过注释行
                if not line or line.startswith('#'):
                    continue
                # 提取LUT尺寸
                if line.startswith('LUT_3D_SIZE'):
                    try:
                        lut_size = int(line.split()[-1])
                        logger.info(f"找到LUT_3D_SIZE: {lut_size}")
                    except (ValueError, IndexError):
                        continue
                # 提取RGB数据
                try:
                    parts = line.split()
                    if len(parts) >= 3:
                        r = float(parts[0])
                        g = float(parts[1])
                        b = float(parts[2])
                        # 验证RGB值范围
                        if 0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0:
                            rgb_data.append([r, g, b])
                except (ValueError, IndexError):
                    continue
            
            if lut_size is None:
                logger.error(f"未找到LUT_3D_SIZE: {file_path}")
                return None, None
            
            # 转换为numpy数组并reshape为3D LUT
            rgb_array = np.array(rgb_data, dtype=np.float64)
            
            # 验证数据量
            expected_size = lut_size ** 3
            if len(rgb_data) != expected_size:
                logger.warning(f"LUT数据量不匹配: 期望 {expected_size}, 实际 {len(rgb_data)}")
                # 如果数据量不足，尝试填充或截断
                if len(rgb_data) < expected_size:
                    # 填充零值
                    padding = np.zeros((expected_size - len(rgb_data), 3))
                    rgb_array = np.vstack([rgb_array, padding])
                else:
                    # 截断
                    rgb_array = rgb_array[:expected_size]
            
            # Reshape为3D LUT (lut_size, lut_size, lut_size, 3)
            # .cube格式：最外层B，中间G，最内层R
            lut_array = rgb_array.reshape((lut_size, lut_size, lut_size, 3))
            
            return lut_array, lut_size
            
        except Exception as e:
            logger.error(f"读取LUT文件失败 {file_path}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None, None
    
    def calculate_color_error(self, lut_array: np.ndarray, lut_size: int) -> Dict[str, float]:
        """
        计算LUT的色彩误差
        
        色彩误差评估方法：
        1. 中性色误差：检查中性色（灰度）是否保持中性
        2. 色彩一致性：检查相同输入是否产生一致输出
        3. 色彩范围误差：检查输出是否在有效范围内
        
        Args:
            lut_array: 3D LUT数组 (lut_size, lut_size, lut_size, 3)
            lut_size: LUT尺寸
            
        Returns:
            包含各种误差指标的字典
        """
        try:
            errors = {}
            
            # 1. 中性色误差（检查灰度输入是否保持灰度输出）
            neutral_errors = []
            for i in range(lut_size):
                # 获取灰度输入对应的输出 (i, i, i)
                output = lut_array[i, i, i]
                # 计算RGB三个通道的差异（理想情况下应该相等）
                r, g, b = output[0], output[1], output[2]
                # 计算标准差作为误差
                std_error = np.std([r, g, b])
                neutral_errors.append(std_error)
            
            errors['neutral_error_mean'] = float(np.mean(neutral_errors))
            errors['neutral_error_max'] = float(np.max(neutral_errors))
            errors['neutral_error_std'] = float(np.std(neutral_errors))
            
            # 2. 色彩范围误差（检查输出是否超出有效范围）
            # 理想情况下，输出应该在0-1范围内
            out_of_range = np.sum((lut_array < 0) | (lut_array > 1))
            total_pixels = lut_array.size
            errors['out_of_range_ratio'] = float(out_of_range / total_pixels)
            
            # 3. 色彩一致性误差（检查相同输入是否产生相同输出）
            # 对于.cube格式，相同输入应该产生相同输出
            # 这里我们检查相邻点的变化是否合理
            consistency_errors = []
            for i in range(lut_size - 1):
                for j in range(lut_size):
                    for k in range(lut_size):
                        # 检查相邻点的差异
                        diff = np.abs(lut_array[i+1, j, k] - lut_array[i, j, k])
                        consistency_errors.append(np.mean(diff))
            
            errors['consistency_error_mean'] = float(np.mean(consistency_errors))
            errors['consistency_error_max'] = float(np.max(consistency_errors))
            
            # 4. 总体色彩误差（综合指标）
            # 使用加权平均
            errors['total_color_error'] = (
                errors['neutral_error_mean'] * 0.4 +
                errors['out_of_range_ratio'] * 100 * 0.3 +
                errors['consistency_error_mean'] * 0.3
            )
            
            logger.info(f"色彩误差计算完成: {errors}")
            return errors
            
        except Exception as e:
            logger.error(f"计算色彩误差失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def calculate_smoothness(self, lut_array: np.ndarray, lut_size: int) -> Dict[str, float]:
        """
        计算LUT的平滑度
        
        平滑度评估方法：
        1. 梯度平滑度：计算LUT在RGB空间中的梯度变化
        2. 二阶导数：检查二阶导数（曲率）来评估平滑度
        3. 局部变化：检查相邻点之间的变化幅度
        
        Args:
            lut_array: 3D LUT数组 (lut_size, lut_size, lut_size, 3)
            lut_size: LUT尺寸
            
        Returns:
            包含各种平滑度指标的字典
        """
        try:
            smoothness_metrics = {}
            
            # 1. 一阶梯度平滑度（计算相邻点的梯度）
            gradients_r = []
            gradients_g = []
            gradients_b = []
            
            # 计算R方向的梯度
            for i in range(lut_size - 1):
                for j in range(lut_size):
                    for k in range(lut_size):
                        grad = np.abs(lut_array[i+1, j, k] - lut_array[i, j, k])
                        gradients_r.append(grad)
            
            # 计算G方向的梯度
            for i in range(lut_size):
                for j in range(lut_size - 1):
                    for k in range(lut_size):
                        grad = np.abs(lut_array[i, j+1, k] - lut_array[i, j, k])
                        gradients_g.append(grad)
            
            # 计算B方向的梯度
            for i in range(lut_size):
                for j in range(lut_size):
                    for k in range(lut_size - 1):
                        grad = np.abs(lut_array[i, j, k+1] - lut_array[i, j, k])
                        gradients_b.append(grad)
            
            # 计算梯度统计
            all_gradients = np.concatenate([gradients_r, gradients_g, gradients_b])
            smoothness_metrics['gradient_mean'] = float(np.mean(all_gradients))
            smoothness_metrics['gradient_std'] = float(np.std(all_gradients))
            smoothness_metrics['gradient_max'] = float(np.max(all_gradients))
            
            # 2. 二阶导数（曲率）平滑度
            # 计算二阶导数来评估平滑度
            second_derivatives = []
            
            # 计算R方向的二阶导数
            for i in range(lut_size - 2):
                for j in range(lut_size):
                    for k in range(lut_size):
                        second_deriv = np.abs(
                            lut_array[i+2, j, k] - 2 * lut_array[i+1, j, k] + lut_array[i, j, k]
                        )
                        second_derivatives.append(np.mean(second_deriv))
            
            smoothness_metrics['curvature_mean'] = float(np.mean(second_derivatives)) if second_derivatives else 0.0
            smoothness_metrics['curvature_max'] = float(np.max(second_derivatives)) if second_derivatives else 0.0
            
            # 3. 局部变化平滑度（检查局部区域的变化）
            local_variations = []
            for i in range(lut_size - 1):
                for j in range(lut_size - 1):
                    for k in range(lut_size - 1):
                        # 计算2x2x2局部区域的方差
                        local_block = lut_array[i:i+2, j:j+2, k:k+2, :]
                        local_var = np.var(local_block)
                        local_variations.append(local_var)
            
            smoothness_metrics['local_variation_mean'] = float(np.mean(local_variations))
            smoothness_metrics['local_variation_max'] = float(np.max(local_variations))
            
            # 4. 总体平滑度评分（综合指标）
            # 平滑度越高，梯度、曲率和局部变化应该越小
            # 归一化到0-1范围，1表示最平滑
            gradient_score = 1.0 / (1.0 + smoothness_metrics['gradient_mean'] * 10)
            curvature_score = 1.0 / (1.0 + smoothness_metrics['curvature_mean'] * 100)
            variation_score = 1.0 / (1.0 + smoothness_metrics['local_variation_mean'] * 100)
            
            smoothness_metrics['total_smoothness'] = (
                gradient_score * 0.5 +
                curvature_score * 0.3 +
                variation_score * 0.2
            )
            
            logger.info(f"平滑度计算完成: {smoothness_metrics}")
            return smoothness_metrics
            
        except Exception as e:
            logger.error(f"计算平滑度失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def assess_quality(self, file_path: str) -> Dict:
        """
        评估LUT文件的质量
        
        Args:
            file_path: LUT文件路径
            
        Returns:
            包含评估结果的字典
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': '文件不存在'
                }
            
            # 读取LUT文件
            lut_array, lut_size = self.read_cube_lut(file_path)
            
            if lut_array is None or lut_size is None:
                return {
                    'success': False,
                    'error': '无法读取LUT文件'
                }
            
            # 计算色彩误差
            color_errors = self.calculate_color_error(lut_array, lut_size)
            
            # 计算平滑度
            smoothness_metrics = self.calculate_smoothness(lut_array, lut_size)
            
            # 生成评估结论
            conclusion = self._generate_conclusion(color_errors, smoothness_metrics)
            
            return {
                'success': True,
                'lut_size': lut_size,
                'color_errors': color_errors,
                'smoothness': smoothness_metrics,
                'conclusion': conclusion
            }
            
        except Exception as e:
            logger.error(f"评估LUT质量失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_conclusion(self, color_errors: Dict, smoothness_metrics: Dict) -> Dict:
        """
        根据评估结果生成结论
        
        Args:
            color_errors: 色彩误差指标
            smoothness_metrics: 平滑度指标
            
        Returns:
            包含评估结论的字典
        """
        conclusion = {
            'overall_quality': 'unknown',
            'color_error_level': 'unknown',
            'smoothness_level': 'unknown',
            'recommendation': '',
            'details': []
        }
        
        # 评估色彩误差等级
        total_color_error = color_errors.get('total_color_error', float('inf'))
        if total_color_error < 0.01:
            conclusion['color_error_level'] = 'excellent'
            conclusion['details'].append('色彩误差极低，色彩映射非常准确')
        elif total_color_error < 0.05:
            conclusion['color_error_level'] = 'good'
            conclusion['details'].append('色彩误差较低，色彩映射准确')
        elif total_color_error < 0.1:
            conclusion['color_error_level'] = 'fair'
            conclusion['details'].append('色彩误差中等，色彩映射基本准确')
        elif total_color_error < 0.2:
            conclusion['color_error_level'] = 'poor'
            conclusion['details'].append('色彩误差较高，可能存在色彩失真')
        else:
            conclusion['color_error_level'] = 'very_poor'
            conclusion['details'].append('色彩误差很高，存在明显色彩失真')
        
        # 评估平滑度等级
        total_smoothness = smoothness_metrics.get('total_smoothness', 0.0)
        if total_smoothness >= 0.9:
            conclusion['smoothness_level'] = 'excellent'
            conclusion['details'].append('平滑度极高，色彩过渡非常自然')
        elif total_smoothness >= 0.7:
            conclusion['smoothness_level'] = 'good'
            conclusion['details'].append('平滑度较高，色彩过渡自然')
        elif total_smoothness >= 0.5:
            conclusion['smoothness_level'] = 'fair'
            conclusion['details'].append('平滑度中等，色彩过渡基本自然')
        elif total_smoothness >= 0.3:
            conclusion['smoothness_level'] = 'poor'
            conclusion['details'].append('平滑度较低，可能存在色彩突变')
        else:
            conclusion['smoothness_level'] = 'very_poor'
            conclusion['details'].append('平滑度很低，存在明显的色彩突变')
        
        # 检查超出范围的比例
        out_of_range_ratio = color_errors.get('out_of_range_ratio', 0.0)
        if out_of_range_ratio > 0.01:
            conclusion['details'].append(f'警告：有 {out_of_range_ratio*100:.2f}% 的输出值超出有效范围(0-1)')
        
        # 综合评估
        if conclusion['color_error_level'] in ['excellent', 'good'] and conclusion['smoothness_level'] in ['excellent', 'good']:
            conclusion['overall_quality'] = 'excellent'
            conclusion['recommendation'] = 'LUT质量优秀，可以放心使用'
        elif conclusion['color_error_level'] in ['excellent', 'good', 'fair'] and conclusion['smoothness_level'] in ['excellent', 'good', 'fair']:
            conclusion['overall_quality'] = 'good'
            conclusion['recommendation'] = 'LUT质量良好，适合大多数应用场景'
        elif conclusion['color_error_level'] in ['poor', 'very_poor'] or conclusion['smoothness_level'] in ['poor', 'very_poor']:
            conclusion['overall_quality'] = 'poor'
            conclusion['recommendation'] = 'LUT质量较差，建议重新生成或检查LUT文件'
        else:
            conclusion['overall_quality'] = 'fair'
            conclusion['recommendation'] = 'LUT质量一般，建议根据具体需求决定是否使用'
        
        return conclusion
