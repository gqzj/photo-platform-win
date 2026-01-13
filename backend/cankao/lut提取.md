从多张风格类似图片中提取LUT（颜色查找表），核心思路是**建立中性原图与风格化图片的颜色映射关系**，并通过多张样本提升映射的鲁棒性与泛化能力。以下是结构化的完整方案，包含两种主流方法与可直接运行的代码实现。

---

### 一、核心原理与方法概览

LUT本质是RGB到RGB的3D颜色映射表，记录每个输入颜色对应的输出颜色。从多张风格图提取LUT的关键在于：
1. **获取颜色映射对**：通过中性图+风格图的成对数据，或多张风格图的统计分布
2. **建立映射关系**：用插值、回归或机器学习方法拟合颜色变换
3. **生成标准LUT**：导出为行业通用的CUBE格式，便于跨软件使用

主流方法对比：

| 方法 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| **HaldCLUT法** | 有中性原图+风格图成对数据 | 简单直观、无代码基础也能操作 | 依赖精确的成对匹配，单张映射可能不鲁棒 |
| **统计融合法** | 多张风格相似图片（无成对原图） | 鲁棒性强、覆盖更多色彩分布 | 需编程，需处理异常值 |
| **AI学习法** | 大量风格样本（≥100张） | 精度高、泛化能力强 | 需训练模型，计算资源要求高 |

---

### 二、详细实现步骤

#### 方法1：基于HaldCLUT的多张图融合法（推荐入门）

这是最可靠的传统方法，通过HaldCLUT测试图建立统一的颜色映射基准。

##### 步骤1：准备工作
1. 准备**1张中性测试图**（灰阶渐变图或HaldCLUT图，可生成）
2. 收集**5-20张风格一致的图片**（确保光照、场景类型相似）
3. 工具：Photoshop/GIMP（手动）或Python（自动），最终导出CUBE格式

##### 步骤2：生成HaldCLUT测试图（关键）
```python
# 生成标准HaldCLUT图（32×32×32网格）
from pylut import LUT
lut = LUT(size=32)  # 32³=32768个颜色点，平衡精度与文件大小
lut.identity()      # 创建单位映射（输入=输出）
lut.to_image("hald_identity.png")  # 保存为PNG
```

##### 步骤3：批量生成风格化HaldCLUT
1. 将中性HaldCLUT图分别应用到每张风格图的调色流程中（如PS的动作批量处理）
2. 对每张风格图，保存处理后的HaldCLUT结果（如style1_hald.png、style2_hald.png）
3. 关键：**禁用锐化、降噪等非色彩调整**，只保留亮度、对比度、色阶、曲线等颜色变换

##### 步骤4：融合多张HaldCLUT生成最终LUT
```python
import numpy as np
from PIL import Image
import os

def average_hald_cluts(hald_dir, output_path, size=32):
    """融合多张风格化HaldCLUT图，生成平均映射LUT"""
    hald_files = [f for f in os.listdir(hald_dir) if f.endswith(('.png', '.jpg'))]
    num_files = len(hald_files)
    if num_files == 0:
        raise ValueError("No HaldCLUT files found")
    
    # 读取第一张图作为基准
    base = np.array(Image.open(os.path.join(hald_dir, hald_files[0])).convert("RGB"), dtype=np.float32)
    sum_hald = base.copy()
    
    # 累加所有HaldCLUT图
    for f in hald_files[1:]:
        img = np.array(Image.open(os.path.join(hald_dir, f)).convert("RGB"), dtype=np.float32)
        sum_hald += img
    
    # 计算平均值（融合）
    avg_hald = (sum_hald / num_files).astype(np.uint8)
    
    # 从平均HaldCLUT生成CUBE文件
    avg_img = Image.fromarray(avg_hald)
    lut = LUT.from_image(avg_img, size=size)
    lut.to_cube(output_path)
    print(f"成功生成融合LUT: {output_path}")

# 使用示例
average_hald_cluts("hald_style_outputs/", "multi_style_lut.cube", size=32)
```

##### 步骤5：验证与优化
1. 将生成的CUBE文件导入PS/PR/Lightroom，应用到新图测试效果
2. 若颜色偏差大，可剔除异常风格图，或增加样本数量（建议≥5张）
3. 调整HaldCLUT网格大小（16→64）：越大越精确但文件更大

---

#### 方法2：基于统计分布的无成对图提取法（适合无原图场景）

