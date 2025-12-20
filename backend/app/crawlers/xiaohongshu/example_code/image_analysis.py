import os
import json
import base64
from openai import OpenAI

# 删除照片美学倾向，改为美学风格
# 增加人像景别：半身、全身
# 增加美学评分：1-10分


def encode_image_to_base64(image_path):
    """将图片文件编码为 base64 字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def get_image_mime_type(image_path):
    """根据文件扩展名返回 MIME 类型"""
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


client = OpenAI(
    # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx"
    api_key='sk-49b9d09679d54394a7d253c96e1a2596',
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

prompt = """你是一位资深的摄影师，你熟悉摄影的各种理论知识。你能够很清晰的分辨出图片的光线特征，景别和人物情绪姿态，并给出照片的美学风格；
其中光线特征分为：
方向: 顺光、左侧光、右侧光、逆光、顶光、脚光；
光源位置: 左侧、右侧、顶部、底部、中心、后方；
光源个数: 单个、多个；
主导色: 红色、蓝色、绿色、黄色、紫色、橙色、棕色、灰色、黑色、白色；
色温: 暖光、冷光；
强度: 强光、弱光；
质地: 硬光、柔光；
来源: 自然光、人造光；
影调亮度: 高调、低调、中间调；
影调跨度: 长调、中调、短调；
影调反差: 硬调、软调；
影调质感: 高质感、低质感、中间质感；
景别包括：
远景、全景、中景、近景、特写；
人像景别包括：
九分人像、七分人像、半身人像、全身人像、特写；
人物情绪包括：
喜悦、悲伤、愤怒、恐惧、惊讶、严肃、安静、厌恶、孤独；
人物姿态包括：
站姿、坐姿、躺姿、跪姿、蹲姿、动态姿势；
人脸朝向包括:
正面视图、三分之四视图、左侧面视图、右侧面视图、背面视图；
头部倾斜：
正头、左侧头、右侧头、低头、抬头；
人物位置(人像在画面中的位置)：
左侧、偏左、中心、偏右、右侧；
美学风格包括：
文艺风、复古风、纪实风、极简风、极繁风、现代风、后现代风、超现实风、梦幻风、童话风、科幻风、未来风；
照片情绪：
愉悦、悲伤、愤怒、恐惧、惊讶、严肃、安静、厌恶、孤独；

