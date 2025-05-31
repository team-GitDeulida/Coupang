import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
from dotenv import load_dotenv
import os

load_dotenv()

REQUEST_METHOD = "POST"
DOMAIN = "https://api-gateway.coupang.com"

# Replace with your own ACCESS_KEY and SECRET_KEY
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# 보안을 위해 쿠팡 API에 보낼 인증 서명(Authorization 헤더)를 만드는 함수이다.
def generateHmac(method, url, secretKey, accessKey):
    method = method.upper()  # << 여기를 추가하세요
    path, *query = url.split("?")

    # 현재 GMT 시간 생성 ex) 250527T034201Z
    datetimeGMT = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'

    # 요청 메시지 생성
    message = datetimeGMT + method + path + (query[0] if query else "")

    # HMAC SHA256으로 서명
    signature = hmac.new(bytes(secretKey, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    # 최종 Authorization 헤더 문자열 생성
    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(accessKey, datetimeGMT, signature)

# 딥링크 생성 함수
def create_deeplink(coupang_urls: list[str]) -> dict:
    DEEPLINK_URL = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    url = f"{DOMAIN}{DEEPLINK_URL}"
    headers = {
        "Authorization": generateHmac(REQUEST_METHOD, DEEPLINK_URL, SECRET_KEY, ACCESS_KEY),
        "Content-Type": "application/json"
    }
    body = {
        "coupangUrls": coupang_urls
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))
    return response.json()

if __name__ == "__main__":

    # ex) 사용자가 링크를 장바구니에 담았다고 가정
    test_urls = [
        # 제로콜라 
        "https://www.coupang.com/vp/products/7735518590?itemId=20797927043&vendorItemId=87867153243&q=펩시+콜라+제로슈가+라임향%2C+355ml%2C+24개&itemsCount=36&searchId=f188f05d3277220&rank=0&searchRank=0&isAddedCart=",
    ]

    # 딥링크 만들기
    result = create_deeplink(test_urls)
    product_keyword = None
    if result.get("rCode") == "0":
        print("✅ 딥링크 생성 성공!\n")
        for item in result["data"]:
            print("🛒 원래 URL:")
            print(item["originalUrl"])
            print("\n✅ 짧은 딥링크 -> 여기서 사용자가 구매시 수익 발생(shortenUrl):")
            print(item["shortenUrl"])
            print("\n" + "-"*60 + "\n")
    else:
        print(f"❌ 오류 발생: {result.get('rMessage')}")

