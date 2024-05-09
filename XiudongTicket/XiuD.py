import json
import os
import time
from configparser import ConfigParser

import execjs
import requests
from loguru import logger
from requests.exceptions import Timeout

requests.packages.urllib3.disable_warnings()

from XiudongTicket.XiuDLogin import XiuDongLogin

logger.add("Xiudong.log")


class XiuDong(object):
    def __init__(self) -> None:
        self.init_browser()
        if not os.path.exists("./settings.ini"):
            raise Exception("先修改配置文件！")
        self.conf = ConfigParser()
        self.conf.read("settings.ini", encoding="utf-8")
        self.js_ctx = self.init_js_ctx()

    def init_browser(self):
        self.XD_browser = XiuDongLogin()
        if os.path.exists("./local_storage.json"):
            local_storage = json.load(
                open("./local_storage.json", "r", encoding="utf-8")
            )
            for k, v in local_storage.items():
                self.XD_browser.set_localStorage(k, v)
        self.XD_browser.open_login_page()
        self.local_storage = self.XD_browser.get_localStorage()
        with open("./local_storage.json", "w", encoding="utf-8") as f:
            json.dump(local_storage, f, ensure_ascii=False, indent=4)

    def init_js_ctx(self):
        # 读取JavaScript文件内容
        with open("XiudongTicket/xiudong.js", "r", encoding="utf-8") as f:
            js_code = f.read()

        # 创建一个execjs上下文
        ctx = execjs.compile(js_code)
        return ctx

    def prepare_headers(
        self, url: str, data: dict, ctraceid=None, st_flpv=None, sign=None
    ):
        if data.get("st_flpv") is not None:
            data["st_flpv"] = self.local_storage.get(
                "st_flpv",
                self.js_ctx.call(
                    "create_st_flpv",
                ),
            )
        if data.get("sign") is not None:
            data["sign"] = self.local_storage.get("sign", "")
        if ctraceid is None:
            ctraceid = self.js_ctx.call(
                "create_crtraceid",
            )
        userid = str(json.loads(self.local_storage["userInfo"])["data"]["userId"])
        crpsign = self.js_ctx.call(
            "create_crpsign",
            self.local_storage.get("accessToken"),
            "",
            self.local_storage.get("token"),
            ctraceid,
            url,
            json.dumps(
                data,
                separators=(",", ":"),
            ),
            sign or self.local_storage.get("sign"),
            userid,
            self.local_storage.get("idToken"),
        )
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "no-cache",
            "cdeviceinfo": '{"vendorName":"","deviceMode":"Nexus 5","deviceName":"","systemName":"android","systemVersion":"6.0","cpuMode":" ","cpuCores":"","cpuArch":"","memerySize":"","diskSize":"","network":"UNKNOWN","resolution":"532*831","pixelResolution":""}',
            "cdeviceno": self.local_storage.get("token"),  # 猜测只与当前设备有关，一般不变，可以定死。
            "content-type": "application/json",
            "crtraceid": ctraceid,
            "crpsign": crpsign,  # generate_random_string(32) + 时间戳
            "csappid": "wap",
            "csourcepath": "",
            "cterminal": "wap",
            "ctrackpath": "",
            "cusat": self.local_storage.get(
                "accessToken", "nil"
            ),  # 由首次请求gettoken得到，此后一直不变。
            "cusid": userid,
            "cusit": self.local_storage.get(
                "idToken", "nil"
            ),  # 由二次请求gettoken得到（需要携带之前的sign参数），此后一直不变。
            "cusname": "nil",
            "cusut": sign or self.local_storage.get("sign", "nil"),
            "cuuserref": self.local_storage.get("token"),  # 猜测只与当前设备有关，一般不变，可以定死。
            "cversion": "997",
            "origin": "https://wap.showstart.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://wap.showstart.com/pages/passport/login/login?redirect=%2Fpages%2FmyHome%2FmyHome",
            "sec-ch-ua": '"Chromium";v="124", "Microsoft Edge";v="124", "Not-A.Brand";v="99"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "st_flpv": st_flpv
            or data.get(
                "st_flpv",
                self.js_ctx.call(
                    "create_st_flpv",
                ),
            ),  # generate_random_string(20)
            "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 Edg/124.0.0.0",
        }
        return headers

    def postRequest(self, url: str, data: dict, ctraceid=None, st_flpv=None, sign=None):
        headers = self.prepare_headers(url, data, ctraceid, st_flpv, sign)
        response = requests.request(
            "POST",
            "https://wap.showstart.com/v3" + url,
            data=json.dumps(data, separators=(",", ":")),
            headers=headers,
            verify=False,
        )
        return response

    def refresh_token(self):
        res = self.postRequest(
            "/waf/gettoken",
            {"st_flpv": "CwqO0nj0ol8H9xCsv5W8", "sign": "", "trackPath": ""},
        )
        self.local_storage["idToken"] = res.json()["result"]["idToken"]["id_token"]
        self.local_storage["accessToken"] = res.json()["result"]["accessToken"][
            "access_token"
        ]

    def search_activity(self, keyword: str):
        res = self.postRequest(
            "/wap/activity/list",
            {
                "pageNo": 1,
                "cityCode": "311",
                "keyword": keyword,
                "style": "",
                "activityIds": "",
                "couponCode": "",
                "performerId": "",
                "hosterId": "",
                "siteId": "",
                "tag": "",
                "tourId": "",
                "themeId": "",
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        search_result = res.json()
        if search_result.get("status") == 200:
            return search_result["result"]
        return search_result

    def get_tickets_info_list(self, activityId: str):
        res = self.postRequest(
            "/wap/activity/V2/ticket/list",
            {
                "activityId": activityId,
                "coupon": "",
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        search_result = res.json()
        if search_result.get("status") == 200:
            return search_result["result"]
        return search_result

    def confirm_order_info(self, activityId, ticketId, ticketNum="1"):
        res = self.postRequest(
            "/order/wap/order/confirm",
            {
                "sequence": activityId,
                "ticketId": ticketId,
                "ticketNum": ticketNum,
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        search_result = res.json()
        if search_result.get("status") == 200:
            return search_result["result"]
        return search_result

    def submit_order(self, confirmed_info, commonPerfomerIds, addressId, ticketNum="1"):
        orderInfoVo = confirmed_info["orderInfoVo"]
        ticketPriceVo = orderInfoVo["ticketPriceVo"]
        data = {
            "orderDetails": [
                {
                    "goodsType": 1,
                    "skuType": ticketPriceVo["ticketType"],
                    "num": ticketNum,
                    "goodsId": orderInfoVo["activityId"],
                    "skuId": ticketPriceVo["ticketId"],
                    "price": ticketPriceVo["price"],
                    "goodsPhoto": "",
                    "dyPOIType": ticketPriceVo["dyPOIType"],
                    "goodsName": orderInfoVo["title"],
                }
            ],
            "commonPerfomerIds": [commonPerfomerIds],
            "areaCode": "86_CN",
            "telephone": orderInfoVo["telephone"],
            "addressId": addressId,
            "teamId": "",
            "couponId": "",
            "checkCode": "",
            "source": 0,
            "discount": 0,
            "sessionId": orderInfoVo["sessionId"],
            "freight": 0,
            "amountPayable": str(ticketPriceVo["price"]),
            "totalAmount": str(ticketPriceVo["price"]),
            "partner": "",
            "orderSource": 1,
            "videoId": "",
            "payVideotype": "",
            "st_flpv": "",
            "sign": "",
            "trackPath": "",
        }
        if data.get("st_flpv") is not None:
            data["st_flpv"] = self.local_storage.get(
                "st_flpv",
                self.js_ctx.call(
                    "create_st_flpv",
                ),
            )
        if data.get("sign") is not None:
            data["sign"] = self.local_storage.get("sign", "")
        ctraceid = self.js_ctx.call(
            "create_crtraceid",
        )
        key = (
            self.js_ctx.call("create_key", self.local_storage.get("token"), ctraceid),
        )
        encrypted_data = self.js_ctx.call(
            "data_encrypt",
            key,
            json.dumps(data, separators=(",", ":"), ensure_ascii=False),
        )
        res = self.postRequest(
            "/nj/order/order",
            {
                "q": encrypted_data,
            },
            ctraceid,
            data["st_flpv"],
            data["sign"],
        )
        order_result = res.json()
        if order_result.get("success") is True:
            # 提交后等待一秒，否则后续查询响应一直为pending
            time.sleep(1)
            return order_result["result"]
        logger.warning(f"submit_order函数响应结果：{order_result}")
        if "超出限购策略" in order_result["msg"]:
            logger.success("已抢购成功")
            exit(0)
        return order_result

    def core_order(self, orderId):
        data = {
            "coreOrderKey": orderId,
            "st_flpv": "9y1xOb97fNN1Me31fav0",
            "sign": "bef492137311f6cc32e93e5dc8fcf963",
            "trackPath": "",
        }
        if data.get("st_flpv") is not None:
            data["st_flpv"] = self.local_storage.get(
                "st_flpv",
                self.js_ctx.call(
                    "create_st_flpv",
                ),
            )
        if data.get("sign") is not None:
            data["sign"] = self.local_storage.get("sign", "")
        ctraceid = self.js_ctx.call(
            "create_crtraceid",
        )
        key = (
            self.js_ctx.call("create_key", self.local_storage.get("token"), ctraceid),
        )
        encrypted_data = self.js_ctx.call(
            "data_encrypt",
            key,
            json.dumps(data, separators=(",", ":"), ensure_ascii=False),
        )
        res = self.postRequest(
            "/nj/order/coreOrder",
            {
                "q": encrypted_data,
            },
            ctraceid,
            data["st_flpv"],
            data["sign"],
        )
        order_result = res.json()
        if order_result.get("success") is True:
            return order_result["result"]
        logger.warning(f"core_order函数响应结果：{order_result}")
        return order_result

    def getOrderResult(self, orderId):
        data = {
            "orderJobKey": orderId,
            "st_flpv": "9y1xOb97fNN1Me31fav0",
            "sign": "bef492137311f6cc32e93e5dc8fcf963",
            "trackPath": "",
        }
        if data.get("st_flpv") is not None:
            data["st_flpv"] = self.local_storage.get(
                "st_flpv",
                self.js_ctx.call(
                    "create_st_flpv",
                ),
            )
        if data.get("sign") is not None:
            data["sign"] = self.local_storage.get("sign", "")
        ctraceid = self.js_ctx.call(
            "create_crtraceid",
        )
        key = (
            self.js_ctx.call("create_key", self.local_storage.get("token"), ctraceid),
        )
        encrypted_data = self.js_ctx.call(
            "data_encrypt",
            key,
            json.dumps(data, separators=(",", ":"), ensure_ascii=False),
        )
        res = self.postRequest(
            "/nj/order/getOrderResult",
            {
                "q": encrypted_data,
            },
            ctraceid,
            data["st_flpv"],
            data["sign"],
        )
        order_result = res.json()
        if order_result.get("success") is True:
            return order_result["result"]
        logger.warning(f"getOrderResult函数响应结果：{order_result}")
        return order_result

    def detail(self, orderId):
        res = self.postRequest(
            "/order/wap/order/detail",
            {
                "orderId": orderId,
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        detail_result = res.json()
        if detail_result.get("status") == 200:
            return detail_result["result"]
        logger.warning(f"detail函数响应结果：{detail_result}")
        return detail_result

    def order_list(self, page=1, size=10):
        res = self.postRequest(
            "/order/wap/order/list",
            {
                "history": 1,
                "pageNo": 1,
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        order_list_result = res.json()
        if order_list_result.get("status") == 200:
            return order_list_result["result"]
        logger.warning(f"order_list函数响应结果：{order_list_result}")
        return order_list_result

    def addr_list(self):
        res = self.postRequest(
            "/wap/address/list",
            {
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        addr_list_result = res.json()
        if addr_list_result.get("status") == 200 and addr_list_result["state"] == "1":
            return addr_list_result["result"]
        logger.warning(f"addr_list函数响应结果：{addr_list_result}")
        return []

    def id_list(self):
        res = self.postRequest(
            "/wap/cp/list",
            {
                "st_flpv": "",
                "sign": "",
                "ticketPriceId": "",
                "trackPath": "",
            },
        )
        id_list_result = res.json()
        if id_list_result.get("status") == 200:
            return id_list_result["result"]
        logger.warning(f"id_list函数响应结果：{id_list_result}")
        return []

    def add_addr(self):
        if not self.conf.has_section("addr_dict"):
            return ""
        addr_dict = self.conf["addr_dict"]
        logger.debug("地址信息:")
        for k, v in addr_dict.items():
            logger.debug(f"{k}:{v}")
        addr_data = {
            "consignee": addr_dict["consignee"],
            "id": "",
            "areaCode": "86_CN",
            "telephone": addr_dict["telephone"],
            "address": addr_dict["address"],
            "provinceCode": addr_dict.getint("provinceCode"),
            "cityCode": addr_dict.getint("cityCode"),
            "isDefault": 0,
            "postCode": "",
            "st_flpv": "",
            "sign": "",
            "trackPath": "",
        }
        res = self.postRequest(
            "/wap/address/add",
            addr_data,
        )
        add_addr_result = res.json()
        if add_addr_result.get("status") != 200 or add_addr_result["state"] != "1":
            logger.warning(f"add_addr函数响应结果：{add_addr_result}")
        addr_list = self.addr_list()
        for addr in addr_list:
            if addr["address"] == addr_dict["address"]:
                return addr["id"]
        else:
            return ""

    def add_id(self):
        id_dict = self.conf["id_dict"]
        id_list = self.id_list()
        for id in id_list:
            if id["name"] == id_dict["name"]:
                return id["id"]
        logger.debug(f'开始添加身份证信息：{id_dict["name"]}，{id_dict["documentNumber"]}')
        res = self.postRequest(
            "/wap/cp/addOrUp",
            {
                "id": "",
                "name": id_dict["name"],
                "documentType": 1,
                "documentNumber": id_dict["documentNumber"],
                "isSelf": 0,
                "st_flpv": "",
                "sign": "",
                "trackPath": "",
            },
        )
        add_id_result = res.json()
        if add_id_result.get("status") == 200 and add_id_result["state"] == "1":
            return json.loads(add_id_result["result"])["id"]
        logger.error(f"add_id函数响应结果：{add_id_result}")
        raise Exception(f"增加身份信息错误")

    def count_down(self, startTime):
        while int(time.time()) * 1000 < startTime:
            time.sleep(0.5)
            print(
                f"距抢购开始还有{startTime/1000 - int(time.time())}s",
                end="\r",
            )

    def run(self):
        self.refresh_token()
        # 取消搜索流程
        # search_result = self.search_activity("fall")
        # if search_result.get("activityInfo"):
        #     logger.info(f'共搜索到{len(search_result["activityInfo"])}场演出\n')
        #     for act in search_result["activityInfo"]:
        #         logger.info(f"演出名称：{act['title']}")
        #         logger.info(f"演出ID：{act['activityId']}")
        #         logger.info(f"演出城市：{act['city']}")
        #         logger.info(f"演出时间：{act['showTime']}")
        #         logger.info(f"演出价格：{act['activityPrice']}\n")
        activityId = self.conf["Ticket"].getint("activityId")
        if not activityId:
            activityId = input("请输入活动ID：")
        ticket_list = self.get_tickets_info_list(activityId)[0]["ticketList"]
        for ticket in ticket_list:
            logger.info(f"票序号：{ticket_list.index(ticket)}")
            logger.info(f"票种：{ticket['ticketType']}")
            logger.info(f"票价：{ticket['sellingPrice']}")
            logger.info(f"票ID：{ticket['ticketId']}")
            logger.info(f"票种提示：{ticket['confirmPreOrderDetailTips']}\n")

        index = input(
            "请输入需要抢购的票序号：",
        )

        # 增加身份证和地址信息
        commonPerfomerIds = self.add_id()
        addressId = self.add_addr()

        chosen_ticket = ticket_list[int(index)]
        confirm_result = self.confirm_order_info(activityId, chosen_ticket["ticketId"])

        self.count_down(chosen_ticket["startTime"])

        while True:
            try:
                submit_result = self.submit_order(
                    confirm_result, commonPerfomerIds, addressId
                )
                if not submit_result.get("orderJobKey"):
                    time.sleep(0.2)
                    continue

                order_info = self.core_order(submit_result["orderJobKey"])
                logger.debug(f"order_info响应：{order_info}")
                if not order_info.get("orderJobKey"):
                    time.sleep(0.2)
                    continue
                while True:
                    order_result = self.getOrderResult(submit_result["orderJobKey"])
                    if order_result == "pending":
                        time.sleep(1)
                        continue
                    logger.debug(f"getOrderResult成功：{order_result}")
                    break
                detail_result = self.detail(order_result["orderId"])
                logger.info(f"订单详情：{detail_result}")
                break
            except Timeout:
                logger.error("请求超时,继续抢票")
                continue
        # 触发缴款事件，就能在app中看到订单
        self.XD_browser.page.get(
            f'https://wap.showstart.com/pages/order/activity/detail/detail?orderId={detail_result["orderId"]}'
        )
        self.XD_browser.click_pay()
        self.XD_browser.page.quit()
        logger.success("抢票成功")
        exit(0)
