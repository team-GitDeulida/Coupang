# 쿠팡의 베스트 카테고리 상품 정보를 가져오는 코드
import hmac
import hashlib
import requests
import os
from time import gmtime, strftime
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

REQUEST_METHOD = "GET"
DOMAIN = "https://api-gateway.coupang.com"
# 카테고리 ID는 쿠팡 API 문서에서 확인할 수 있다.
CATEGORY_ID = "1012"

# 쿠팡의 베스트 카테고리 상품 정보를 가져오는 URL
URL = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/bestcategories/{CATEGORY_ID}?limit=100"


def generateHmac(method, url, secretKey, accessKey):
    path, *query = url.split("?")
    datetimeGMT = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetimeGMT + method + path + (query[0] if query else "")

    signature = hmac.new(bytes(secretKey, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(accessKey, datetimeGMT, signature)


authorization = generateHmac(REQUEST_METHOD, URL, SECRET_KEY, ACCESS_KEY)
url = f"{DOMAIN}{URL}"
response = requests.request(method=REQUEST_METHOD, url=url,
                            headers={
                                "Authorization": authorization,
                                "Content-Type": "application/json"
                            }
                            )

result = response.json()

if "data" in result:
    for item in result["data"]:
        print(f"상품명: {item.get('productName')}")
        print(f"가격: {item.get('productPrice')}원")
        print(f"카테고리: {item.get('categoryName')}")
        print(f"로켓배송: {'O' if item.get('isRocket') else 'X'}")
        print(f"무료배송: {'O' if item.get('isFreeShipping') else 'X'}")
        print(f"상품 링크: {item.get('productUrl')}")
        print(f"이미지: {item.get('productImage')}")
        print("-" * 40)
else:
    print(result)