给你一张照片，请按下面格式输出结果，不要增加额外的字段，也不要删除任何字段：
{
    "光线方向": "顺光",
    "光源位置": "左侧",
    "光源个数": "单个",
    "主导色": "红色",
    "光线冷暖": "暖光",
    "光线强度": "强光",
    "光线质地": "硬光",
    "光线来源": "自然光",
    "影调亮度": "高调",
    "影调跨度": "长调",
    "影调反差": "硬调",
    "影调质感": "高质感",
    "景别": "远景",
    "人像景别": "九分人像",
    "人物情绪": "喜悦",
    "人物姿态": "站姿",
    "人脸朝向": "正面",
    "头部倾斜": "低头",
    "人物位置": "中心",
    "美学风格": "文艺风",
    "照片情绪": "愉悦",
    
}"""


def image_analysis(image_path, is_absolute_path=False):
    """
    分析图片的光线特征、构图方法、景别和人物情绪姿态

    Args:
        image_path: 图片文件路径
        is_absolute_path: 如果为 True，image_path 是绝对路径；
                         如果为 False，是相对于 images/ 目录的路径
    """
    # 使用基于脚本文件所在目录的绝对路径
    if is_absolute_path:
        full_image_path = image_path
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        full_image_path = os.path.join(project_root, "src/images", image_path)

    # 将图片编码为 base64
    base64_image = encode_image_to_base64(full_image_path)
    mime_type = get_image_mime_type(full_image_path)

    # 使用 base64 数据调用 API
    completion = client.chat.completions.create(
        # 模型列表 qwen-vl-plus、qwen-vl-max、qwen3-omni-flash
        # model="qwen-vl-plus",  # 此处以qwen-vl-plus为例，可按需更换模型名称
        model="qwen-vl-max",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        response_format={"type": "json_object"}
    )
    print(completion.model_dump_json())
    return completion.choices[0].message.content


class BatchImageAnalyzer:
    """
    批量图片特征分析类
    用于批量分析 images 目录下所有图片的特征并保存为 JSON 文件
    """

    def __init__(self, image_dir=None, output_dir=None):
        """
        初始化批量分析器

        Args:
            image_dir: 图片目录路径，如果为 None 则使用默认的 images 目录
            output_dir: 输出目录，如果为 None 则保存到 images 目录的对应子目录中
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)

        if image_dir is None:
            self.image_dir = os.path.join(project_root, "src/images")
        else:
            self.image_dir = image_dir

        self.output_dir = output_dir
        self.project_root = project_root

        # 支持的图片格式
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp',
                                 '.bmp'}

        # 统计信息
        self.stats = {
            'total_images': 0,
            'success_count': 0,
            'error_count': 0
        }

    def _get_all_image_files(self):
        """
        获取所有图片文件（包括子目录）

        Returns:
            list: [(相对路径, 绝对路径, 子目录名), ...]
        """
        image_files = []

        # 遍历 images 目录及其子目录
        for root, dirs, files in os.walk(self.image_dir):
            for filename in files:
                ext = os.path.splitext(filename)[1].lower()
                if ext in self.image_extensions:
                    full_path = os.path.join(root, filename)
                    # 计算相对于 images 目录的路径
                    rel_path = os.path.relpath(full_path, self.image_dir)
                    # 获取子目录名（如果存在）
                    subdir = (os.path.dirname(rel_path)
                              if os.path.dirname(rel_path) else None)
                    image_files.append((rel_path, full_path, subdir))

        # 按路径排序
        image_files.sort(key=lambda x: x[0])
        return image_files

    def _get_output_file_path(self, rel_path, subdir):
        """
        获取输出文件路径

        Args:
            rel_path: 相对于 images 目录的路径
            subdir: 子目录名

        Returns:
            str: 输出文件的完整路径
        """
        if self.output_dir is None:
            # 保存到对应的子目录中
            base_name = os.path.splitext(rel_path)[0]
            output_file = os.path.join(self.image_dir, f"{base_name}.json")
        else:
            # 保存到指定的输出目录，保持子目录结构
            output_dir_full = os.path.join(self.project_root, self.output_dir)
            if subdir:
                output_subdir = os.path.join(output_dir_full, subdir)
                os.makedirs(output_subdir, exist_ok=True)
                base_name = os.path.splitext(
                    os.path.basename(rel_path))[0]
                output_file = os.path.join(
                    output_subdir, f"{base_name}.json")
            else:
                base_name = os.path.splitext(rel_path)[0]
                output_file = os.path.join(
                    output_dir_full, f"{base_name}.json")

        return output_file

    def analyze(self):
        """
        执行批量分析

        Returns:
            dict: 统计信息 {'total_images': int, 'success_count': int,
                  'error_count': int}
        """
        # 获取所有图片文件
        image_files = self._get_all_image_files()
        self.stats['total_images'] = len(image_files)

        if not image_files:
            print(f"在 {self.image_dir} 中没有找到图片文件")
            return self.stats

        print(f"找到 {len(image_files)} 张图片，开始分析...")

        # 遍历每张图片
        for idx, (rel_path, full_path, subdir) in enumerate(image_files, 1):
            print(f"\n[{idx}/{len(image_files)}] 正在处理: {rel_path}")

            try:
                # 调用分析函数（使用绝对路径）
                result_content = image_analysis(full_path,
                                                is_absolute_path=True)

                # 解析 JSON 字符串
                try:
                    result_json = json.loads(result_content)
                except json.JSONDecodeError:
                    # 如果解析失败，将原始内容保存
                    result_json = {"raw_content": result_content}

                # 获取输出文件路径
                output_file = self._get_output_file_path(rel_path, subdir)

                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # 保存 JSON 文件
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result_json, f, ensure_ascii=False, indent=2)

                print(f"✓ 已保存: {output_file}")
                self.stats['success_count'] += 1

            except Exception as e:
                print(f"✗ 处理失败: {rel_path}, 错误: {str(e)}")
                self.stats['error_count'] += 1

        print(f"\n处理完成！成功: {self.stats['success_count']}, "
              f"失败: {self.stats['error_count']}")

        return self.stats

    def get_stats(self):
        """
        获取统计信息

        Returns:
            dict: 统计信息
        """
        return self.stats.copy()


