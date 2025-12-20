"""
小红书爬虫服务 - 基于Playwright实现
参考示例代码：playwright_test_db_with_download.py
"""
import json
import logging
import sys
import os
import re
import requests
import hashlib
from urllib.parse import urlparse
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError, expect
from PIL import Image as PILImage

from app.database import db
from app.models.post import Post
from app.models.post_media import PostMedia
from app.models.post_comment import PostComment
from app.models.image import Image
from app.models.crawler_cookie import CrawlerCookie
from app.utils.config_manager import get_local_image_dir, get_relative_path

logger = logging.getLogger(__name__)

class XiaohongshuCrawlerService:
    """小红书爬虫服务类"""
    
    def __init__(self):
        self.timeout = 60000  # 60秒超时
        self.download_dir = get_local_image_dir()  # 使用config.json中的配置
        os.makedirs(self.download_dir, exist_ok=True)
    
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
            logger.error(f"计算图片哈希失败 {file_path}: {e}")
            return None
    
    def get_cookie_list(self, cookie_json_str):
        """从cookie JSON字符串转换为Playwright cookie列表"""
        try:
            cookies = json.loads(cookie_json_str)
            # 转换为Playwright格式
            playwright_cookies = []
            for name, value in cookies.items():
                playwright_cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.xiaohongshu.com',
                    'path': '/'
                })
            return playwright_cookies
        except Exception as e:
            logger.error(f"解析Cookie失败: {e}")
            return None
    
    def crawl_by_keyword(self, keyword, cookie_json_str=None, max_posts=10, task_id=None):
        """
        根据关键字爬取小红书内容
        
        Args:
            keyword: 搜索关键字
            cookie_json_str: Cookie JSON字符串
            max_posts: 最大爬取帖子数
            task_id: 任务ID（用于更新进度）
        
        Returns:
            dict: 包含成功状态和统计信息
        """
        logger.info(f"开始爬取小红书，关键字: {keyword}, 最大帖子数: {max_posts}")
        
        stats = {
            'posts': 0,
            'comments': 0,
            'media': 0,
            'images': 0,
            'errors': []
        }
        
        try:
            logger.info("启动Playwright浏览器...")
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=False,  # 调试时设置为False，生产环境可设置为True
                    args=['--disable-blink-features=AutomationControlled', '--disable-extensions']
                )
                logger.info("浏览器启动成功")
                
                # 创建上下文
                context_options = {
                    'viewport': {'width': 1280, 'height': 800},
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'locale': 'zh-CN'
                }
                
                context = browser.new_context(**context_options)
                logger.info("浏览器上下文创建成功")
                
                # 如果有Cookie，添加到上下文
                if cookie_json_str:
                    cookie_list = self.get_cookie_list(cookie_json_str)
                    if cookie_list:
                        try:
                            context.add_cookies(cookie_list)
                            logger.info(f"成功添加 {len(cookie_list)} 个Cookie")
                        except Exception as e:
                            logger.warning(f"添加Cookie失败: {e}")
                
                page = context.new_page()
                logger.info("新页面创建成功")
                
                try:
                    # 访问小红书
                    logger.info("访问小红书首页...")
                    try:
                        page.goto("https://www.xiaohongshu.com/explore", timeout=self.timeout)
                        logger.info("小红书首页访问成功")
                        page.wait_for_timeout(5000)
                    except Exception as goto_error:
                        logger.error(f"访问小红书首页失败: {goto_error}", exc_info=True)
                        raise
                    
                    # 搜索关键字
                    logger.info(f"搜索关键字: {keyword}")
                    try:
                        search_box = page.get_by_role("textbox", name="搜索小红书")
                        if search_box.count() == 0:
                            logger.error("未找到搜索框，可能页面未加载完成")
                            raise Exception("未找到搜索框")
                        search_box.click()
                        search_box.fill(keyword)
                        search_box.press("Enter")
                        page.wait_for_timeout(2000)
                        logger.info("关键字搜索成功")
                    except Exception as search_error:
                        logger.error(f"搜索关键字失败: {search_error}", exc_info=True)
                        raise
                    
                    # 筛选：最多点赞、图文
                    logger.info("设置筛选条件...")
                    page.get_by_text("筛选").click()
                    page.get_by_text("筛选").click()
                    page.get_by_text("最多点赞").click()
                    page.locator("span").filter(has_text="图文").click()
                    page.get_by_text("已筛选").click()
                    page.wait_for_timeout(5000)
                    
                    # 爬取帖子
                    topic_set = set()
                    has_new = True
                    post_count = 0
                    
                    while has_new and post_count < max_posts:
                        has_new = False
                        section_list = page.locator("section").all()
                        
                        for section in section_list:
                            if post_count >= max_posts:
                                break
                            
                            # 判断section是否合法
                            if section.locator("div > a").count() == 0:
                                continue
                            
                            # 获取帖子ID
                            href = section.locator("div > a").first.get_attribute('href')
                            try:
                                topic_id = re.findall(r'\/explore\/(\w+)', href)[0]
                            except:
                                continue
                            
                            if topic_id in topic_set:
                                continue
                            
                            has_new = True
                            topic_set.add(topic_id)
                            
                            # 点击进入帖子详情
                            section.click()
                            page.wait_for_timeout(5000)
                            
                            url = page.url
                            try:
                                post_id = re.findall(r'\/explore\/(\w+)', url)[0]
                            except:
                                page.locator(".close > .reds-icon").click()
                                continue
                            
                            # 检查帖子是否已存在
                            existing_post = Post.query.filter_by(post_id=post_id).first()
                            if existing_post:
                                logger.info(f"帖子已存在，跳过: {post_id}")
                                page.locator(".close > .reds-icon").click()
                                continue
                            
                            # 爬取帖子数据
                            try:
                                result = self._crawl_post_detail(page, post_id, keyword, task_id)
                                if result:
                                    stats['posts'] += 1
                                    stats['comments'] += result.get('comments', 0)
                                    stats['media'] += result.get('media', 0)
                                    stats['images'] += result.get('images', 0)
                                    post_count += 1
                                    
                                    # 更新任务进度
                                    if task_id:
                                        self._update_task_progress(task_id, post_count, stats)
                            except Exception as e:
                                error_msg = f"爬取帖子失败 {post_id}: {str(e)}"
                                logger.error(error_msg, exc_info=True)
                                stats['errors'].append(error_msg)
                            
                            # 关闭详情页
                            page.locator(".close > .reds-icon").click()
                            page.wait_for_timeout(2000)
                    
                    logger.info(f"爬取完成，统计: {stats}")
                    return {
                        'success': True,
                        'message': '爬取完成',
                        'stats': stats
                    }
                    
                except Exception as e:
                    error_msg = f"爬取过程出错: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    stats['errors'].append(error_msg)
                    return {
                        'success': False,
                        'message': error_msg,
                        'stats': stats
                    }
                finally:
                    # 确保浏览器被正确关闭
                    try:
                        if page:
                            logger.info("关闭页面...")
                            page.close()
                        if context:
                            logger.info("关闭上下文...")
                            context.close()
                        if browser:
                            logger.info("关闭浏览器...")
                            browser.close()
                    except Exception as close_error:
                        logger.error(f"关闭浏览器时出错: {close_error}", exc_info=True)
                    
        except Exception as e:
            error_msg = f"Playwright执行失败: {str(e)}"
            logger.critical(error_msg, exc_info=True)
            stats['errors'].append(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'stats': stats
            }
    
    def _crawl_post_detail(self, page, post_id, keyword, task_id=None):
        """爬取帖子详情"""
        try:
            # 获取帖子基本信息
            desc = ''
            if page.locator("#detail-desc > span > span").count() > 0:
                desc = page.locator("#detail-desc > span > span").all()[0].inner_text()
            
            title = ''
            if page.locator("#detail-title").count() > 0:
                title = page.locator("#detail-title").inner_text()
            
            like_count = '0'
            if page.locator('div.interact-container > div > div.left > span.like-wrapper.like-active').count() > 0:
                like_count = page.locator('div.interact-container > div > div.left > span.like-wrapper.like-active').inner_text()
            
            collect_count = '0'
            if page.locator('div.interact-container > div > div.left > span.collect-wrapper').count() > 0:
                collect_count = page.locator('div.interact-container > div > div.left > span.collect-wrapper').inner_text()
            
            comment_count = '0'
            if page.locator('div.interact-container > div > div.left > span.chat-wrapper').count() > 0:
                comment_count = page.locator('div.interact-container > div > div.left > span.chat-wrapper').inner_text()
            
            author_name = ''
            author_url = ''
            author_id = ''
            if page.locator('span.username').count() > 0:
                author_name = page.locator('span.username').all()[0].inner_text()
            if page.locator('div.info > a').count() > 0:
                author_url = page.locator('div.info > a').all()[0].get_attribute('href')
                try:
                    author_id = re.findall(r'\/profile\/(\w+)', author_url)[0]
                except:
                    pass
            
            # 获取标签
            tags = []
            if page.locator('#detail-desc a').count() > 0:
                tags = [tag.inner_text() for tag in page.locator('#detail-desc a').all()]
            
            # 获取作者信息
            author_follower_count = '0'
            author_like_collect_count = '0'
            if page.locator('div.author-container .author-wrapper .info').count() > 0:
                page.locator('div.author-container .author-wrapper .info').all()[0].hover()
                page.wait_for_timeout(1000)
                if page.locator('div.interaction-info').count() > 0:
                    user_info = [user.inner_text() for user in page.locator('div.interaction-info a').all()]
                    if len(user_info) > 1:
                        author_follower_count = user_info[1].replace('粉丝', '')
                    if len(user_info) > 2:
                        author_like_collect_count = user_info[2].replace('获赞与收藏', '')
            
            # 创建帖子记录
            post_data = {
                'post_id': post_id,
                'title': title,
                'content': desc,
                'author_id': author_id,
                'author_name': author_name,
                'author_follower_count': author_follower_count,
                'author_like_collect_count': author_like_collect_count,
                'like_count': like_count,
                'comment_count': comment_count,
                'collect_count': collect_count,
                'post_type': 'image',
                'tags': tags,
                'search_keyword': keyword,
                'publish_time': datetime.now(),
                'crawl_time': datetime.now()
            }
            
            post = Post(**post_data)
            db.session.add(post)
            db.session.flush()  # 获取ID但不提交
            
            # 爬取评论
            comment_count_num = self._crawl_comments(page, post_id)
            
            # 爬取媒体（图片）
            media_count, image_count = self._crawl_media(page, post_id, keyword, tags)
            
            # 提交事务
            db.session.commit()
            
            logger.info(f"成功爬取帖子: {post_id}, 评论数: {comment_count_num}, 媒体数: {media_count}")
            
            return {
                'comments': comment_count_num,
                'media': media_count,
                'images': image_count
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"爬取帖子详情失败 {post_id}: {str(e)}", exc_info=True)
            raise
    
    def _crawl_comments(self, page, post_id):
        """爬取评论"""
        comment_count = 0
        try:
            parent_comments = page.locator('div.list-container > .parent-comment').all()
            
            for parent_comment in parent_comments:
                comment = ''
                comment_id = ''
                
                if parent_comment.locator('>div.comment-item').count() > 0:
                    comment = parent_comment.locator('>div.comment-item span.note-text').all()[0].inner_text()
                    avatar = ''
                    if parent_comment.locator('div.avatar a img').count() > 0:
                        avatar = parent_comment.locator('div.avatar a img').first.get_attribute('src')
                    
                    user_id = ''
                    if parent_comment.locator('div.author a').count() > 0:
                        user_id = parent_comment.locator('div.author a').first.get_attribute('data-user-id')
                    
                    user_name = ''
                    if parent_comment.locator('div.author a').count() > 0:
                        user_name = parent_comment.locator('div.author a').first.inner_text()
                    
                    comment_id = parent_comment.locator('>div.comment-item').first.get_attribute('id')
                    
                    # 检查评论是否已存在
                    existing_comment = PostComment.query.filter_by(comment_id=comment_id).first()
                    if not existing_comment:
                        comment_data = {
                            'comment_id': comment_id,
                            'post_id': post_id,
                            'user_name': user_name,
                            'user_id': user_id,
                            'content': comment,
                            'user_avatar': avatar,
                            'crawl_time': datetime.now()
                        }
                        comment_obj = PostComment(**comment_data)
                        db.session.add(comment_obj)
                        comment_count += 1
                
                # 爬取回复
                if parent_comment.locator('div.reply-container').count() > 0:
                    sub_comment_items = parent_comment.locator('div.reply-container div.comment-item.comment-item-sub').all()
                    for sub_comment_item in sub_comment_items:
                        sub_comment_id = sub_comment_item.get_attribute('id')
                        
                        # 检查回复是否已存在
                        existing_reply = PostComment.query.filter_by(comment_id=sub_comment_id).first()
                        if existing_reply:
                            continue
                        
                        sub_avatar = ''
                        if sub_comment_item.locator('div.avatar a img').count() > 0:
                            sub_avatar = sub_comment_item.locator('div.avatar a img').first.get_attribute('src')
                        
                        sub_user_id = ''
                        if sub_comment_item.locator('div.avatar a').count() > 0:
                            sub_user_id = sub_comment_item.locator('div.avatar a').first.get_attribute('data-user-id')
                        
                        sub_user_name = ''
                        if sub_comment_item.locator('div.right div.author a').count() > 0:
                            sub_user_name = sub_comment_item.locator('div.right div.author a').first.inner_text()
                        
                        content = ''
                        if sub_comment_item.locator('div.right div.content span').count() > 0:
                            content = sub_comment_item.locator('div.right div.content span').first.inner_text()
                        
                        reply_data = {
                            'post_id': post_id,
                            'comment_id': sub_comment_id,
                            'parent_comment_id': comment_id,
                            'user_name': sub_user_name,
                            'user_id': sub_user_id,
                            'content': content,
                            'user_avatar': sub_avatar,
                            'crawl_time': datetime.now()
                        }
                        reply_obj = PostComment(**reply_data)
                        db.session.add(reply_obj)
                        comment_count += 1
            
        except Exception as e:
            logger.error(f"爬取评论失败 {post_id}: {str(e)}", exc_info=True)
        
        return comment_count
    
    def _crawl_media(self, page, post_id, keyword, tags=None):
        """爬取媒体（图片）"""
        media_count = 0
        image_count = 0
        
        # 确保tags是列表
        if tags is None:
            tags = []
        
        try:
            image_list = page.locator('div.swiper-wrapper > div img').all()
            if len(image_list) > 2:
                image_list = image_list[1:-1]  # 排除首尾
            
            for idx, image in enumerate(image_list):
                media_url = image.get_attribute('src')
                if not media_url:
                    continue
                
                # 下载图片
                downloaded_path = None
                download_status = "failed"
                file_size = None
                width = None
                height = None
                
                try:
                    response = requests.get(media_url, timeout=30)
                    response.raise_for_status()
                    
                    # 解析URL获取文件名
                    parsed_url = urlparse(media_url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename or '.' not in filename:
                        filename = f"image_{post_id}_{idx}.jpg"
                    
                    # 创建关键字目录
                    keyword_dir = os.path.join(self.download_dir, keyword.replace('/', '_'))
                    os.makedirs(keyword_dir, exist_ok=True)
                    
                    # 构造保存路径（绝对路径）
                    file_path = os.path.join(keyword_dir, filename)
                    
                    # 保存图片
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    # 转换为相对路径用于存储
                    relative_path = get_relative_path(file_path)
                    downloaded_path = relative_path  # 存储相对路径
                    download_status = "success"
                    file_size = len(response.content)
                    
                    # 获取图片尺寸
                    try:
                        from PIL import Image as PILImage
                        img = PILImage.open(file_path)
                        width, height = img.size
                    except:
                        pass
                    
                except Exception as e:
                    logger.error(f"下载图片失败 {media_url}: {e}")
                    download_status = "failed"
                
                # 计算图片哈希值（如果下载成功）
                image_hash = None
                if download_status == 'success' and downloaded_path:
                    try:
                        # 使用绝对路径计算哈希值
                        image_hash = self._compute_image_hash(file_path)
                    except Exception as e:
                        logger.error(f"计算图片哈希值失败 {file_path}: {e}")
                
                # 创建媒体记录
                media_data = {
                    'post_id': post_id,
                    'media_type': 'image',
                    'media_url': media_url,
                    'media_local_path': downloaded_path,
                    'width': width,
                    'height': height,
                    'sort_order': idx,
                    'download_status': download_status,
                    'download_time': datetime.now() if download_status == 'success' else None,
                    'file_size': file_size,
                    'image_hash': image_hash,
                    'create_time': datetime.now()
                }
                
                media_obj = PostMedia(**media_data)
                db.session.add(media_obj)
                media_count += 1
                
                # 如果下载成功，同时保存到images表
                if download_status == 'success' and downloaded_path:
                    try:
                        # 使用已计算的image_hash
                        
                        # 优先根据image_hash检查是否已存在
                        existing_image = None
                        if image_hash:
                            existing_image = Image.query.filter_by(image_hash=image_hash).first()
                        
                        # 如果image_hash不存在或未找到，再根据original_url检查
                        if not existing_image:
                            existing_image = Image.query.filter_by(original_url=media_url).first()
                        
                        # 如果图片已存在，跳过添加
                        if existing_image:
                            logger.info(f"图片已存在，跳过添加 (hash: {image_hash}, url: {media_url})")
                        else:
                            # 获取文件格式
                            file_format = filename.split('.')[-1] if '.' in filename else 'jpg'
                            
                            # 将标签转换为JSON字符串
                            hash_tags_json = json.dumps(tags, ensure_ascii=False) if tags else None
                            
                            image_data = {
                                'filename': filename,
                                'storage_path': downloaded_path,  # 存储相对路径
                                'original_url': media_url,
                                'status': 'active',
                                'storage_mode': 'local',
                                'source_site': 'xiaohongshu',
                                'keyword': keyword,
                                'hash_tags_json': hash_tags_json,
                                'image_hash': image_hash,
                                'width': width,
                                'height': height,
                                'format': file_format
                            }
                            image_obj = Image(**image_data)
                            db.session.add(image_obj)
                            image_count += 1
                    except Exception as e:
                        logger.error(f"保存图片到images表失败: {e}", exc_info=True)
            
        except Exception as e:
            logger.error(f"爬取媒体失败 {post_id}: {str(e)}", exc_info=True)
        
        return media_count, image_count
    
    def _update_task_progress(self, task_id, post_count, stats):
        """更新任务进度"""
        try:
            from app.models.crawler_task import CrawlerTask
            task = CrawlerTask.query.get(task_id)
            if task:
                task.processed_posts = post_count
                task.processed_comments = stats.get('comments', 0)
                task.downloaded_media = stats.get('media', 0)
                progress = {
                    'posts': post_count,
                    'comments': stats.get('comments', 0),
                    'media': stats.get('media', 0),
                    'images': stats.get('images', 0)
                }
                task.progress_json = json.dumps(progress, ensure_ascii=False)
                db.session.commit()
        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")

