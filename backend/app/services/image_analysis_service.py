# -*- coding: utf-8 -*-
"""
图像分析服务
用于检测图片的各种特征：人脸、文字、模糊度等
"""
import cv2
import numpy as np
import os
import logging
from typing import Dict, List, Tuple, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# 尝试导入MTCNN（更先进的人脸检测方法，支持侧脸）
try:
    from mtcnn import MTCNN
    MTCNN_AVAILABLE = True
except ImportError:
    MTCNN_AVAILABLE = False
    logger.warning("MTCNN未安装，将使用传统方法。建议安装: pip install mtcnn")

# 尝试导入YOLOv8（用于人物检测，准确率高）
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("YOLOv8未安装，人物检测将使用OpenCV HOG方法。建议安装: pip install ultralytics")

def imread_unicode(image_path: str):
    """
    读取图片文件（支持中文路径）
    使用PIL读取后转换为OpenCV格式
    """
    try:
        # 使用PIL读取图片（支持中文路径）
        pil_img = Image.open(image_path)
        # 转换为RGB格式（如果是RGBA或其他格式）
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        # 转换为numpy数组
        img_array = np.array(pil_img)
        # PIL使用RGB，OpenCV使用BGR，需要转换
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        return img_bgr
    except Exception as e:
        logger.error(f"使用PIL读取图片失败 {image_path}: {e}")
        # 如果PIL失败，尝试使用OpenCV（可能不支持中文路径）
        return cv2.imread(image_path)

