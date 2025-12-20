# -*- coding: utf-8 -*-
"""
图片打标服务
使用大模型对图片进行特征打标
"""
import os
import json
import base64
import logging
from typing import Dict, List, Optional
from openai import OpenAI
from PIL import Image

logger = logging.getLogger(__name__)

def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"编码图片失败 {image_path}: {e}")
        raise

def get_image_mime_type(image_path: str) -> str:
    """根据文件扩展名返回 MIME 类型"""
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp'
    }
    return mime_types.get(ext, 'image/jpeg')

class ImageTaggingService:
    """图片打标服务类"""
    
    def __init__(self):
        """初始化服务"""
        # 初始化OpenAI客户端（使用阿里云百炼API）
        api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-49b9d09679d54394a7d253c96e1a2596')
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen-vl-max"  # 使用qwen-vl-max模型
    
    def _build_prompt(self, features: List[Dict]) -> str:
        """
        根据特征列表构建prompt
        
        Args:
            features: 特征列表，每个特征包含 name, description, values_json 等信息
            
        Returns:
            str: 构建的prompt
        """
        prompt_parts = []
        prompt_parts.append("你是一位资深的摄影师和图像分析专家，你熟悉摄影的各种理论知识。")
        prompt_parts.append("请仔细分析这张图片，并根据要求输出相应的特征信息。")
        prompt_parts.append("")
        
        # 构建特征描述
        feature_descriptions = []
        output_fields = []
        
        for feature in features:
            name = feature.get('name', '')
            description = feature.get('description', '')
            values_json = feature.get('values_json', '')
            
            # 解析特征值
            values = []
            if values_json:
                try:
                    parsed = json.loads(values_json) if isinstance(values_json, str) else values_json
                    if isinstance(parsed, list):
                        values = parsed
                except:
                    pass
            
            # 构建特征描述
            feature_desc = f"{name}"
            if description:
                feature_desc += f"：{description}"
            if values:
                feature_desc += f"，可选值包括：{', '.join(values)}"
            
            feature_descriptions.append(f"- {feature_desc}")
            output_fields.append(f'"{name}": "对应的值"')
        
        if feature_descriptions:
            prompt_parts.append("需要分析的特征包括：")
            prompt_parts.extend(feature_descriptions)
            prompt_parts.append("")
        
        # 构建输出格式
        prompt_parts.append("请按下面格式输出结果，使用JSON格式，不要增加额外的字段，也不要删除任何字段：")
        prompt_parts.append("{")
        for field in output_fields:
            prompt_parts.append(f"    {field},")
        prompt_parts.append("}")
        
        return "\n".join(prompt_parts)
    
    def tag_image(self, image_path: str, features: List[Dict]) -> Dict:
        """
        对图片进行打标
        
        Args:
            image_path: 图片路径
            features: 特征列表，每个特征包含 name, description, values_json 等信息
            
        Returns:
            Dict: 打标结果
        """
        try:
            # 检查图片文件是否存在
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 将图片编码为 base64
            base64_image = encode_image_to_base64(image_path)
            mime_type = get_image_mime_type(image_path)
            
            # 构建prompt
            prompt = self._build_prompt(features)
            
            logger.info(f"开始调用大模型进行打标: image_path={image_path}, features={[f['name'] for f in features]}")
            logger.debug(f"Prompt: {prompt}")
            
            # 调用大模型API
            completion = self.client.chat.completions.create(
                model=self.model,
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
            
            # 解析返回结果
            result_content = completion.choices[0].message.content
            logger.debug(f"大模型返回结果: {result_content}")
            
            try:
                result_json = json.loads(result_content)
            except json.JSONDecodeError as e:
                logger.warning(f"解析JSON失败，原始内容: {result_content}")
                # 尝试提取JSON部分
                import re
                json_match = re.search(r'\{[^{}]*\}', result_content, re.DOTALL)
                if json_match:
                    result_json = json.loads(json_match.group())
                else:
                    result_json = {"raw_content": result_content, "error": "无法解析JSON"}
            
            return {
                'success': True,
                'result': result_json,
                'raw_response': result_content
            }
            
        except Exception as e:
            logger.error(f"图片打标失败 {image_path}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'result': {}
            }

