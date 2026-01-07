import numpy as np
import os
import shutil

def rgb2hsv(rgb):
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

def read_cube_lut(file_path):
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
                r, g, b = map(float, line.split())
                rgb_data.append([r, g, b])
            except:
                continue

        # 转换为numpy数组
        rgb_array = np.array(rgb_data, dtype=np.float64)
        return rgb_array, lut_size

    except Exception as e:
        print(f"读取文件失败 {file_path}：{e}")
        return None, None

def classify_lut_by_features(rgb_array):
    """基于RGB数组，提取特征并返回分类路径（色调/饱和度/对比度）"""
    if rgb_array is None or len(rgb_array) == 0:
        return "未分类/无法解析"

    # 1. 转换为HSV
    hsv_array = rgb2hsv(rgb_array)
    h_mean = np.mean(hsv_array[:, 0])  # 色调均值
    s_mean = np.mean(hsv_array[:, 1])  # 饱和度均值
    s_var = np.var(hsv_array[:, 1])    # 饱和度方差
    v_var = np.var(hsv_array[:, 2])    # 明度方差

    # 2. 计算对比度（RGB极值差）
    rgb_max = np.max(rgb_array)
    rgb_min = np.min(rgb_array)
    contrast_rgb = rgb_max - rgb_min

    # 3. 判断色调（暖/冷/中性）
    tone = "中性调"
    if (0 <= h_mean <= 30) or (330 <= h_mean <= 360):
        tone = "暖调"
    elif 180 <= h_mean <= 240:
        tone = "冷调"

    # 4. 判断饱和度（高/中/低）
    saturation = "中饱和"
    if s_mean < 0.2:
        saturation = "低饱和"
    elif s_mean > 0.6:
        # 饱和度波动大，归为中饱和
        saturation = "高饱和" if s_var <= 0.1 else "中饱和"

    # 5. 判断对比度（高/中/低）
    contrast = "中对比"
    if contrast_rgb < 0.5 and v_var < 0.01:
        contrast = "低对比"
    elif contrast_rgb > 0.8 and v_var > 0.05:
        contrast = "高对比"

    # 6. 返回层级分类路径
    return os.path.join(tone, saturation, contrast)

def auto_classify_luts(lut_folder_path):
    """批量处理LUT文件夹，自动分类所有.cube文件"""
    # 验证文件夹是否存在
    if not os.path.isdir(lut_folder_path):
        print("文件夹路径不存在！")
        return

    # 遍历所有.cube文件
    for file_name in os.listdir(lut_folder_path):
        if not file_name.lower().endswith('.cube'):
            continue  # 只处理.cube格式

        file_path = os.path.join(lut_folder_path, file_name)
        if os.path.isdir(file_path):
            continue

        # 1. 读取LUT的RGB数据
        rgb_array, _ = read_cube_lut(file_path)

        # 2. 获取分类路径
        classify_path = classify_lut_by_features(rgb_array)

        # 3. 构建目标文件夹路径
        target_folder = os.path.join(lut_folder_path, classify_path)
        os.makedirs(target_folder, exist_ok=True)

        # 4. 移动文件到目标文件夹
        target_file_path = os.path.join(target_folder, file_name)
        try:
            shutil.move(file_path, target_file_path)
            print(f"已分类：{file_name} → {classify_path}")
        except Exception as e:
            print(f"移动文件失败 {file_name}：{e}")

if __name__ == "__main__":
    # ************************* 修改这里 *************************
    # 你的LUT文件夹路径（Windows用\\，Mac/Linux用/）
    lut_folder_path = r"C:\Users\YourName\LUTs\Unclassified"
    # ***********************************************************
    auto_classify_luts(lut_folder_path)