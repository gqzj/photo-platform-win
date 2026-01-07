import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def preprocess_image(image_path, target_size=(256, 256)):
    """
    图片预处理：读取、灰度化、统一尺寸、归一化
    :param image_path: 图片路径
    :param target_size: 目标尺寸 (宽, 高)
    :return: 预处理后的灰度图
    """
    # 读取图片（cv2.IMREAD_GRAYSCALE 直接读为灰度图）
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法读取图片：{image_path}，请检查路径是否正确")

    # 统一尺寸（插值方式选双线性插值，保证缩放质量）
    img_resized = cv2.resize(img, target_size, interpolation=cv2.INTER_LINEAR)

    # 归一化（像素值缩放到0-1）
    img_normalized = img_resized / 255.0
    return img_normalized

def extract_histogram_feature(img):
    """
    提取灰度直方图特征
    :param img: 预处理后的灰度图
    :return: 归一化的直方图特征向量（长度256）
    """
    # 计算直方图：bins=256对应灰度级0-255，range=(0,1)对应归一化后的像素值
    hist = cv2.calcHist([img], [0], None, [256], [0, 1])
    # 归一化直方图（消除图片尺寸影响）
    hist_normalized = cv2.normalize(hist, hist).flatten()
    return hist_normalized

def calculate_image_similarity(img_path1, img_path2):
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

# ------------------- 测试示例 -------------------
if __name__ == "__main__":
    # 替换为你自己的图片路径
    img_path_1 = "test1.jpg"
    img_path_2 = "test2.jpg"
    img_path_3 = "test3.jpg"  # 可新增对比图

    # 计算相似度
    sim_1_2 = calculate_image_similarity(img_path_1, img_path_2)
    sim_1_3 = calculate_image_similarity(img_path_1, img_path_3)

    # 输出结果
    print(f"图片1与图片2的相似度：{sim_1_2:.4f}")
    print(f"图片1与图片3的相似度：{sim_1_3:.4f}")

    # 判定逻辑示例（可根据场景调整阈值）
    threshold = 0.8
    if sim_1_2 > threshold:
        print("图片1和图片2高度相似")
    else:
        print("图片1和图片2相似度较低")