当只有多张风格图而无中性原图时，通过**色彩分布匹配**建立映射。

##### 步骤1：图像预处理
```python
import cv2
import numpy as np
from glob import glob

def load_and_preprocess_images(folder_path, size=(256,256)):
    """加载并预处理多张风格图"""
    images = []
    for path in glob(f"{folder_path}/*.jpg") + glob(f"{folder_path}/*.png"):
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # 转为RGB
        img = cv2.resize(img, size)  # 统一尺寸
        img = img.astype(np.float32)/255.0  # 归一化到[0,1]
        images.append(img)
    return np.array(images)  # shape: (num_images, height, width, 3)

# 加载风格图片
style_imgs = load_and_preprocess_images("my_style_photos/")
```

##### 步骤2：提取颜色分布特征
```python
from sklearn.cluster import KMeans
from scipy.stats import gaussian_kde

def get_color_distribution(images, n_clusters=16):
    """提取多张图的颜色分布特征"""
    # 展平所有图像的像素
    pixels = images.reshape(-1, 3)
    
    # K-Means聚类提取主色调（减少计算量）
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    kmeans.fit(pixels)
    dominant_colors = kmeans.cluster_centers_
    
    # 计算颜色分布密度
    kde = gaussian_kde(pixels.T)
    return dominant_colors, kde

# 获取风格图的颜色分布
dominant_colors, color_kde = get_color_distribution(style_imgs)
```

##### 步骤3：建立中性→风格的映射关系
```python
def generate_lut_from_distribution(dominant_colors, color_kde, lut_size=32):
    """从颜色分布生成LUT"""
    lut = np.zeros((lut_size, lut_size, lut_size, 3), dtype=np.float32)
    
    # 遍历LUT的每个颜色点
    for r in range(lut_size):
        for g in range(lut_size):
            for b in range(lut_size):
                # 归一化到[0,1]
                input_rgb = np.array([r, g, b])/(lut_size-1)
                
                # 找到最匹配的主色调（简化版映射）
                distances = np.linalg.norm(dominant_colors - input_rgb, axis=1)
                closest_idx = np.argmin(distances)
                output_rgb = dominant_colors[closest_idx]
                
                # 加入分布密度调整（增强风格特征）
                density = color_kde(output_rgb)
                output_rgb = output_rgb * (0.8 + 0.4 * density / color_kde.max())
                
                lut[r, g, b] = np.clip(output_rgb, 0, 1)
    
    return lut

# 生成LUT
lut_data = generate_lut_from_distribution(dominant_colors, color_kde)
```

##### 步骤4：导出CUBE格式
```python
def save_lut_to_cube(lut_data, output_path):
    """保存LUT为CUBE文件"""
    lut_size = lut_data.shape[0]
    with open(output_path, 'w') as f:
        f.write("TITLE \"Multi-Style LUT\"\n")
        f.write("LUT_3D_SIZE {}\n".format(lut_size))
        for r in range(lut_size):
            for g in range(lut_size):
                for b in range(lut_size):
                    rgb = lut_data[r, g, b]
                    f.write(f"{rgb[0]:.6f} {rgb[1]:.6f} {rgb[2]:.6f}\n")

# 保存为CUBE
save_lut_to_cube(lut_data, "statistical_style_lut.cube")
```

---

#### 方法3：AI辅助的LUT提取法（适合专业需求）

对于大量风格样本，用神经网络学习更精确的映射关系。

##### 关键步骤
1. 准备**中性原图+风格图对**（≥50对）
2. 用TensorFlow/PyTorch训练轻量级CNN（如MobileNet）学习颜色变换
3. 固定模型后，遍历所有LUT颜色点生成映射
4. 导出CUBE格式，可结合传统方法优化边缘情况

---

### 三、实用技巧与优化建议

1. **样本选择**
   - 确保图片风格一致（如同一组滤镜、同一摄影师作品）
   - 覆盖不同亮度/色彩场景（高光、暗部、中间调都要有样本）
   - 剔除过曝、欠曝或色彩异常的图片

2. **精度控制**
   - LUT尺寸：16×16×16（快速）、32×32×32（平衡）、64×64×64（高精度）
   - 输出格式：优先CUBE（兼容PS/PR/AE/达芬奇），可选3DL、ICC

