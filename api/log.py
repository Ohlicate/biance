import logging
import os

# 确保 logs 目录存在
os.makedirs("logs", exist_ok=True)

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='【%(asctime)s.%(msecs)03d】 %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('./logs/action.txt', encoding='utf-8'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

logger = logging.getLogger()