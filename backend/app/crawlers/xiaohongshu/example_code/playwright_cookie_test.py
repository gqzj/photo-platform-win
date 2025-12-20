import re
from playwright.sync_api import Playwright, sync_playwright, expect

import csv
log_path = 'pailide.csv'

# open log file
file = open(log_path, 'a+', encoding='utf-8', newline='')
csv_writer = csv.writer(file)

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.xiaohongshu.com/explore")
    page.get_by_role("textbox", name="+").click()
    page.get_by_role("textbox", name="+").fill("17610240619")
    # page.get_by_placeholder("输入手机号").click()
    # page.get_by_placeholder("输入手机号").fill("17610240619")

    page.locator(".icon-wrapper").first.click()

    page.get_by_role("spinbutton", name="获取验证码").fill("196908")
    page.locator("form").get_by_role("button", name="登录").click()

    page.wait_for_timeout(5000)
    page.get_by_role("textbox", name="搜索小红书").click()
    context.storage_state(path="state.json")  # 保存状态

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)