# -*- coding: utf-8 -*-
"""
语义搜索服务
使用CLIP ViT-L/14模型和FAISS向量数据库
"""
import os
import torch
import numpy as np
from PIL import Image
import logging
import pickle
from app.utils.config_manager import get_local_image_dir

# 延迟导入CLIP和FAISS，避免启动时就必须安装
CLIP_AVAILABLE = False
CLIP_MODULE = None

def _disable_proxy_for_download():
    """临时禁用代理环境变量，用于模型下载"""
    original_proxies = {}
    proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy', 'SOCKS_PROXY', 'socks_proxy']
    for var in proxy_env_vars:
        if var in os.environ:
            original_proxies[var] = os.environ[var]
            del os.environ[var]
    
    # 设置 NO_PROXY 为 *，确保所有请求都不使用代理
    if 'NO_PROXY' not in os.environ:
        original_proxies['NO_PROXY'] = None
    original_no_proxy = os.environ.get('NO_PROXY', '')
    os.environ['NO_PROXY'] = '*'
    original_proxies['_NO_PROXY'] = original_no_proxy
    
    return original_proxies

def _restore_proxy(original_proxies):
    """恢复代理环境变量"""
    for var, value in original_proxies.items():
        if var == '_NO_PROXY':
            # 恢复 NO_PROXY
            if value:
                os.environ['NO_PROXY'] = value
            elif 'NO_PROXY' in os.environ:
                del os.environ['NO_PROXY']
        elif var == 'NO_PROXY' and value is None:
            # 如果原来没有 NO_PROXY，删除它
            if 'NO_PROXY' in os.environ:
                del os.environ['NO_PROXY']
        else:
            os.environ[var] = value

try:
    import clip
    CLIP_MODULE = clip
    CLIP_AVAILABLE = True
except ImportError:
    try:
        # 尝试使用open-clip-torch作为替代
        # 在导入前禁用代理，避免下载模型时出现代理错误
        original_proxies = _disable_proxy_for_download()
        try:
            import open_clip
            CLIP_MODULE = open_clip
            CLIP_AVAILABLE = True
            logging.info("使用open-clip-torch作为CLIP替代")
        finally:
            _restore_proxy(original_proxies)
    except ImportError:
        CLIP_AVAILABLE = False
        logging.warning("CLIP模块未安装，语义搜索功能将不可用。请运行: pip install open-clip-torch 或 pip install git+https://github.com/openai/CLIP.git")

# 导入FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS模块未安装，语义搜索功能将不可用。请运行: pip install faiss-cpu 或 pip install faiss-gpu")

logger = logging.getLogger(__name__)

