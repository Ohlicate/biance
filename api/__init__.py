import aiohttp
from config import API_SECRET, headers, BASE_URL, Funding_rate, sign_request, leverage, Buy_USDT, divisions
import time
import asyncio
import websockets
from api.log import logger
from decimal import Decimal, ROUND_DOWN


# 创建WS函数
async def create_websocket(url, name=None, retry_interval=1, max_retries=3):
	"""
	创建 WebSocket 并带重连机制
	:param url: WebSocket 地址
	:param name: 通道名称，用于日志
	:param retry_interval: 重连间隔秒
	:param max_retries: 最大重连次数，None 表示无限重连
	:return: WebSocket 对象
	"""
	attempt = 0
	while True:
		try:
			ws = await asyncio.wait_for(websockets.connect(url), timeout=1)
			logger.info(f"✅ WebSocket {name}通道已连接")
			return ws
		except asyncio.TimeoutError:
			logger.info(f"❌ WebSocket {name}通道连接超时")
		except Exception as e:
			logger.info(f"❌ {name}连接失败，错误信息: {e}")
		
		attempt += 1
		if max_retries is not None and attempt >= max_retries:
			logger.info(f"❌ WebSocket {name}已达到最大重连次数 {max_retries}，停止重连")
			exit()
			return None
		
		logger.info(f"⏳ {name}将在 {retry_interval}s 后重连… (第 {attempt} 次尝试)")
		await asyncio.sleep(retry_interval)


#  === 获取交易对 ===
async def get_sysbol(Bitcoin: dict):
	url = BASE_URL + "/fapi/v1/premiumIndex"
	async with aiohttp.ClientSession() as session:
		async with session.get(url=url) as response:
			data = await response.json()
			current_time = int(time.time() * 1000)
			one_hour = 3600 * 1000  # 一小时的毫秒数
			#  筛选下一个小时内结算的
			next_hour_data = [item for item in data if item['nextFundingTime'] - current_time <= one_hour and item['estimatedSettlePrice'] != "0.00000000"]
			#  排序从小到大 (从负到正)
			sorted_data = sorted(next_hour_data, key=lambda x: float(x['lastFundingRate']))
			for sorted_datas in sorted_data:
				res = sorted_datas
				if float(res['lastFundingRate']) * 100 < Funding_rate:
					Bitcoin['symbol'] = res['symbol']
					Bitcoin['lastFundingRate'] = float(res['lastFundingRate']) * 100
					Bitcoin['nextFundingTime'] = res['nextFundingTime']
					Bitcoin['markPrice'] = Decimal(res['markPrice'])
					Bitcoin['min_qty'] = await get_qty(session, Bitcoin, 1 * leverage, first=True)
					Bitcoin['qty'] = await get_qty(session, Bitcoin, int(Buy_USDT / divisions * leverage))
					await set_marginType(session, symbol=Bitcoin['symbol'])
					res = await set_level(session, symbol=Bitcoin['symbol'], leverage=leverage)
					if res:
						return
				else:
					Bitcoin_init(Bitcoin)


# === 交易对初始化 ===
def Bitcoin_init(Bitcoin: dict):
	Bitcoin['symbol'] = "BTCUSDT"
	Bitcoin['lastFundingRate'] = "0.00000000"
	Bitcoin['nextFundingTime'] = 1782025200000
	Bitcoin['markPrice'] = "0.0000"


async def set_level(session, symbol: str, leverage: int):
	logger.info("开始设置倍数")
	url = f"{BASE_URL}/fapi/v1/leverage"
	timestamp = int(time.time() * 1000)
	params = {
		"symbol": symbol,  # 杠杆倍数
		"leverage": leverage,  # 当前杠杆倍数下允许的最大名义价值
		"timestamp": timestamp  # 交易对
		
	}
	# 构造签名
	params['signature'] = sign_request(params)
	async with session.post(url=url, headers=headers, params=params) as response:
		code = response.status
		if code == 200:
			logger.info(f"设置完毕:{params['symbol']},倍数:{params['leverage']}")
			return True
		else:
			logger.info(f"设置错误{params['symbol']},倍数:{params['leverage']}")
			return False


async def set_marginType(session, symbol: str):
	logger.info("开始设置持仓模式")
	url = f"{BASE_URL}/fapi/v1/marginType"
	timestamp = int(time.time() * 1000)
	params = {
		"symbol": symbol,  # 杠杆倍数
		"marginType": "ISOLATED",  # 逐仓模式
		"timestamp": timestamp  # 交易对
		
	}
	# 构造签名
	params['signature'] = sign_request(params)
	async with session.post(url=url, headers=headers, params=params) as response:
		code = response.status
		text = await response.json()
		if code == 200:
			logger.info(f"设置持仓模式完毕:{params['symbol']},持仓模式:逐仓模式")
		elif text['code'] == -4046:
			logger.info(f"已设置{params['symbol']},持仓模式:逐仓模式")
		else:
			logger.info(f"设置持仓模式失败{params['symbol']},持仓模式:逐仓模式{text}")


async def get_qty(session, Bitcoin: dict, USDT: int, first: bool = False):
	logger.info("开始获取购买数量")
	url = f"{BASE_URL}/fapi/v1/exchangeInfo"
	async with session.get(url=url) as response:
		result = await response.json()
		for item in result['symbols']:
			if item['symbol'] == Bitcoin['symbol']:
				minQty = Decimal(item['filters'][1]['minQty'])
				if first:
					if float(Bitcoin['markPrice']) >= 5:
						raw_qty = minQty
						num = raw_qty
					else:
						raw_qty = Decimal("6") / Decimal(Bitcoin['markPirce'])
						num = (raw_qty // minQty) * minQty
				else:
					raw_qty = Decimal(str(USDT)) / Decimal(Bitcoin['markPrice'])
					num = (raw_qty // minQty) * minQty
				logger.info(f"购买金额:{USDT}购买数量：{num}")
				return str(num)