class ImageAnalysisService:
    """图像分析服务类"""
    
    def __init__(self):
        """初始化服务"""
        # 初始化MTCNN人脸检测器（唯一的人脸检测方法）
        self.mtcnn_detector = None
        if MTCNN_AVAILABLE:
            try:
                # MTCNN对侧脸和多角度人脸检测效果很好
                # 使用默认参数
                self.mtcnn_detector = MTCNN()
                logger.info("MTCNN人脸检测器已加载（支持侧脸检测）")
            except Exception as e:
                logger.error(f"无法加载MTCNN人脸检测器: {e}", exc_info=True)
                self.mtcnn_detector = None
                logger.error("MTCNN是数据清洗任务必需的人脸检测方法，请确保已安装: pip install mtcnn")
        else:
            logger.error("MTCNN未安装，数据清洗任务将无法进行人脸检测。请安装: pip install mtcnn")
        
        # 初始化人物检测器（使用Haar Cascade）
        self.person_cascade = None
        try:
            # 尝试加载Haar Cascade人物检测器
            # OpenCV的Haar Cascade主要用于人脸检测，但也可以尝试使用身体检测器
            # 如果没有专门的人物检测器，可以使用Haar Cascade检测人体上半身或全身
            cascade_path = cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            if os.path.exists(cascade_path):
                self.person_cascade = cv2.CascadeClassifier(cascade_path)
                logger.info("Haar Cascade人物检测器已加载（全身检测）")
            else:
                # 如果全身检测器不存在，尝试上半身检测器
                cascade_path = cv2.data.haarcascades + 'haarcascade_upperbody.xml'
                if os.path.exists(cascade_path):
                    self.person_cascade = cv2.CascadeClassifier(cascade_path)
                    logger.info("Haar Cascade人物检测器已加载（上半身检测）")
                else:
                    # 如果都不存在，尝试使用HOG作为备选（因为Haar Cascade的人物检测器可能不存在）
                    logger.warning("Haar Cascade人物检测器文件不存在，使用HOG作为备选")
                    try:
                        self.hog = cv2.HOGDescriptor()
                        self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                        logger.info("OpenCV HOG人物检测器已加载（备选方案）")
                    except Exception as e:
                        logger.warning(f"无法加载HOG人物检测器: {e}")
                        self.hog = None
        except Exception as e:
            logger.warning(f"无法加载Haar Cascade人物检测器: {e}")
            self.person_cascade = None
            # 如果Haar Cascade加载失败，尝试使用HOG作为备选
            try:
                self.hog = cv2.HOGDescriptor()
                self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                logger.info("OpenCV HOG人物检测器已加载（备选方案）")
            except Exception as e2:
                logger.warning(f"无法加载HOG人物检测器: {e2}")
                self.hog = None
    
    def detect_faces(self, image_path: str) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """
        检测图片中的人脸数量
        
        Args:
            image_path: 图片路径
            
        Returns:
            Tuple[int, List]: (人脸数量, 人脸位置列表[(x, y, w, h), ...])
        """
        try:
            # 读取图片
            img = imread_unicode(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return 0, []
            
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用MTCNN检测人脸（支持侧脸和多角度）
            faces = []
            if not self.mtcnn_detector:
                logger.warning("MTCNN人脸检测器未加载，无法进行人脸检测")
                return 0, []
            
            try:
                # MTCNN需要RGB格式
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                # 执行检测
                detections = self.mtcnn_detector.detect_faces(img_rgb)
                
                if detections:
                    for detection in detections:
                        # 获取边界框和置信度
                        x, y, face_w, face_h = detection['box']
                        confidence = detection['confidence']
                        
                        # 确保坐标在图片范围内
                        x = max(0, x)
                        y = max(0, y)
                        face_w = min(face_w, w - x)
                        face_h = min(face_h, h - y)
                        
                        # 过滤条件：面积不能太小（至少占图片面积的0.05%）
                        face_area = face_w * face_h
                        img_area = w * h
                        if face_area < img_area * 0.0005:
                            logger.debug(f"MTCNN检测到的人脸太小，跳过: area_ratio={face_area/img_area:.6f}")
                            continue
                        
                        # 过滤条件：尺寸不能太大（不超过图片的50%）
                        if face_w > w * 0.5 or face_h > h * 0.5:
                            logger.debug(f"MTCNN检测到的人脸太大，跳过: w={face_w}/{w}, h={face_h}/{h}")
                            continue
                        
                        # 过滤条件：置信度不能太低
                        if confidence < 0.5:
                            logger.debug(f"MTCNN检测到的人脸置信度太低，跳过: confidence={confidence:.2f}")
                            continue
                        
                        # 确保所有值都是 Python 原生 int 类型
                        faces.append((int(x), int(y), int(face_w), int(face_h)))
                        logger.debug(f"MTCNN检测到人脸: x={x}, y={y}, w={face_w}, h={face_h}, confidence={confidence:.2f}")
                
                if faces:
                    logger.info(f"MTCNN检测到 {len(faces)} 个人脸（包括侧脸）")
                else:
                    logger.debug("MTCNN未检测到人脸")
            except Exception as e:
                logger.error(f"MTCNN人脸检测失败: {e}", exc_info=True)
                return 0, []
            
            # 去重：如果检测框重叠度很高，只保留一个
            if len(faces) > 1:
                faces = self._remove_overlapping_faces(faces)
            
            return len(faces), faces
            
        except Exception as e:
            logger.error(f"人脸检测失败 {image_path}: {e}", exc_info=True)
            return 0, []
    
    def _remove_overlapping_faces(self, faces: List[Tuple[int, int, int, int]], overlap_threshold: float = 0.5) -> List[Tuple[int, int, int, int]]:
        """
        去除重叠的人脸检测框
        
        Args:
            faces: 人脸检测框列表
            overlap_threshold: 重叠阈值，超过此值认为是重复检测
            
        Returns:
            去重后的人脸列表
        """
        if len(faces) <= 1:
            return faces
        
        def calculate_iou(box1, box2):
            """计算两个框的交并比（IoU）"""
            x1, y1, w1, h1 = box1
            x2, y2, w2, h2 = box2
            
            # 计算交集
            xi1 = max(x1, x2)
            yi1 = max(y1, y2)
            xi2 = min(x1 + w1, x2 + w2)
            yi2 = min(y1 + h1, y2 + h2)
            
            if xi2 <= xi1 or yi2 <= yi1:
                return 0.0
            
            inter_area = (xi2 - xi1) * (yi2 - yi1)
            box1_area = w1 * h1
            box2_area = w2 * h2
            union_area = box1_area + box2_area - inter_area
            
            if union_area == 0:
                return 0.0
            
            return inter_area / union_area
        
        # 按面积从大到小排序，保留面积较大的检测框
        faces_with_area = [(f, f[2] * f[3]) for f in faces]
        faces_with_area.sort(key=lambda x: x[1], reverse=True)
        
        filtered_faces = []
        for face, area in faces_with_area:
            is_duplicate = False
            for existing_face in filtered_faces:
                iou = calculate_iou(face, existing_face)
                if iou > overlap_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_faces.append(face)
        
        return filtered_faces
    
    def _calculate_union_area(self, boxes: List[Tuple[int, int, int, int]]) -> float:
        """
        计算多个矩形框的并集面积（考虑重叠）
        
        Args:
            boxes: 矩形框列表，每个框为 (x, y, w, h)
            
        Returns:
            float: 并集面积
        """
        if not boxes:
            return 0.0
        
        # 使用numpy数组存储所有矩形框
        boxes_array = np.array(boxes, dtype=np.int32)
        
        # 找到所有矩形框的边界
        min_x = np.min(boxes_array[:, 0])
        min_y = np.min(boxes_array[:, 1])
        max_x = np.max(boxes_array[:, 0] + boxes_array[:, 2])
        max_y = np.max(boxes_array[:, 1] + boxes_array[:, 3])
        
        # 创建一个足够大的画布
        canvas = np.zeros((max_y - min_y, max_x - min_x), dtype=np.uint8)
        
        # 将所有矩形框绘制到画布上（填充为1）
        for x, y, w, h in boxes:
            # 转换为相对于画布的坐标
            rel_x = x - min_x
            rel_y = y - min_y
            # 确保坐标在画布范围内
            rel_x = max(0, rel_x)
            rel_y = max(0, rel_y)
            rel_x2 = min(canvas.shape[1], rel_x + w)
            rel_y2 = min(canvas.shape[0], rel_y + h)
            
            if rel_x2 > rel_x and rel_y2 > rel_y:
                canvas[rel_y:rel_y2, rel_x:rel_x2] = 1
        
        # 计算非零像素的数量（即并集面积）
        union_area = np.sum(canvas > 0)
        
        return float(union_area)
    
    def detect_text(self, image_path: str) -> Tuple[bool, List[Tuple[int, int, int, int]], float]:
        """
        使用EAST算法检测图片中的文字，并返回文字位置和面积占比
        
        Args:
            image_path: 图片路径
            
        Returns:
            Tuple[bool, List, float]: (是否包含文字, 文字位置列表[(x, y, w, h), ...], 文字面积占比)
        """
        try:
            # 读取图片
            img = imread_unicode(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return False, [], 0.0
            
            h, w = img.shape[:2]
            img_area = w * h
            text_locations = []
            
            # 尝试使用OpenCV DNN的EAST文本检测器
            try:
                # EAST模型文件路径（需要下载EAST模型）
                # 可以从以下地址下载：https://github.com/opencv/opencv_extra/blob/master/testdata/dnn/frozen_east_text_detection.pb
                east_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'frozen_east_text_detection.pb')
                
                if os.path.exists(east_model_path):
                    # 加载EAST模型
                    net = cv2.dnn.readNet(east_model_path)
                    
                    # 准备输入图像（EAST需要特定的输入尺寸，必须是32的倍数）
                    orig = img.copy()
                    (H, W) = img.shape[:2]
                    
                    # 设置新的宽度和高度（EAST模型通常使用320x320）
                    (newW, newH) = (320, 320)
                    rW = W / float(newW)
                    rH = H / float(newH)
                    
                    # 调整图像大小
                    resized = cv2.resize(img, (newW, newH))
                    
                    # 创建blob（EAST需要特定的预处理）
                    blob = cv2.dnn.blobFromImage(
                        resized, 1.0, (newW, newH),
                        (123.68, 116.78, 103.94), swapRB=True, crop=False
                    )
                    
                    # 设置网络输入
                    net.setInput(blob)
                    
                    # 获取输出层（EAST模型有两个输出层）
                    layerNames = [
                        "feature_fusion/Conv_7/Sigmoid",  # 分数图
                        "feature_fusion/concat_3"          # 几何图
                    ]
                    
                    # 前向传播
                    (scores, geometry) = net.forward(layerNames)
                    
                    # 解析检测结果
                    (numRows, numCols) = scores.shape[2:4]
                    rects = []
                    confidences = []
                    
                    # 最小置信度阈值
                    min_confidence = 0.5
                    
                    for y in range(0, numRows):
                        # 提取分数和几何数据
                        scoresData = scores[0, 0, y]
                        xData0 = geometry[0, 0, y]
                        xData1 = geometry[0, 1, y]
                        xData2 = geometry[0, 2, y]
                        xData3 = geometry[0, 3, y]
                        anglesData = geometry[0, 4, y]
                        
                        for x in range(0, numCols):
                            # 如果分数不够高，忽略
                            if scoresData[x] < min_confidence:
                                continue
                            
                            # 计算偏移量（每个像素对应4个像素）
                            (offsetX, offsetY) = (x * 4.0, y * 4.0)
                            
                            # 提取旋转角度
                            angle = anglesData[x]
                            cos = np.cos(angle)
                            sin = np.sin(angle)
                            
                            # 计算边界框的宽度和高度
                            h_box = xData0[x] + xData2[x]
                            w_box = xData1[x] + xData3[x]
                            
                            # 计算边界框的终点
                            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                            
                            # 计算边界框的起点
                            startX = int(endX - w_box)
                            startY = int(endY - h_box)
                            
                            # 缩放回原始图像尺寸
                            startX = int(startX * rW)
                            startY = int(startY * rH)
                            endX = int(endX * rW)
                            endY = int(endY * rH)
                            
                            # 确保坐标在图像范围内
                            startX = max(0, min(startX, W))
                            startY = max(0, min(startY, H))
                            endX = max(0, min(endX, W))
                            endY = max(0, min(endY, H))
                            
                            box_w = endX - startX
                            box_h = endY - startY
                            
                            if box_w > 0 and box_h > 0:
                                rects.append((startX, startY, box_w, box_h))
                                confidences.append(float(scoresData[x]))
                    
                    # 应用非极大值抑制（NMS）去除重叠的检测框
                    if rects:
                        indices = cv2.dnn.NMSBoxes(rects, confidences, min_confidence, 0.4)
                        if len(indices) > 0:
                            indices = indices.flatten()
                            for i in indices:
                                x, y, box_w, box_h = rects[i]
                                text_locations.append((int(x), int(y), int(box_w), int(box_h)))
                    
                    logger.debug(f"EAST检测到 {len(text_locations)} 个文字区域")
                else:
                    logger.warning(f"EAST模型文件不存在: {east_model_path}")
                    logger.warning("将使用备选方法进行文字检测")
                    raise FileNotFoundError("EAST model not found")
                    
            except (FileNotFoundError, Exception) as e:
                # 如果EAST不可用，使用备选方法（基于轮廓的简单检测）
                logger.warning(f"EAST文字检测失败: {e}, 使用备选方法")
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
                # 使用形态学操作增强文字区域
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
                
                # 使用边缘检测
                edges = cv2.Canny(morph, 50, 150)
                
                # 查找轮廓
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 分析轮廓，判断是否可能是文字
                for contour in contours:
                    x, y, cw, ch = cv2.boundingRect(contour)
                    area = cv2.contourArea(contour)
                    
                    # 过滤太小的轮廓
                    if area < 50:
                        continue
                    
                    # 文字通常具有特定的宽高比
                    aspect_ratio = cw / ch if ch > 0 else 0
                    
                    # 文字区域通常宽度大于高度，且面积适中
                    if 0.2 < aspect_ratio < 10 and area > 50 and area < (w * h * 0.5):
                        text_locations.append((int(x), int(y), int(cw), int(ch)))
            
            # 计算文字面积占比（考虑重叠）
            text_area_ratio = 0.0
            if text_locations:
                union_area = self._calculate_union_area(text_locations)
                text_area_ratio = union_area / img_area if img_area > 0 else 0.0
                logger.debug(f"文字并集面积: {union_area}, 图片面积: {img_area}, 占比: {text_area_ratio:.2%}")
            
            # 判断是否包含文字：文字面积占比超过50%
            has_text = text_area_ratio > 0.5
            
            return has_text, text_locations, text_area_ratio
            
        except Exception as e:
            logger.error(f"文字检测失败 {image_path}: {e}", exc_info=True)
            import traceback
            logger.error(traceback.format_exc())
            return False, [], 0.0
    
    def detect_blur(self, image_path: str, threshold: float = 20.0) -> Tuple[bool, float]:
        """
        使用 Sobel 梯度方法检测图片是否模糊
        
        Args:
            image_path: 图片路径
            threshold: 模糊阈值，低于此值认为模糊（默认20.0）
                     注意：阈值针对 Sobel 梯度清晰度值，可根据数据分布调整
            
        Returns:
            Tuple[bool, float]: (是否模糊, 清晰度值)
        """
        try:
            # 读取图片
            img = imread_unicode(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return True, 0.0
            
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用 Sobel 算子计算水平和垂直方向的梯度
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            
            # 计算梯度幅值
            grad_mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
            
            # 使用梯度幅值的均值或方差作为清晰度指标
            # 均值 / 方差越大，图像越清晰
            sharpness = float(grad_mag.mean())
            
            is_blur = sharpness < threshold
            
            return is_blur, sharpness
            
        except Exception as e:
            logger.error(f"模糊检测失败 {image_path}: {e}", exc_info=True)
            return True, 0.0
    
    def detect_persons(self, image_path: str) -> Tuple[int, List[Tuple[int, int, int, int]]]:
        """
        检测图片中的人物数量
        
        Args:
            image_path: 图片路径
            
        Returns:
            Tuple[int, List]: (人物数量, 人物位置列表[(x, y, w, h), ...])
        """
        try:
            # 读取图片
            img = imread_unicode(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return 0, []
            
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            persons = []
            
            # 使用Haar Cascade检测人物
            if self.person_cascade:
                try:
                    # 优化参数：根据图片大小动态调整minSize
                    min_size = max(50, int(min(w, h) * 0.1))  # 至少为图片宽高的10%
                    
                    detected_persons = self.person_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.2,  # 增大步长，减少检测次数
                        minNeighbors=5,   # 增加邻居数，减少误检
                        minSize=(min_size, min_size),  # 动态最小尺寸
                        flags=cv2.CASCADE_SCALE_IMAGE
                    )
                    
                    # 过滤检测结果
                    for (x, y, person_w, person_h) in detected_persons:
                        # 过滤条件1: 面积不能太小（至少占图片面积的0.5%）
                        person_area = person_w * person_h
                        img_area = w * h
                        if person_area < img_area * 0.005:
                            continue
                        
                        # 过滤条件2: 宽高比应该在合理范围内（人物通常高度大于宽度）
                        aspect_ratio = person_w / person_h if person_h > 0 else 0
                        if aspect_ratio < 0.3 or aspect_ratio > 1.5:
                            continue
                        
                        # 过滤条件3: 尺寸不能太大（不超过图片的80%）
                        if person_w > w * 0.8 or person_h > h * 0.8:
                            continue
                        
                        persons.append((int(x), int(y), int(person_w), int(person_h)))
                        logger.debug(f"Haar Cascade检测到人物: x={x}, y={y}, w={person_w}, h={person_h}")
                    
                    if persons:
                        logger.info(f"Haar Cascade检测到 {len(persons)} 个人物")
                        return len(persons), persons
                except Exception as e:
                    logger.warning(f"Haar Cascade人物检测失败: {e}", exc_info=True)
            
            # 如果Haar Cascade不可用或失败，使用HOG作为备选
            if len(persons) == 0 and hasattr(self, 'hog') and self.hog:
                try:
                    # HOG检测人物
                    (rects, weights) = self.hog.detectMultiScale(
                        img,
                        winStride=(4, 4),
                        padding=(8, 8),
                        scale=1.05,
                        hitThreshold=0.0,
                        finalThreshold=2.0
                    )
                    
                    for (x, y, person_w, person_h) in rects:
                        # 过滤太小的人物检测框
                        person_area = person_w * person_h
                        img_area = w * h
                        if person_area < img_area * 0.005:
                            continue
                        
                        # 过滤太大的人物检测框
                        if person_w > w * 0.8 or person_h > h * 0.8:
                            continue
                        
                        persons.append((int(x), int(y), int(person_w), int(person_h)))
                        logger.debug(f"HOG检测到人物: x={x}, y={y}, w={person_w}, h={person_h}")
                    
                    if persons:
                        logger.info(f"HOG检测到 {len(persons)} 个人物")
                        return len(persons), persons
                        
                except Exception as e:
                    logger.warning(f"HOG人物检测失败: {e}", exc_info=True)
            
            if len(persons) == 0:
                logger.debug("未检测到人物")
            
            return len(persons), persons
            
        except Exception as e:
            logger.error(f"人物检测失败 {image_path}: {e}", exc_info=True)
            return 0, []
    
    def analyze_image(self, image_path: str, filter_features: List[str]) -> Dict[str, any]:
        """
        分析图片，检测指定的特征
        
        Args:
            image_path: 图片路径
            filter_features: 要检测的特征列表，例如：['no_face', 'multiple_faces', 'contains_text', 'blurry']
            
        Returns:
            Dict: 检测结果，包含匹配的特征和详细信息
        """
        result = {
            'matched_features': [],
            'details': {}
        }
        
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return result
        
        logger.debug(f"开始分析图片: {image_path}, 检测特征: {filter_features}")
        
        # 检测人脸
        if 'no_face' in filter_features or 'multiple_faces' in filter_features:
            face_count, face_locations = self.detect_faces(image_path)
            result['details']['face_count'] = face_count
            result['details']['face_locations'] = face_locations
            logger.debug(f"人脸检测结果: 数量={face_count}, 位置={face_locations}")
            
            if 'no_face' in filter_features and face_count == 0:
                result['matched_features'].append('no_face')
                logger.debug(f"匹配特征: no_face (无人脸)")
            
            if 'multiple_faces' in filter_features and face_count > 1:
                result['matched_features'].append('multiple_faces')
                logger.debug(f"匹配特征: multiple_faces (多人脸, 数量={face_count})")
        
        # 检测人物
        if 'no_person' in filter_features or 'multiple_persons' in filter_features:
            person_count, person_locations = self.detect_persons(image_path)
            result['details']['person_count'] = person_count
            result['details']['person_locations'] = person_locations
            logger.debug(f"人物检测结果: 数量={person_count}, 位置={person_locations}")
            
            if 'no_person' in filter_features and person_count == 0:
                result['matched_features'].append('no_person')
                logger.debug(f"匹配特征: no_person (无人物)")
            
            if 'multiple_persons' in filter_features and person_count > 1:
                result['matched_features'].append('multiple_persons')
                logger.debug(f"匹配特征: multiple_persons (多人物, 数量={person_count})")
        
        # 检测文字
        if 'contains_text' in filter_features:
            has_text, text_locations, text_area_ratio = self.detect_text(image_path)
            result['details']['has_text'] = has_text
            result['details']['text_locations'] = text_locations
            result['details']['text_area_ratio'] = text_area_ratio
            logger.debug(f"文字检测结果: 包含文字={has_text}, 位置数量={len(text_locations)}, 面积占比={text_area_ratio:.2%}")
            if has_text:
                result['matched_features'].append('contains_text')
                logger.debug(f"匹配特征: contains_text (包含文字, 面积占比={text_area_ratio:.2%})")
        
        # 检测模糊
        if 'blurry' in filter_features:
            is_blur, blur_value = self.detect_blur(image_path)
            result['details']['is_blur'] = is_blur
            result['details']['blur_value'] = blur_value
            logger.debug(f"模糊检测结果: 是否模糊={is_blur}, 模糊度值={blur_value}")
            if is_blur:
                result['matched_features'].append('blurry')
                logger.debug(f"匹配特征: blurry (图片模糊, 值={blur_value})")
        
        logger.debug(f"图片分析完成: {image_path}, 匹配特征={result['matched_features']}")
        return result

