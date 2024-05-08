import json

import execjs
import requests


class XiuDong(object):
    def __init__(self, local_storage) -> None:
        self.js_ctx = self.init_js_ctx()
        self.local_storage = local_storage

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

    def submit_order_info(self, confirmed_info, ticketNum="1"):
        orderInfoVo = confirmed_info["orderInfoVo"]
        ticketPriceVo = orderInfoVo["ticketPriceVo"]
        data = {
            "orderDetails": [
                {
                    "goodsType": "",
                    "skuType": "",
                    "num": ticketNum,
                    "goodsId": orderInfoVo["activityId"],
                    # "skuId": ticketInfo["ticketId"],
                    "price": ticketPriceVo["price"],
                    "goodsPhoto": "",
                    "dyPOIType": ticketPriceVo["dyPOIType"],
                    "goodsName": orderInfoVo["title"],
                }
            ],
            "commonPerfomerIds": [29373316],
            "areaCode": "86_CN",
            "telephone": orderInfoVo["telephone"],
            "addressId": "",
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
        # data = '{"orderDetails":[{"goodsType":1,"skuType":1,"num":"1","goodsId":223943,"skuId":"f9e458dd33807bc3585a4698c6f45bf8","price":588,"goodsPhoto":"https://s2.showstart.com/img/2024/0326/18/30/54ee0b02bd5443a4968ee60f6589fab9_1200_1600_3466723.0x0.png","dyPOIType":2,"goodsName":"【广州】Fall Out Boy演唱会2024-fall out boy打倒男孩/翻闹小子"}],"commonPerfomerIds":[29373316],"areaCode":"86_CN","telephone":"18100176721","addressId":"","teamId":"","couponId":"","checkCode":"","source":0,"discount":0,"sessionId":3210594,"freight":0,"amountPayable":"588.00","totalAmount":"588.00","partner":"","orderSource":1,"videoId":"","payVideotype":"","st_flpv":"9y1xOb97fNN1Me31fav0","sign":"a381a6d8b258d3fc159b01d130c0b63a","trackPath":""}'
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
        # encrypted_data = self.js_ctx.call("data_encrypt", key, data)

        # self.js_ctx.call("data_decrypt", key, encrypted_data)
        res = self.postRequest(
            "/nj/order/order",
            {
                "q": encrypted_data,
            },
            ctraceid,
            data["st_flpv"],
            data["sign"],
            # self.local_storage["st_flpv"],
            # self.local_storage["sign"],
        )
        search_result = res.json()
        if search_result.get("status") == 200:
            return search_result["result"]
        return search_result
