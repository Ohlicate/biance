import asyncio
from api.log import logger
import uuid
from config import API_KEY, API_SECRET, sign_request_order
import time
import json


async def ws_order(ws, Bitcoin: dict, order_queue):
	logger.info("[order WS] 启动成功，等待接受信息")
	while True:
		try:
			order_type = await asyncio.wait_for(order_queue.get(), timeout=180)
			params = {
				"symbol": Bitcoin['symbol'],
				"side": "BUY",
				"type": "MARKET",
				"quantity": 0,
				"apiKey": API_KEY,
				"reduceOnly": "false",
				"timestamp": int(time.time() * 1000),
			}
			if order_type == "下单":
				logger.info("准备首次下单")
				params['quantity'] = Bitcoin['min_qty']
			elif order_type == "追加":
				logger.info("准备追加下单")
				params['quantity'] = Bitcoin['qty']
			elif order_type == "平仓":
				logger.info("准备全部平仓")
				params['side'] = "SELL"
				params['reduceOnly'] = "true"
				params['quantity'] = Bitcoin['Sell_sz']
			
			parms = {
				"id": str(uuid.uuid4()),
				"method": "order.place",
				"params": {
					**params
				}
			}
			parms['params']['signature'] = sign_request_order(parms['params'])
			
			msg = f"下单类型:{order_type} 下单信息:{parms}"
			logger.info(msg)
			await ws.send(json.dumps(parms))
			try:
				response = await ws.recv()
				data = json.loads(response)
				if data.get("status") == 200 and data.get("result"):
					if order_type != "平仓":
						logger.info(f"✅ 下单成功: {data}")
						Bitcoin['Sell_sz'] += float(params['quantity'])
					else:
						logger.info(f"✅ 平仓成功: {data}")
				else:
					logger.info(f"❌ 下单失败: {data}")
			except Exception as e:
				logger.error(f"❌ 等待下单响应失败: {e}")
		except asyncio.TimeoutError:
			logger.info("🐕[order_ws] 准备销毁")
			await ws.close()
			break
		except Exception as e:
			logger.info(f"[order_ws] 异常: {e}")
			break
