import hmac
import hashlib
import requests
from bs4 import BeautifulSoup
import json
from time import gmtime, strftime
from dotenv import load_dotenv
import os
import pprint # pprint.pprint(response.json())
from urllib.parse import quote_plus
from urllib.parse import urlparse, parse_qs

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

# 링크에서 파라미터 꺼내기
def extract_info_from_url(url: str) -> dict:
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    product_id = parsed_url.path.split("/products/")[1].split("?")[0]

    return {
        "productId": product_id,
        "itemId": query_params.get("itemId", [None])[0],
        "vendorItemId": query_params.get("vendorItemId", [None])[0],
        "keyword": query_params.get("q", [None])[0]
    }

# 상세페이지에서 제목 크롤링하여 리턴하기 선택자: .prod-buy-header__title
def crawl_product_title(detail_url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        response = requests.get(detail_url, headers=headers, timeout=5)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        title_tag = soup.select_one(".prod-buy-header__title")

        if title_tag:
            return title_tag.text.strip()
        else:
            return "❌ 제목을 찾을 수 없습니다"
    except Exception as e:
        return f"❌ 크롤링 실패: {e}"

def extract_product_id(url: str) -> str:
    """
    주어진 쿠팡 상품 URL에서 productId(상품 ID)만 추출해서 반환하는 함수.
    예: https://www.coupang.com/vp/products/123456789?itemId=xxx
        -> "123456789" 반환

    Args:
        url (str): 상품 상세 페이지 URL

    Returns:
        str: 추출한 productId 문자열
    """
    parsed_url = urlparse(url)
    return parsed_url.path.split("/products/")[1].split("?")[0]

def match_product_by_id(product_id: str, keyword: str, limit: int = 10):
    """
    쿠팡 키워드 검색 API를 이용해 해당 키워드로 상품을 조회하고,
    결과 중에서 product_id와 일치하는 상품 정보를 반환하는 함수.

    Args:
        product_id (str): 찾으려는 상품의 productId
        keyword (str): 검색할 키워드 (예: "제로콜라")
        limit (int, optional): 최대 검색 결과 수. 기본값은 10.

    Returns:
        dict or None: 일치하는 상품 정보 딕셔너리, 없으면 None 반환
    """
    result = search_products_by_keyword(keyword, limit=limit)
    products = result.get("data", {}).get("productData", [])

    for product in products:
        if str(product.get("productId")) == product_id:
            return product
    return None


