import asyncio
from api.log import logger
import json


async def ws_postion(ws, check_future, Bitcoin: dict):
	logger.info("[positions WS] 等待接受信息")
	first = False
	while True:
		try:
			data = await asyncio.wait_for(ws.recv(), timeout=180)
			logger.info(data)
			message = json.loads(data)
			if not first:
				if message.get('e') == "TRADE_LITE" and message.get('s') == Bitcoin['symbol']:
					Bitcoin['start_price'] = float(message.get('L'))
					logger.info(f"获取到开仓价格：{Bitcoin['start_price']}")
					first = True
			if message.get('e') == "ACCOUNT_UPDATE" and message.get('a')['m'] == "FUNDING_FEE":
				logger.info(f"获取到资金费")
				Bitcoin['FUNDING_FEE'] = True
		except asyncio.TimeoutError:
			logger.info("🐕[potions_ws] 接受超时")
		except Exception as e:
			logger.info(f"[positions WS] 异常: {e}")
			break
