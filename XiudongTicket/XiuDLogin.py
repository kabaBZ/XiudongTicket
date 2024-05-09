# from DrissionPage import ChromiumOptions
# import json
import time

from DrissionPage import WebPage

# path = r"D:\Chrome\Chrome.exe"  # 请改为你电脑内Chrome可执行文件路径
# co = ChromiumOptions().set_browser_path(path)
# page = WebPage(co)


class XiuDongLogin(object):
    def __init__(self):
        self.page = WebPage()

    def check_login(self):
        login_status = self.page.ele("tag:uni-view@@text():退出登录", timeout=60)
        time.sleep(1)
        # 跳过设备下线
        login_status = self.page.ele("tag:uni-view@@text():退出登录", timeout=120)
        return login_status

    def open_login_page(self):
        # url = "https://wap.showstart.com/pages/passport/login/login?redirect=%2Fpages%2FmyHome%2FmyHome"
        # if cache:
        url = "https://wap.showstart.com/pages/myHome/myHome"
        self.page.get(url)
        login_status = self.check_login()
        if not login_status:
            raise Exception("请在两分钟内登录")

    def click_pay(self):
        self.page.ele("tag:uni-view@@class:payBtn", timeout=120).click()
        self.page.ele("tag:uni-view@@class:wxpay", timeout=120).click()

    def get_localStorage(self):
        return self.page.local_storage()

    def set_localStorage(self, k, v):
        self.page.set.local_storage(k, v)
