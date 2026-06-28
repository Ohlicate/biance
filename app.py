import asyncio
from action import run as runs


async def run():
	await asyncio.gather(runs())


if __name__ == '__main__':
	asyncio.run(run())
