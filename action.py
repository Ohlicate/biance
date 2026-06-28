import asyncio
import time
from api import check, create_websocket, get_sysbol, order
from api.log import logger
import config


# === 币种获取检测 ===#
async def rate_refesh(Bitcoin: dict):
	await get_sysbol(Bitcoin)
	logger.info(f"📈{Bitcoin}")
	while True:
		await asyncio.sleep(60)
		if time.localtime().tm_min == 58:
			await get_sysbol(Bitcoin)
			logger.info(f"📈{Bitcoin}")


async def run():
	# === 判断变量 === #
	order_queue = asyncio.Queue()
	check_future = asyncio.Future()
	
	Bitcoin = {
		"symbol": "BTCUSDT",
		"lastFundingRate": "0.00000000",
		"nextFundingTime": 1782025200000,
		"FUNDING_FEE": False,
		"Sell_sz": 0
	}
	#  启动获取合适的资金费交易对任务
	asyncio.create_task(rate_refesh(Bitcoin))
	
	while True:
		# 当前时间
		now_ms = int(time.time() * 1000)
		# 目标时间戳的前8秒
		target_ms = Bitcoin['nextFundingTime'] - 8000
		# 计算倒计时
		# 测试区域
		# asyncio.create_task(check.ws_postion(ws=await create_websocket(config.WS_URL + config.get_listen_key(), "positions"), check_future=check_future, Bitcoin=Bitcoin))
		# asyncio.create_task(order.ws_order(ws=await create_websocket(config.order_ws_url, "order"), Bitcoin=Bitcoin, order_queue=order_queue))
		# await asyncio.sleep(5)
		# await order_queue.put("下单")
		# 测试区域
		diff_ms = target_ms - now_ms
		if 0 < diff_ms < 10000:
			# 变量回归初始化
			Bitcoin['FUNDING_FEE'] = False
			Bitcoin['Sell_sz'] = 0
			# 开启资金费检测任务
			asyncio.create_task(check.ws_postion(ws=await create_websocket(config.WS_URL + config.get_listen_key(), "positions"), check_future=check_future, Bitcoin=Bitcoin))
			# 开启WS下单任务
			asyncio.create_task(order.ws_order(ws=await create_websocket(config.order_ws_url, "order"), Bitcoin=Bitcoin, order_queue=order_queue))
			# 进行倒计时下单
			for i in range(config.divisions + 1):
				now_ms = int(time.time() * 1000)
				order_diff_ms = Bitcoin['nextFundingTime'] + (i * 1000) - now_ms
				await asyncio.sleep(order_diff_ms / 1000)
				if i == 0 and not Bitcoin['FUNDING_FEE']:
					await order_queue.put("下单")
				elif i in (1, 2, 3, 4, 5) and not Bitcoin['FUNDING_FEE']:
					await order_queue.put("追加")
				elif i == 6 or Bitcoin['FUNDING_FEE']:
					await order_queue.put("平仓")
					break
			
			await asyncio.sleep(20)
			logger.info("√本次套利完成，等待下一次")
		# now_ms = int(time.time() * 1000)
		# diff_ms1 = Bitcoin['funding_time'] - now_ms
		# await asyncio.sleep(diff_ms1 / 1000)
		# 下单触发
		
		else:
			await asyncio.sleep(1)
