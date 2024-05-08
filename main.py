from XiudongTicket.XiuDLogin import XiuDongLogin
from XiudongTicket.XiuD import XiuDong
import os
import json

if __name__ == "__main__":
    XD_browser = XiuDongLogin()
    if os.path.exists("./local_storage.json"):
        local_storage = json.load(open("./local_storage.json", "r", encoding="utf-8"))
        for k, v in local_storage.items():
            XD_browser.set_localStorage(k, v)
    XD_browser.open_login_page()
    local_storage = XD_browser.get_localStorage()
    with open("./local_storage.json", "w", encoding="utf-8") as f:
        json.dump(local_storage, f, ensure_ascii=False, indent=4)
    # XD_browser.page.quit()
    XD_session = XiuDong(local_storage)
    XD_session.refresh_token()
    search_result = XD_session.search_activity("fall")
    if search_result.get("activityInfo"):
        print(f'共搜索到{len(search_result["activityInfo"])}场演出\n')
        for act in search_result["activityInfo"]:
            print(f"演出名称：{act['title']}")
            print(f"演出ID：{act['activityId']}")
            print(f"演出城市：{act['city']}")
            print(f"演出时间：{act['showTime']}")
            print(f"演出价格：{act['activityPrice']}\n")
        ticket_list = XD_session.get_tickets_info_list("223943")[0]["ticketList"]
        for ticket in ticket_list:
            print(f"票种：{ticket['ticketType']}")
            print(f"票价：{ticket['sellingPrice']}")
            print(f"票ID：{ticket['ticketId']}")
            print(f"票种提示：{ticket['confirmPreOrderDetailTips']}\n")

        chosen_ticket = ticket_list[0]
        confirm_result = XD_session.confirm_order_info(
            "223943", chosen_ticket["ticketId"]
        )
        XD_session.submit_order_info(confirm_result)
