import clip
import torch
import numpy as np
from PIL import Image
import os
from pymilvus import MilvusClient, DataType

# ===================== 基础配置（和你之前一致，可直接改） =====================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# 可选 ViT-B/32（显存小） 或 ViT-L/14（精度高），按需切换
MODEL_NAME = "ViT-L/14"  # 换成 "ViT-B/32" 显存压力更小
IMAGE_DIR = "test_images"  # 你的图片文件夹路径
TEST_QUERY_TEXT = "一只雪地里的金毛犬"  # 文本检索示例
TEST_QUERY_IMAGE = "query_dog.jpg"  # 图片检索示例（可选）
TOP_K = 5  # 返回相似图片数量
VECTOR_DIM = 512  # CLIP所有模型的特征向量维度都是 512 ✅ 固定值

# ===================== 1. 加载CLIP模型 + 显存优化（解决ViT-L/14显存不足） =====================
model, preprocess = clip.load(MODEL_NAME, device=DEVICE, jit=False)
# 关键优化：ViT-L/14显存优化 - 开启半精度，显存占用直接减半，精度几乎无损失
if DEVICE == "cuda":
    model = model.half()
model.eval()  # 推理模式，关闭梯度，节省显存

# ===================== 2. 初始化 Milvus Lite 客户端 【无启动码！一行搞定】 =====================
# 本地文件存储向量数据，无需启动服务，无任何配置，这就是Milvus Lite的核心优势
client = MilvusClient("./milvus_clip_image.db")  # 数据存在当前目录的db文件里

# ===================== 3. 创建向量集合（表），只需要执行一次 =====================
COLLECTION_NAME = "clip_image_vectors"
# 检查集合是否存在，不存在则创建
if not client.has_collection(collection_name=COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=[
            {"name": "id", "type": DataType.INT64, "is_primary": True, "auto_id": True},
            {"name": "image_path", "type": DataType.VARCHAR, "max_length": 500},  # 存储图片路径
            {"name": "vector", "type": DataType.FLOAT_VECTOR, "dim": VECTOR_DIM}  # CLIP向量维度固定512
        ],
        # 索引配置：语义检索最优选择 - IVF_FLAT（精确+高效），归一化后用余弦相似度
        index_params=client.prepare_index_params()
        .add_index(field_name="vector", metric_type="COSINE", index_type="IVF_FLAT", params={"nlist": 128})
    )
    print(f"✅ 集合 {COLLECTION_NAME} 创建成功")

# ===================== 4. 图片特征提取 + 批量插入Milvus =====================
def get_image_paths():
    """获取图片文件夹下所有图片路径"""
    exts = (".jpg", ".png", ".jpeg")
    return [os.path.join(IMAGE_DIR, f) for f in os.listdir(IMAGE_DIR) if f.lower().endswith(exts)]

def encode_image_to_vector(img_path):
    """单张图片编码为CLIP向量 + L2归一化（必须！余弦相似度前提）"""
    with torch.no_grad():
        img = preprocess(Image.open(img_path)).unsqueeze(0).to(DEVICE)
        if DEVICE == "cuda":
            img = img.half()  # 和模型保持半精度，避免显存溢出
        vec = model.encode_image(img)
        vec = vec / vec.norm(dim=-1, keepdim=True)  # L2归一化，核心步骤
        return vec.cpu().numpy().astype(np.float32).reshape(-1,)

# 批量插入图片向量
image_paths = get_image_paths()
vectors_to_insert = []
for img_path in image_paths:
    vec = encode_image_to_vector(img_path)
    vectors_to_insert.append({"image_path": img_path, "vector": vec})

if vectors_to_insert:
    client.insert(collection_name=COLLECTION_NAME, data=vectors_to_insert)
    print(f"✅ 成功插入 {len(vectors_to_insert)} 张图片向量")

# ===================== 5. 核心：语义检索函数（以文搜图 + 以图搜图） =====================
def semantic_search(query, is_text=True, top_k=TOP_K):
    """
    语义检索主函数
    :param query: 文本字符串 或 图片路径
    :param is_text: True=文本检索，False=图片检索
    :return: top_k 相似图片路径+相似度
    """
    # 生成查询向量
    with torch.no_grad():
        if is_text:
            # 文本编码
            text = clip.tokenize([query]).to(DEVICE)
            if DEVICE == "cuda":
                text = text.half()
            query_vec = model.encode_text(text)
        else:
            # 图片编码
            query_vec = encode_image_to_vector(query)
        
        query_vec = query_vec / query_vec.norm(dim=-1, keepdim=True)  # 归一化
        query_vec = query_vec.cpu().numpy().astype(np.float32).reshape(-1,)

    # Milvus检索：余弦相似度，返回TOP-K
    res = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vec],
        limit=top_k,
        search_params={"metric_type": "COSINE"},
        output_fields=["image_path"]
    )

    # 整理结果：图片路径 + 相似度分数
    results = []
    for hit in res[0]:
        results.append({
            "image_path": hit["entity"]["image_path"],
            "similarity": hit["distance"]  # 余弦相似度，值越大越相似
        })
    return results

# ===================== 6. 测试检索 =====================
# 测试1：以文搜图（核心需求）
print("\n===== 以文搜图结果 =====")
text_results = semantic_search(TEST_QUERY_TEXT, is_text=True)
for i, item in enumerate(text_results):
    print(f"TOP-{i+1}: {item['image_path']} | 相似度: {item['similarity']:.4f}")

# 测试2：以图搜图（可选）
if os.path.exists(TEST_QUERY_IMAGE):
    print("\n===== 以图搜图结果 =====")
    img_results = semantic_search(TEST_QUERY_IMAGE, is_text=False)
    for i, item in enumerate(img_results):
        print(f"TOP-{i+1}: {item['image_path']} | 相似度: {item['similarity']:.4f}")