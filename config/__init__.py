import requests
import hmac
import hashlib

API_KEY = 'x'
API_SECRET = 'x'
BASE_URL = "https://fapi.binance.com"
headers = {"X-MBX-APIKEY": API_KEY}
WS_URL = "wss://fstream.binance.com/private/ws/"
order_ws_url = "wss://ws-fapi.binance.com/ws-fapi/v1"

# 常量
Funding_rate = -0.001  # 资金费限制
leverage = 10  # 倍数
divisions = 6  # 拆分次数
Buy_USDT = 5  # 总共购买金额

# 获取 listenKey
def get_listen_key():
	url = f"{BASE_URL}/fapi/v1/listenKey"
	res = requests.post(url, headers=headers)
	data = res.json()
	return data["listenKey"]


# === 签名 ===
def sign_request(params: dict) -> str:
	query = '&'.join([f"{k}={v}" for k, v in params.items()])
	return hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()


def sign_request_order(params: dict) -> str:
    # 不把 signature 本身参与签名
    params = {k: v for k, v in params.items() if k != "signature"}

    # 按 key 排序
    query = '&'.join(f"{k}={params[k]}" for k in sorted(params))

    return hmac.new(
        API_SECRET.encode('utf-8'),
        query.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()