3. **常见问题解决**
   - 颜色偏差大：增加样本数量，或用中位数代替平均值减少异常值影响
   - 细节丢失：在映射中保留亮度信息（如只调整色度，保持明度不变）
   - 过渡不自然：加入高斯模糊或双边滤波优化LUT的平滑度

---

### 四、完整工作流总结

1. **准备阶段**：收集5-20张风格一致的图片，准备中性测试图
2. **映射建立**：
   - 有原图：用HaldCLUT法批量生成风格化测试图→融合生成LUT
   - 无原图：提取风格图颜色分布→建立中性到风格的映射
3. **验证优化**：在新图上测试LUT效果，调整参数或样本
4. **导出应用**：保存为CUBE格式，用于后期软件或游戏引擎

---

### 五、代码工具箱（可直接运行）

```python
# 完整依赖安装
# pip install numpy opencv-python scikit-learn scipy pillow pylut

# 工具1：生成HaldCLUT测试图
def create_hald_clut(output_path="hald_identity.png", size=32):
    from pylut import LUT
    lut = LUT(size=size)
    lut.identity()
    lut.to_image(output_path)
    print(f"HaldCLUT saved to {output_path}")

# 工具2：多张HaldCLUT融合生成CUBE
def merge_hald_to_cube(hald_folder, output_cube="merged_lut.cube", size=32):
    from pylut import LUT
    from PIL import Image
    import os
    import numpy as np
    
    hald_files = [f for f in os.listdir(hald_folder) if f.endswith(('.png', '.jpg'))]
    if not hald_files:
        raise ValueError("No HaldCLUT files found")
    
    sum_hald = np.zeros((size*size, size*size, 3), dtype=np.float32)
    for f in hald_files:
        img = np.array(Image.open(os.path.join(hald_folder, f)).convert("RGB"), dtype=np.float32)
        sum_hald += img
    
    avg_hald = (sum_hald / len(hald_files)).astype(np.uint8)
    avg_img = Image.fromarray(avg_hald)
    lut = LUT.from_image(avg_img, size=size)
    lut.to_cube(output_cube)
    print(f"Merged LUT saved to {output_cube}")

# 工具3：从风格文件夹生成LUT（无原图版）
def style_folder_to_lut(style_folder, output_cube="style_lut.cube", lut_size=32):
    import cv2
    import numpy as np
    from glob import glob
    from sklearn.cluster import KMeans
    from scipy.stats import gaussian_kde
    
    # 加载图片
    imgs = []
    for path in glob(f"{style_folder}/*.jpg") + glob(f"{style_folder}/*.png"):
        img = cv2.imread(path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (128,128))
        imgs.append(img/255.0)
    imgs = np.array(imgs)
    
    # 提取颜色分布
    pixels = imgs.reshape(-1, 3)
    kmeans = KMeans(n_clusters=16, random_state=42).fit(pixels)
    dominant = kmeans.cluster_centers_
    kde = gaussian_kde(pixels.T)
    
    # 生成LUT
    lut = np.zeros((lut_size, lut_size, lut_size, 3), dtype=np.float32)
    for r in range(lut_size):
        for g in range(lut_size):
            for b in range(lut_size):
                input_rgb = np.array([r, g, b])/(lut_size-1)
                dists = np.linalg.norm(dominant - input_rgb, axis=1)
                output_rgb = dominant[np.argmin(dists)]
                lut[r, g, b] = np.clip(output_rgb, 0, 1)
    
    # 保存CUBE
    with open(output_cube, 'w') as f:
        f.write("TITLE \"Auto Style LUT\"\nLUT_3D_SIZE {}\n".format(lut_size))
        for r in range(lut_size):
            for g in range(lut_size):
                for b in range(lut_size):
                    f.write(f"{lut[r,g,b,0]:.6f} {lut[r,g,b,1]:.6f} {lut[r,g,b,2]:.6f}\n")
    print(f"LUT saved to {output_cube}")

# 使用示例
# create_hald_clut("my_hald.png")
# merge_hald_to_cube("hald_results/", "my_style_lut.cube")
# style_folder_to_lut("my_style_photos/", "auto_style_lut.cube")
```

通过以上方法，你可以高效地从多张风格相似图片中提取出高质量的LUT，实现一键应用相同风格到新图片的效果。建议先从HaldCLUT法入手，再根据需求尝试统计或AI方法提升效果。

需要我根据你的具体情况（有无原图、样本数量、目标软件）给出定制化的步骤清单和对应的参数设置吗？