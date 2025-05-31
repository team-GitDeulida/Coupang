import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

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


# 키워드 검색 함수
def search_products_by_keyword(keyword: str, limit: int = 5) -> dict:
    SEARCH_PATH = "/v2/providers/affiliate_open_api/apis/openapi/products/search"
    encoded_keyword = quote_plus(keyword)
    query = f"?keyword={encoded_keyword}&limit={limit}"
    
    signed_url = f"{SEARCH_PATH}{query}"
    full_url = f"{DOMAIN}{signed_url}"

    headers = {
        "Authorization": generateHmac("GET", signed_url, SECRET_KEY, ACCESS_KEY),
        "Content-Type": "application/json"
    }

    response = requests.get(full_url, headers=headers)
    return response.json()

if __name__ == "__main__":
    product_keyword = "제로콜라"
    result = search_products_by_keyword(product_keyword, limit=1)

    products = result.get("data", {}).get("productData", [])
    for product in products:
        print("🛒 상품명:", product.get("productName"))
        print("💰 가격:", f"{product.get('productPrice'):,}원")
        print("📦 로켓배송:", product.get("isRocket"))
        print("🔗 추적 링크:", product.get("productUrl"))
        print("🖼️ 이미지:", product.get("productImage"))
        print("\n" + "-" * 50 + "\n")