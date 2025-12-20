"""
Cookie获取服务 - 使用Playwright自动登录并获取Cookie
"""
import json
import logging
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class CookieFetcherService:
    """Cookie获取服务类"""
    
    def __init__(self):
        self.timeout = 30000  # 30秒超时
    
    def fetch_xiaohongshu_cookie(self, account, verification_code=None, password=None):
        """
        获取小红书Cookie
        
        Args:
            account: 账号（手机号）
            verification_code: 验证码（如果使用验证码登录）
            password: 密码（如果使用密码登录）
        
        Returns:
            dict: 包含cookie_json和成功状态
        """
        logger.info(f"开始获取小红书Cookie，账号: {account}, 登录方式: {'验证码' if verification_code else '密码'}")
        
        try:
            with sync_playwright() as playwright:
                logger.info("启动Playwright浏览器...")
                browser = playwright.chromium.launch(
                    headless=False,
                    args=['--disable-blink-features=AutomationControlled']
                )
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                try:
                    logger.info("访问小红书登录页面...")
                    # 访问小红书登录页面
                    page.goto("https://www.xiaohongshu.com/explore", timeout=self.timeout)
                    page.wait_for_timeout(3000)  # 增加等待时间
                    logger.info("页面加载完成")
                    
                    # 点击登录按钮或输入框
                    logger.info("查找登录输入框...")
                    try:
                        page.get_by_role("textbox", name="+").click(timeout=10000)
                        logger.info("找到登录输入框（方式1）")
                    except Exception as e1:
                        logger.warning(f"方式1失败: {str(e1)}")
                        try:
                            # 如果找不到，尝试其他方式
                            page.locator("input[placeholder*='手机号'], input[placeholder*='账号']").first.click(timeout=10000)
                            logger.info("找到登录输入框（方式2）")
                        except Exception as e2:
                            logger.error(f"方式2也失败: {str(e2)}")
                            # 尝试点击登录按钮
                            try:
                                page.locator("text=登录").first.click(timeout=5000)
                                page.wait_for_timeout(2000)
                            except:
                                pass
                    
                    logger.info(f"输入账号: {account}")
                    # 输入账号
                    try:
                        page.get_by_role("textbox", name="+").fill(account)
                    except:
                        page.locator("input[placeholder*='手机号'], input[placeholder*='账号']").first.fill(account)
                    
                    page.wait_for_timeout(2000)  # 增加等待时间
                    
                    logger.info("点击下一步按钮...")
                    # 点击下一步或获取验证码按钮
                    try:
                        page.locator(".icon-wrapper").first.click(timeout=10000)
                    except Exception as e:
                        logger.warning(f"点击下一步失败: {str(e)}")
                        # 尝试其他方式
                        try:
                            page.locator("button:has-text('下一步'), button:has-text('获取验证码')").first.click(timeout=5000)
                        except:
                            pass
                    
                    page.wait_for_timeout(3000)  # 增加等待时间
                    
                    # 根据登录方式处理
                    if verification_code:
                        logger.info("使用验证码登录...")
                        # 验证码登录
                        try:
                            page.get_by_role("spinbutton", name="获取验证码").fill(verification_code)
                        except:
                            page.locator("input[type='text'], input[placeholder*='验证码']").first.fill(verification_code)
                        page.wait_for_timeout(2000)
                        try:
                            page.locator("form").get_by_role("button", name="登录").click(timeout=10000)
                        except:
                            page.locator("button:has-text('登录')").first.click(timeout=10000)
                    elif password:
                        logger.info("使用密码登录...")
                        # 密码登录（需要先切换到密码登录）
                        try:
                            # 尝试点击"密码登录"标签
                            page.locator("text=密码登录").first.click(timeout=5000)
                            page.wait_for_timeout(2000)
                        except:
                            pass
                        
                        password_input = page.locator("input[type='password']").first
                        password_input.fill(password)
                        page.wait_for_timeout(2000)
                        try:
                            page.locator("form").get_by_role("button", name="登录").click(timeout=10000)
                        except:
                            page.locator("button:has-text('登录')").first.click(timeout=10000)
                    else:
                        raise ValueError("需要提供验证码或密码")
                    
                    logger.info("等待登录完成...")
                    # 等待登录完成
                    page.wait_for_timeout(8000)  # 增加等待时间，让用户能看到浏览器
                    
                    # 验证是否登录成功（检查是否有搜索框或其他登录后的元素）
                    logger.info("验证登录状态...")
                    try:
                        page.get_by_role("textbox", name="搜索小红书").wait_for(timeout=15000)
                        logger.info("登录成功，找到搜索框")
                    except Exception as e:
                        logger.warning(f"未找到搜索框: {str(e)}")
                        # 如果找不到搜索框，尝试其他方式验证
                        page.wait_for_timeout(5000)
                    
                    logger.info("获取Cookies...")
                    # 获取所有cookies
                    cookies = context.cookies()
                    logger.info(f"获取到 {len(cookies)} 个Cookie")
                    
                    # 转换为JSON格式
                    cookie_dict = {}
                    for cookie in cookies:
                        cookie_dict[cookie['name']] = cookie['value']
                    
                    cookie_json = json.dumps(cookie_dict, ensure_ascii=False)
                    
                    logger.info("关闭浏览器...")
                    browser.close()
                    
                    logger.info("Cookie获取成功")
                    return {
                        'success': True,
                        'cookie_json': cookie_json,
                        'message': 'Cookie获取成功'
                    }
                    
                except PlaywrightTimeoutError as e:
                    logger.error(f"操作超时: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    browser.close()
                    return {
                        'success': False,
                        'cookie_json': None,
                        'message': f'操作超时: {str(e)}'
                    }
                except Exception as e:
                    logger.error(f"获取Cookie失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    browser.close()
                    return {
                        'success': False,
                        'cookie_json': None,
                        'message': f'获取Cookie失败: {str(e)}'
                    }
                    
        except Exception as e:
            logger.error(f"Playwright执行失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'cookie_json': None,
                'message': f'Playwright执行失败: {str(e)}'
            }
    
    def fetch_cookie(self, platform, account, login_method=None, verification_code=None, password=None):
        """
        通用Cookie获取方法
        
        Args:
            platform: 平台名称
            account: 账号
            login_method: 登录方式（password/sms）
            verification_code: 验证码
            password: 密码
        
        Returns:
            dict: 包含cookie_json和成功状态
        """
        if platform == 'xiaohongshu':
            return self.fetch_xiaohongshu_cookie(account, verification_code, password)
        else:
            return {
                'success': False,
                'cookie_json': None,
                'message': f'暂不支持平台: {platform}'
            }