# 为了向后兼容，保留函数接口
def batch_analyze_images(output_dir=None):
    """
    遍历 images 目录中的所有图片（包括子目录），调用 image_analysis 方法，
    并将结果保存为对应名称的 JSON 文件

    Args:
        output_dir: 输出目录，如果为 None 则保存到 images 目录的对应子目录中
    """
    analyzer = BatchImageAnalyzer(output_dir=output_dir)
    return analyzer.analyze()


def calculate_similarity(features1, features2):
    """
    计算两个特征字典的相似度
    相似度 = 匹配的特征数 / 总的特征数
    
    Args:
        features1: 第一个图片的特征字典
        features2: 第二个图片的特征字典
        
    Returns:
        float: 相似度值（0-1之间）
    """
    if not features1 or not features2:
        return 0.0
    
    # 排除 raw_content 等非特征字段
    exclude_keys = {'raw_content'}
    
    # 获取所有特征键
    all_keys = set(features1.keys()) | set(features2.keys())
    all_keys = {k for k in all_keys if k not in exclude_keys}
    
    if not all_keys:
        return 0.0
    
    # 计算匹配的特征数
    match_count = 0
    for key in all_keys:
        val1 = features1.get(key)
        val2 = features2.get(key)
        if val1 is not None and val2 is not None and val1 == val2:
            match_count += 1
    
    # 相似度 = 匹配数 / 总数
    similarity = match_count / len(all_keys) if all_keys else 0.0
    return similarity


def load_all_features():
    """
    加载 images 目录下所有子目录中的特征 JSON 文件
    
    Returns:
        dict: {子目录名: {图片名: 特征字典}}
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    image_dir = os.path.join(project_root, "src/images")
    
    all_features = {}
    
    # 遍历所有子目录
    for item in os.listdir(image_dir):
        item_path = os.path.join(image_dir, item)
        if os.path.isdir(item_path):
            subdir_features = {}
            # 遍历子目录中的 JSON 文件
            for filename in os.listdir(item_path):
                if filename.endswith('.json'):
                    json_path = os.path.join(item_path, filename)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            features = json.load(f)
                            # 使用不带扩展名的文件名作为键
                            image_name = os.path.splitext(filename)[0]
                            subdir_features[image_name] = features
                    except Exception as e:
                        print(f"加载 JSON 文件失败 {json_path}: {str(e)}")
            
            if subdir_features:
                all_features[item] = subdir_features
    
    return all_features


def find_most_similar_images(uploaded_features, all_features):
    """
    找出每个子目录下与上传图片最相似的三张图片
    
    Args:
        uploaded_features: 上传图片的特征字典
        all_features: 所有图片的特征字典 {子目录名: {图片名: 特征字典}}
        
    Returns:
        dict: {子目录名: [(图片名1, 相似度1), (图片名2, 相似度2), (图片名3, 相似度3)]}
    """
    results = {}
    
    for subdir, images_features in all_features.items():
        similarities = []
        for image_name, features in images_features.items():
            similarity = calculate_similarity(uploaded_features, features)
            similarities.append((image_name, similarity))
        
        # 按相似度降序排序，取前三个
        similarities.sort(key=lambda x: x[1], reverse=True)
        results[subdir] = similarities[:3]
    
    return results


if __name__ == "__main__":
    # 单张图片测试
    # analysis_result = image_analysis("发丝发光/11.jpg")
    # print(analysis_result)

    # 批量处理所有图片 - 使用类方式
    # analyzer = BatchImageAnalyzer()
    # stats = analyzer.analyze()
    # print(f"\n最终统计: {stats}")

    # 或者使用函数方式（向后兼容）
    batch_analyze_images()



