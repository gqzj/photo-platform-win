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
        # 初始化MTCNN人脸检测器
        self.mtcnn_detector = None
        if MTCNN_AVAILABLE:
            try:
                # MTCNN对侧脸和多角度人脸检测效果很好
                # 使用默认参数
                self.mtcnn_detector = MTCNN()
                logger.info("MTCNN人脸检测器已加载（支持侧脸检测）")
            except Exception as e:
                logger.warning(f"无法加载MTCNN人脸检测器: {e}", exc_info=True)
                self.mtcnn_detector = None
        
        # 加载人脸检测器（使用OpenCV的Haar Cascade）作为备选
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(cascade_path):
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        else:
            logger.warning(f"人脸检测模型文件不存在: {cascade_path}")
            self.face_cascade = None
        
        # 尝试加载更准确的人脸检测器（DNN）作为备选
        try:
            # 使用OpenCV的DNN人脸检测器（如果可用）
            dnn_prototxt = os.path.join(os.path.dirname(__file__), '..', 'models', 'deploy.prototxt')
            dnn_model = os.path.join(os.path.dirname(__file__), '..', 'models', 'res10_300x300_ssd_iter_140000.caffemodel')
            if os.path.exists(dnn_prototxt) and os.path.exists(dnn_model):
                self.face_net = cv2.dnn.readNetFromCaffe(dnn_prototxt, dnn_model)
                self.use_dnn = True
            else:
                self.face_net = None
                self.use_dnn = False
        except Exception as e:
            logger.warning(f"无法加载DNN人脸检测器: {e}")
            self.face_net = None
            self.use_dnn = False
        
        # 初始化人物检测器
        self.person_detector = None
        if YOLO_AVAILABLE:
            try:
                # 使用YOLOv8预训练模型（COCO数据集，包含person类别）
                self.person_detector = YOLO('yolov8n.pt')  # 使用nano版本，速度快
                logger.info("YOLOv8人物检测器已加载")
            except Exception as e:
                logger.warning(f"无法加载YOLOv8人物检测器: {e}", exc_info=True)
                self.person_detector = None
        
        # 如果YOLOv8不可用，使用OpenCV的HOG人物检测器作为备选
        if self.person_detector is None:
            try:
                # 使用OpenCV的HOG（Histogram of Oriented Gradients）人物检测器
                self.hog = cv2.HOGDescriptor()
                self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                logger.info("OpenCV HOG人物检测器已加载（备选方案）")
            except Exception as e:
                logger.warning(f"无法加载HOG人物检测器: {e}")
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
            
            # 优先使用MTCNN检测人脸（支持侧脸和多角度）
            faces = []
            if self.mtcnn_detector:
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
                except Exception as e:
                    logger.warning(f"MTCNN人脸检测失败: {e}", exc_info=True)
            
            # 如果MTCNN未检测到人脸，使用Haar Cascade作为备选
            if len(faces) == 0 and self.face_cascade:
                # 优化参数：提高minSize，增加minNeighbors，调整scaleFactor
                # minSize根据图片大小动态调整，至少为图片宽高的5%
                min_size = max(50, int(min(w, h) * 0.05))
                
                detected_faces = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.2,  # 增大步长，减少检测次数
                    minNeighbors=6,   # 增加邻居数，减少误检
                    minSize=(min_size, min_size),  # 动态最小尺寸
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # 过滤检测结果
                for (x, y, face_w, face_h) in detected_faces:
                    # 过滤条件1: 面积不能太小（至少占图片面积的0.1%）
                    face_area = face_w * face_h
                    img_area = w * h
                    if face_area < img_area * 0.001:
                        continue
                    
                    # 过滤条件2: 宽高比应该在合理范围内（人脸接近正方形，比例在0.5-2.0之间）
                    aspect_ratio = face_w / face_h if face_h > 0 else 0
                    if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                        continue
                    
                    # 过滤条件3: 尺寸不能太大（不超过图片的30%）
                    if face_w > w * 0.3 or face_h > h * 0.3:
                        continue
                    
                    faces.append((int(x), int(y), int(face_w), int(face_h)))
            
            # 如果MediaPipe和Haar Cascade都未检测到人脸，尝试DNN作为最后备选
            if len(faces) == 0 and self.use_dnn and self.face_net:
                try:
                    blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), [104, 117, 123])
                    self.face_net.setInput(blob)
                    detections = self.face_net.forward()
                    
                    for i in range(0, detections.shape[2]):
                        confidence = detections[0, 0, i, 2]
                        if confidence > 0.7:  # 提高置信度阈值到0.7，减少误检
                            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                            x, y, x2, y2 = box.astype("int")
                            face_w = int(x2 - x)
                            face_h = int(y2 - y)
                            
                            # 同样的过滤条件
                            face_area = face_w * face_h
                            img_area = w * h
                            if face_area < img_area * 0.001:
                                continue
                            
                            aspect_ratio = face_w / face_h if face_h > 0 else 0
                            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                                continue
                            
                            if face_w > w * 0.3 or face_h > h * 0.3:
                                continue
                            
                            # 确保所有值都是 Python 原生 int 类型
                            faces.append((int(x), int(y), int(face_w), int(face_h)))
                except Exception as e:
                    logger.warning(f"DNN人脸检测失败: {e}")
            
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
    
    def detect_text(self, image_path: str) -> Tuple[bool, List[Tuple[int, int, int, int]]]:
        """
        检测图片中是否包含文字，并返回文字位置
        
        Args:
            image_path: 图片路径
            
        Returns:
            Tuple[bool, List]: (是否包含文字, 文字位置列表[(x, y, w, h), ...])
        """
        try:
            # 读取图片
            img = imread_unicode(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return False, []
            
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用形态学操作增强文字区域
            # 创建矩形核
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            # 应用形态学操作
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # 使用边缘检测
            edges = cv2.Canny(morph, 50, 150)
            
            # 查找轮廓
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 分析轮廓，判断是否可能是文字
            text_locations = []
            h, w = gray.shape
            
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
            
            # 如果找到多个可能的文字轮廓，认为包含文字
            has_text = len(text_locations) >= 3
            
            return has_text, text_locations
            
        except Exception as e:
            logger.error(f"文字检测失败 {image_path}: {e}", exc_info=True)
            return False, []
    
    def detect_blur(self, image_path: str, threshold: float = 100.0) -> Tuple[bool, float]:
        """
        检测图片是否模糊
        
        Args:
            image_path: 图片路径
            threshold: 模糊阈值，低于此值认为模糊（默认100.0）
            
        Returns:
            Tuple[bool, float]: (是否模糊, 模糊度值)
        """
        try:
            # 读取图片
            img = imread_unicode(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return True, 0.0
            
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 使用拉普拉斯算子计算图像的二阶导数（方差）
            # 方差越大，图像越清晰
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            is_blur = laplacian_var < threshold
            
            return is_blur, float(laplacian_var)
            
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
            persons = []
            
            # 优先使用YOLOv8检测人物
            if self.person_detector:
                try:
                    # YOLOv8检测（COCO数据集中person类别ID为0）
                    results = self.person_detector(img, classes=[0], verbose=False)  # 只检测person类别
                    
                    for result in results:
                        boxes = result.boxes
                        if boxes is not None:
                            for box in boxes:
                                # 获取边界框坐标
                                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                confidence = float(box.conf[0].cpu().numpy())
                                
                                # 过滤低置信度的检测结果
                                if confidence < 0.5:
                                    continue
                                
                                # 转换为整数坐标
                                x = int(x1)
                                y = int(y1)
                                person_w = int(x2 - x1)
                                person_h = int(y2 - y1)
                                
                                # 过滤太小的人物检测框（至少占图片面积的0.5%）
                                person_area = person_w * person_h
                                img_area = w * h
                                if person_area < img_area * 0.005:
                                    continue
                                
                                # 过滤太大的人物检测框（不超过图片的80%）
                                if person_w > w * 0.8 or person_h > h * 0.8:
                                    continue
                                
                                persons.append((x, y, person_w, person_h))
                                logger.debug(f"YOLOv8检测到人物: x={x}, y={y}, w={person_w}, h={person_h}, confidence={confidence:.2f}")
                    
                    if persons:
                        logger.info(f"YOLOv8检测到 {len(persons)} 个人物")
                        return len(persons), persons
                        
                except Exception as e:
                    logger.warning(f"YOLOv8人物检测失败: {e}", exc_info=True)
            
            # 如果YOLOv8不可用或失败，使用OpenCV HOG作为备选
            if len(persons) == 0 and self.hog:
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
            has_text, text_locations = self.detect_text(image_path)
            result['details']['has_text'] = has_text
            result['details']['text_locations'] = text_locations
            logger.debug(f"文字检测结果: 包含文字={has_text}, 位置数量={len(text_locations)}")
            if has_text:
                result['matched_features'].append('contains_text')
                logger.debug(f"匹配特征: contains_text (包含文字)")
        
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

