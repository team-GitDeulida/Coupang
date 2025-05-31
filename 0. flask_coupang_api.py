# # https://nurilab.github.io/2020/04/19/we_do_swagger/
# # https://tailerbox.tistory.com/53
from flask import Flask, request, jsonify
from flasgger import Swagger
import hmac
import hashlib
import requests
import json
from time import gmtime, strftime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
swagger = Swagger(app)

REQUEST_METHOD = "POST"
DOMAIN = "https://api-gateway.coupang.com"
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# -----------------------------------------------------
# api
# -----------------------------------------------------
def generateHmac(method, url, secretKey, accessKey):
    method = method.upper()
    path, *query = url.split("?")
    datetimeGMT = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetimeGMT + method + path + (query[0] if query else "")
    signature = hmac.new(bytes(secretKey, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()
    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(
        accessKey, datetimeGMT, signature)

@app.route('/create-deeplink', methods=['POST'])
def create_deeplink():
    """
    쿠팡 딥링크 생성 API
    ---
    parameters:
      - name: coupangUrls
        in: body
        type: array
        required: true
        schema:
          type: object
          properties:
            coupangUrls:
              type: array
              items:
                type: string
              description: 쿠팡 상품 URL 목록
          example:
            coupangUrls:
              - "https://www.coupang.com/vp/products/7735518590?itemId=20797927043"
    responses:
      200:
        description: 딥링크 생성 결과
        examples:
          application/json: {
            "result": [
                {"originalUrl": "https://www.coupang.com/...", "shortenUrl": "https://link.coupang.com/a/xxxx"}
            ]
          }
    """
    data = request.get_json()
    coupang_urls = data.get("coupangUrls", [])
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
    result = response.json()
    # 성공시 딥링크 리스트만 추출해서 반환 (예시)
    if result.get("rCode") == "0":
        links = [
            {
                "originalUrl": item["originalUrl"],
                "shortenUrl": item["shortenUrl"]
            }
            for item in result["data"]
        ]
        return jsonify({"result": links})
    else:
        return jsonify({"error": result.get("rMessage", "API Error")}), 400
    
@app.route('/best-products', methods=['GET'])
def best_products():
    """
    쿠팡 베스트 카테고리 상품 조회 API
    ---
    parameters:
      - name: categoryId
        in: query
        type: string
        required: true
        description: "카테고리 ID (예: 1012)"
      - name: limit
        in: query
        type: integer
        required: false
        description: "조회 개수(기본: 10, 최대: 100)"
    responses:
      200:
        description: 카테고리별 베스트 상품 리스트
    """
    category_id = request.args.get("categoryId")
    limit = request.args.get("limit", 10)
    if not category_id:
        return jsonify({"error": "categoryId 쿼리 파라미터를 입력하세요."}), 400

    url_path = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/bestcategories/{category_id}?limit={limit}"
    url = f"{DOMAIN}{url_path}"
    headers = {
        "Authorization": generateHmac("GET", url_path, SECRET_KEY, ACCESS_KEY),
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    result = response.json()
    if "data" in result:
        products = [
            {
                "productName": item.get("productName"),
                "productPrice": item.get("productPrice"),
                "categoryName": item.get("categoryName"),
                "isRocket": item.get("isRocket"),
                "isFreeShipping": item.get("isFreeShipping"),
                "productUrl": item.get("productUrl"),
                "productImage": item.get("productImage"),
            }
            for item in result["data"]
        ]
        return jsonify({"result": products})
    else:
        return jsonify(result), 400


# ★ Swagger UI 하단 Powered by 문구/로고 숨기기 ★
# @app.after_request
# def remove_swagger_footer(response):
#     if request.path.startswith("/apidocs"):
#         content = response.get_data(as_text=True)
#         hide_powered_css = """
#         <style>
#         .swagger-ui .footer, .swagger-ui .topbar-wrapper img[alt="Swagger UI"], .swagger-ui .topbar {display:none!important;}
#         .swagger-ui .wrapper .footer {display:none!important;}
#         </style>
#         """
#         if "</body>" in content:
#             content = content.replace("</body>", f"{hide_powered_css}</body>")
#             response.set_data(content)
#     return response

if __name__ == "__main__":
    app.run(debug=True)
