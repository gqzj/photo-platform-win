"""
图片抓取服务
TODO: 实现具体的图片抓取逻辑
"""
import requests
import hashlib
from app.database import db
from app.models.image import Image
from app.utils.config_manager import get_local_image_dir, get_relative_path
from PIL import Image as PILImage
import io
import os
from datetime import datetime

class ImageCaptureService:
    """图片抓取服务类"""
    
    def __init__(self):
        self.storage_path = get_local_image_dir()  # 使用config.json中的配置
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
    
    def _compute_image_hash(self, file_path):
        """
        计算图片文件的哈希值（SHA256）
        
        Args:
            file_path: 图片文件路径
            
        Returns:
            str: 图片哈希值，如果计算失败返回None
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                # 分块读取，避免大文件占用过多内存
                while chunk := f.read(8192):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except Exception as e:
            print(f"计算图片哈希失败 {file_path}: {e}")
            return None
    
    def capture_image(self, url, source='web'):
        """
        抓取单张图片
        
        Args:
            url: 图片URL
            source: 图片来源
        
        Returns:
            Image对象
        """
        try:
            # 下载图片
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 获取图片信息
            img_data = response.content
            img = PILImage.open(io.BytesIO(img_data))
            
            # 生成文件名
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(url)}"
            local_path_absolute = os.path.join(self.storage_path, filename)
            
            # 保存图片
            with open(local_path_absolute, 'wb') as f:
                f.write(img_data)
            
            # 计算图片哈希值
            image_hash = self._compute_image_hash(local_path_absolute)
            
            # 转换为相对路径用于存储
            local_path_relative = get_relative_path(local_path_absolute)
            
            # 优先根据image_hash检查是否已存在
            existing_image = None
            if image_hash:
                existing_image = Image.query.filter_by(image_hash=image_hash).first()
            
            # 如果image_hash不存在或未找到，再根据original_url检查
            if not existing_image:
                existing_image = Image.query.filter_by(original_url=url).first()
            
            # 如果图片已存在，返回已存在的图片
            if existing_image:
                print(f"图片已存在，跳过添加 (hash: {image_hash}, url: {url})")
                # 删除刚下载的重复文件
                try:
                    os.remove(local_path_absolute)
                except Exception as e:
                    print(f"删除重复文件失败: {e}")
                return existing_image
            
            # 创建数据库记录
            image = Image(
                filename=filename,
                storage_path=local_path_relative,  # 存储相对路径
                original_url=url,
                status='active',
                storage_mode='local',
                source_site=source,
                image_hash=image_hash,
                width=img.width,
                height=img.height,
                format=img.format.lower() if img.format else None
            )
            
            db.session.add(image)
            db.session.commit()
            
            return image
        except Exception as e:
            db.session.rollback()
            raise Exception(f"抓取图片失败: {str(e)}")
    
    def batch_capture(self, urls, source='web'):
        """
        批量抓取图片
        
        Args:
            urls: 图片URL列表
            source: 图片来源
        
        Returns:
            成功抓取的图片列表
        """
        success_list = []
        for url in urls:
            try:
                image = self.capture_image(url, source)
                success_list.append(image)
            except Exception as e:
                print(f"抓取失败 {url}: {str(e)}")
                continue
        
        return success_list

