
from playwright.sync_api import Playwright, sync_playwright, expect
import re
from xiaohongshu_db.dal import create_dal
from datetime import datetime
import os
import requests
from urllib.parse import urlparse

# 在文件开头或函数外定义下载目录



dal = create_dal()
# 车静媛
# https://www.xiaohongshu.com/user/profile/66670a410000000007005db5?xsec_token=ABlppCZMF2scxXwveB1CWHSM3RqQbkTlaFKjOkmWQ0Wy4%3D&xsec_source=pc_note
#这里表示博主名字
keyword = "车静媛"
person_url = 'https://www.xiaohongshu.com/user/profile/66670a410000000007005db5?xsec_token=ABlppCZMF2scxXwveB1CWHSM3RqQbkTlaFKjOkmWQ0Wy4%3D&xsec_source=pc_note'
DOWNLOAD_DIR = f"person_images/{keyword}"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(storage_state="state.json")  # 加载状态
    page = context.new_page()
    page.goto(person_url)
    page.wait_for_timeout(5000)
    # page.get_by_role("textbox", name="搜索小红书").click()
    # page.get_by_role("textbox", name="搜索小红书").fill(keyword)
    # page.get_by_role("textbox", name="搜索小红书").press("Enter")
    # page.wait_for_timeout(2000)
    # page.get_by_text("筛选").click()
    # page.get_by_text("筛选").click()
    # page.get_by_text("最多点赞").click()
    # # page.get_by_text("筛选").first.click()
    # page.locator("span").filter(has_text="图文").click()
    # page.get_by_text("已筛选").click()
    #
    # page.wait_for_timeout(5000)

    # 增加判重逻辑
    topic_set = set()
    has_new = True
    while has_new:
        has_new = False
        section_list = page.locator("section").all()
        # last_section = section_list[-1]
        for section in section_list:
            # 判断这个section是不是合法的section，如果div下面没有a标签就不是合法的section
            if section.locator("div > a").count() == 0:
                continue
            # 优化重复的判断，不用点击section，通过section里面a的href属性
            href = section.locator("div > a").first.get_attribute('href')
            topic_id = re.findall(r'\/explore\/(\w+)', href)[0]
            if topic_id in topic_set:
                # page.locator(".close > .reds-icon").click()
                continue
            else:
                has_new = True
                topic_set.add(topic_id)

            section.click()
            page.wait_for_timeout(5000)

            url = page.url
            post_id = re.findall(r'\/explore\/(\w+)', url)[0]
            # 判断post_id是否已经存在
            if dal['post'].get_by_post_id(post_id):
                page.locator(".close > .reds-icon").click()
                continue
            desc = ''
            if page.locator("#detail-desc > span > span").count() > 0:
                desc = page.locator("#detail-desc > span > span").all()[0].inner_text()
            title_div = page.locator("#detail-title").count()
            title = ''
            if title_div > 0:
                title = page.locator("#detail-title").inner_text()

            like_count = page.locator(
                'div.interact-container > div > div.left > span.like-wrapper.like-active').inner_text()
            collect_count = page.locator('div.interact-container > div > div.left > span.collect-wrapper').inner_text()
            comment_count = page.locator('div.interact-container > div > div.left > span.chat-wrapper').inner_text()

            author_name = page.locator('span.username').all()[0].inner_text()
            author_url = page.locator('div.info > a').all()[0].get_attribute('href')
            author_id = re.findall(r'\/profile\/(\w+)', author_url)[0]
            tags = [
                tag.inner_text() for tag in page.locator('#detail-desc a').all()
            ]
            # page.locator('div.info > a').all()[0].hover()
            page.locator('div.author-container .author-wrapper .info').all()[0].hover()
            page.wait_for_timeout(1000)
            expect(page.locator('div.interaction-info'))

            # 获取作者粉丝数
            user_info = [
                user.inner_text() for user in page.locator('div.interaction-info a').all()
            ]

            print(user_info)
            # 1. 创建帖子
            post_data = {
                'post_id': post_id,
                'title': title,
                'content': desc,
                'author_id': author_id,
                'author_name': author_name,
                'author_follower_count': user_info[1].replace('粉丝',''),
                'author_like_collect_count': user_info[2].replace('获赞与收藏', ''),
                'like_count': like_count,
                'comment_count': comment_count,
                'collect_count': collect_count,
                'post_type': 'image',
                'tags': tags,
                'search_keyword': keyword,
                'publish_time': datetime.now()
            }
            post = dal['post'].create(post_data)
            # new_id = post.get('id')
            print(f"创建帖子: {post_data}")

            # 获取评论
            parent_comments = page.locator('div.list-container > .parent-comment').all()
            for parent_comment in parent_comments:
                comment = ''
                comment_id = ''
                # reply = ''
                if parent_comment.locator('>div.comment-item').count() > 0:
                    comment = parent_comment.locator('>div.comment-item span.note-text').all()[0].inner_text()
                    avatar = ''
                    if parent_comment.locator('div.avatar a img').count() > 0:
                        avatar = parent_comment.locator('div.avatar a img').first.get_attribute('src')
                    # avatar = parent_comment.locator('div.avatar a img').first.get_attribute('src')
                    user_id = parent_comment.locator('div.author a').first.get_attribute('data-user-id')
                    user_name = parent_comment.locator('div.author a').first.inner_text()
                    comment_id = parent_comment.locator('>div.comment-item').first.get_attribute('id')
                    comment_data = {
                        'comment_id': comment_id,
                        'post_id': post_id,
                        'user_name': user_name,
                        'user_id': user_id,
                        'content': comment,
                        'user_avatar': avatar,
                        'crawl_time':datetime.now()
                    }
                    # 写入评论
                    comment_object = dal['comment'].create(comment_data)

                    # 这里需要获取parent_comment_id
                if parent_comment.locator('div.reply-container').count() > 0:
                    sub_comment_items = parent_comment.locator('div.reply-container div.comment-item.comment-item-sub').all()
                    for sub_comment_item in sub_comment_items:
                        sub_comment_id = sub_comment_item.get_attribute('id')
                        # reply = parent_comment.locator('div.reply-container span.note-text').all()[0].inner_text()
                        sub_avatar = sub_comment_item.locator('div.avatar a img').first.get_attribute('src')
                        sub_user_id = sub_comment_item.locator('div.avatar a').first.get_attribute('data-user-id')
                        sub_user_name = sub_comment_item.locator('div.right div.author a').first.inner_text()
                        content = sub_comment_item.locator('div.right div.content span').first.inner_text()
                        # 写入评论的回复
                        reply_data = {
                            'post_id': post_id,
                            'comment_id': sub_comment_id,
                            'parent_comment_id': comment_id,
                            'user_name': sub_user_name,
                            'user_id': sub_user_id,
                            'content': content,
                            'user_avatar': sub_avatar,
                            'crawl_time': datetime.now(),

                        }
                        dal['comment'].create(reply_data)
                # reply = parent_comment.locator('div.reply-container').all()[0].inner_text()
                # total_comments.append(comment + '::' + reply + '##')


            # 媒体记录
            image_list = page.locator('div.swiper-wrapper > div img').all()
            image_list = image_list[1:-1]
            for image in image_list:
                # 下载图片到本地
                downloaded_path = None
                download_status = "failed"
                media_url = image.get_attribute('src')
                try:
                    # 发送HTTP请求获取图片
                    response = requests.get(media_url, timeout=30)
                    response.raise_for_status()

                    # 解析URL获取文件名
                    parsed_url = urlparse(media_url)
                    filename = os.path.basename(parsed_url.path)
                    if not filename or '.' not in filename:
                        filename = f"image_{post_id}_{image_list.index(image)}.jpg"

                    # 构造保存路径
                    file_path = os.path.join(DOWNLOAD_DIR, filename)

                    # 保存图片
                    with open(file_path, 'wb') as f:
                        f.write(response.content)

                    downloaded_path = file_path
                    download_status = "success"
                except Exception as e:
                    print(f"下载图片失败 {media_url}: {e}")
                    download_status = "failed"

                media_data = {
                    'post_id': post_id,
                    'media_type': 'image',
                    'media_url': image.get_attribute('src'),
                    'width': image.get_attribute('width'),
                    'height': image.get_attribute('height'),
                    'sort_order': image_list.index(image),
                    'download_time': datetime.now(),
                    'download_status': download_status,
                    'media_local_path': downloaded_path
                }
                media = dal['media'].create(media_data)
                print(f"创建媒体记录: {media_data}")

            page.locator(".close > .reds-icon").click()

    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