class SemanticSearchService:
    """语义搜索服务"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.preprocess = None
        self._use_open_clip = False  # 标记是否使用open-clip-torch
        self.collection_name = "image_semantic_search"
        # ViT-L/14的向量维度是768，ViT-B/32是512
        self.dimension = 768  # ViT-L/14的向量维度
        
        # FAISS索引和映射
        self.index = None  # FAISS索引对象
        self.image_id_to_index = {}  # image_id -> FAISS索引位置
        self.index_to_image_id = {}  # FAISS索引位置 -> image_id
        
        # 数据库文件路径
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        faiss_data_dir = os.path.join(backend_dir, "faiss_data")
        os.makedirs(faiss_data_dir, exist_ok=True)
        self.faiss_index_path = os.path.join(faiss_data_dir, "semantic_search.index")
        self.faiss_mapping_path = os.path.join(faiss_data_dir, "semantic_search_mapping.pkl")
        
        self._initialized = False
        
    def initialize(self):
        """初始化模型和FAISS索引"""
        if self._initialized:
            return
        
        if not CLIP_AVAILABLE:
            raise ImportError("CLIP模块未安装，请运行: pip install open-clip-torch 或 pip install git+https://github.com/openai/CLIP.git")
        
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS模块未安装，请运行: pip install faiss-cpu 或 pip install faiss-gpu")
        
        try:
            # 临时禁用代理，避免下载模型时出现代理错误（特别是socks4代理）
            original_proxies = _disable_proxy_for_download()
            
            try:
                # 加载CLIP模型
                logger.info("正在加载CLIP ViT-L/14模型...")
                if CLIP_MODULE.__name__ == 'clip':
                    # 使用原始CLIP
                    self.model, self.preprocess = CLIP_MODULE.load("ViT-L/14", device=self.device, jit=False)
                    self._use_open_clip = False
                else:
                    # 使用open-clip-torch
                    # 确保在下载模型时没有代理
                    model, _, preprocess = CLIP_MODULE.create_model_and_transforms('ViT-L-14', pretrained='openai')
                    self.model = model.to(self.device)
                    self.preprocess = preprocess
                    self._use_open_clip = True
            finally:
                # 恢复原始代理设置
                _restore_proxy(original_proxies)
            
            # ✅ Windows显存优化：使用半精度（如果使用CUDA）
            if self.device == "cuda" and not self._use_open_clip:
                self.model = self.model.half()
                torch.cuda.empty_cache()  # 清空GPU缓存，释放冗余显存
                logger.info("已启用半精度模式，显存占用减半")
            
            self.model.eval()
            logger.info(f"CLIP模型已加载到设备: {self.device}")
            
            # 加载或创建FAISS索引
            self._load_or_create_index()
            
            self._initialized = True
            logger.info("✅ 语义搜索服务初始化完成")
        except Exception as e:
            logger.error(f"初始化语义搜索服务失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _load_or_create_index(self):
        """加载或创建FAISS索引"""
        try:
            # 尝试加载现有索引
            if os.path.exists(self.faiss_index_path) and os.path.exists(self.faiss_mapping_path):
                logger.info(f"加载现有FAISS索引: {self.faiss_index_path}")
                self.index = faiss.read_index(self.faiss_index_path)
                
                # 加载映射关系
                with open(self.faiss_mapping_path, 'rb') as f:
                    mapping_data = pickle.load(f)
                    self.image_id_to_index = mapping_data.get('image_id_to_index', {})
                    self.index_to_image_id = mapping_data.get('index_to_image_id', {})
                
                logger.info(f"✅ FAISS索引加载成功，包含 {self.index.ntotal} 个向量")
            else:
                # 创建新索引
                # 使用IndexFlatIP（内积），因为向量已经归一化，内积等价于余弦相似度
                logger.info(f"创建新的FAISS索引（维度: {self.dimension}）")
                self.index = faiss.IndexFlatIP(self.dimension)
                self.image_id_to_index = {}
                self.index_to_image_id = {}
                logger.info("✅ FAISS索引创建成功")
        except Exception as e:
            logger.error(f"加载/创建FAISS索引失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _save_index(self):
        """保存FAISS索引和映射关系"""
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.faiss_index_path)
                logger.debug(f"FAISS索引已保存: {self.faiss_index_path}")
            
            # 保存映射关系
            mapping_data = {
                'image_id_to_index': self.image_id_to_index,
                'index_to_image_id': self.index_to_image_id
            }
            with open(self.faiss_mapping_path, 'wb') as f:
                pickle.dump(mapping_data, f)
            logger.debug(f"映射关系已保存: {self.faiss_mapping_path}")
        except Exception as e:
            logger.error(f"保存FAISS索引失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    def encode_image(self, image_path):
        """编码单张图片为向量"""
        if not self._initialized:
            self.initialize()
        
        try:
            # 加载和预处理图片
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            # ✅ Windows显存优化：使用半精度（如果使用CUDA且是原始CLIP）
            if self.device == "cuda" and not self._use_open_clip:
                image_tensor = image_tensor.half()
            
            # 编码
            with torch.no_grad():
                image_features = self.model.encode_image(image_tensor)
                # ✅ L2归一化（必须！余弦相似度前提）
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
                vector = image_features.cpu().numpy().astype(np.float32).reshape(-1,)
            
            return vector
        except Exception as e:
            logger.error(f"编码图片失败 {image_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def encode_text(self, text):
        """编码文本为向量"""
        if not self._initialized:
            self.initialize()
        
        try:
            if self._use_open_clip:
                # 使用open-clip-torch
                import open_clip
                text_tokens = open_clip.tokenize([text]).to(self.device)
            else:
                # 使用原始CLIP
                text_tokens = CLIP_MODULE.tokenize([text]).to(self.device)
            
            # ✅ Windows显存优化：使用半精度（如果使用CUDA且是原始CLIP）
            if self.device == "cuda" and not self._use_open_clip:
                text_tokens = text_tokens.half()
            
            with torch.no_grad():
                text_features = self.model.encode_text(text_tokens)
                # ✅ L2归一化（必须！余弦相似度前提）
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                vector = text_features.cpu().numpy().astype(np.float32).reshape(-1,)
            
            return vector
        except Exception as e:
            logger.error(f"编码文本失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def add_image_vector(self, image_id, vector, save_index=True):
        """
        添加图片向量到FAISS索引
        
        Args:
            image_id: 图片ID
            vector: 图片向量
            save_index: 是否立即保存索引（默认True，多线程时可以设为False批量保存）
        """
        if not self._initialized:
            self.initialize()
        
        try:
            # 检查是否已存在
            if image_id in self.image_id_to_index:
                logger.warning(f"图片向量已存在 image_id={image_id}，先删除旧映射再添加新向量")
                # 删除旧的映射（FAISS不支持直接删除向量，所以只删除映射）
                old_index = self.image_id_to_index[image_id]
                del self.image_id_to_index[image_id]
                if old_index in self.index_to_image_id:
                    del self.index_to_image_id[old_index]
            
            # 将向量转换为numpy数组并reshape
            vector_array = vector.reshape(1, -1).astype(np.float32)
            
            # 添加到FAISS索引
            faiss_index = self.index.ntotal  # 当前索引位置
            self.index.add(vector_array)
            
            # 更新映射关系
            self.image_id_to_index[image_id] = faiss_index
            self.index_to_image_id[faiss_index] = image_id
            
            # 保存索引和映射（如果指定）
            if save_index:
                self._save_index()
            
            return faiss_index
        except Exception as e:
            logger.error(f"添加图片向量失败 image_id={image_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def search_by_vector(self, query_vector, top_k=10):
        """根据向量搜索相似图片"""
        if not self._initialized:
            self.initialize()
        
        try:
            # 检查索引是否为空
            if self.index.ntotal == 0:
                logger.warning("FAISS索引为空，无法搜索")
                return []
            
            # 将查询向量转换为numpy数组并reshape
            query_array = query_vector.reshape(1, -1).astype(np.float32)
            
            # 执行搜索（返回top_k个结果）
            # distances: 相似度分数（内积，值越大越相似）
            # indices: 索引位置
            distances, indices = self.index.search(query_array, min(top_k, self.index.ntotal))
            
            # 解析结果
            search_results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS返回-1表示没有找到
                    continue
                
                # 从映射中获取image_id
                image_id = self.index_to_image_id.get(idx)
                if image_id is None:
                    logger.warning(f"索引位置 {idx} 没有对应的image_id")
                    continue
                
                # 内积值就是相似度分数（因为向量已归一化，内积等价于余弦相似度）
                similarity = float(distance)
                # 转换为距离（越小越相似）
                distance_value = float(1 - similarity)
                
                search_results.append({
                    'image_id': image_id,
                    'distance': distance_value,
                    'score': similarity  # 相似度分数（0-1）
                })
            
            return search_results
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def search_by_text(self, text, top_k=10):
        """文本搜索图片"""
        query_vector = self.encode_text(text)
        return self.search_by_vector(query_vector, top_k)
    
    def search_by_image(self, image_path, top_k=10):
        """图片搜索图片"""
        query_vector = self.encode_image(image_path)
        return self.search_by_vector(query_vector, top_k)
    
    def delete_image_vector(self, image_id):
        """删除图片向量"""
        if not self._initialized:
            self.initialize()
        
        try:
            # FAISS不支持直接删除向量，需要重建索引
            if image_id not in self.image_id_to_index:
                logger.warning(f"图片向量不存在 image_id={image_id}")
                return 0
            
            # 从映射中删除
            faiss_index = self.image_id_to_index[image_id]
            del self.image_id_to_index[image_id]
            if faiss_index in self.index_to_image_id:
                del self.index_to_image_id[faiss_index]
            
            # 重建索引（移除已删除的向量）
            # 获取所有有效的向量和映射
            valid_vectors = []
            new_image_id_to_index = {}
            new_index_to_image_id = {}
            
            # 从数据库中重新加载所有已编码的向量（如果需要真正的删除）
            # 这里我们采用标记删除的方式，从映射中移除即可
            # 搜索时会自动过滤掉没有映射的向量
            
            # 保存更新后的映射
            self._save_index()
            
            logger.info(f"已删除图片向量映射 image_id={image_id}, faiss_index={faiss_index}")
            logger.info("注意：FAISS索引中的向量数据仍存在，但已从映射中移除，搜索时不会返回该向量")
            
            return 1
        except Exception as e:
            logger.error(f"删除图片向量失败 image_id={image_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def get_collection_stats(self):
        """获取FAISS索引统计信息"""
        if not self._initialized:
            self.initialize()
        
        try:
            # 获取FAISS索引中的向量总数
            total_vectors = self.index.ntotal if self.index is not None else 0
            
            # 获取有效映射的数量（实际可搜索的图片数）
            total_images = len(self.image_id_to_index)
            
            return {
                'total_images': total_images,
                'total_vectors': total_vectors,  # FAISS索引中的向量数（可能包含已删除的）
                'collection_name': self.collection_name,
                'dimension': self.dimension,
                'index_type': 'FAISS IndexFlatIP'
            }
        except Exception as e:
            logger.error(f"获取集合统计信息失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'total_images': 0,
                'total_vectors': 0,
                'collection_name': self.collection_name,
                'dimension': self.dimension,
                'index_type': 'FAISS IndexFlatIP',
                'error': str(e)
            }

# 全局服务实例
_semantic_search_service = None

def get_semantic_search_service():
    """获取语义搜索服务实例（单例）"""
    global _semantic_search_service
    if _semantic_search_service is None:
        _semantic_search_service = SemanticSearchService()
    return _semantic_search_service
