from datetime import datetime
from logging import getLogger, StreamHandler, Formatter, Logger, DEBUG, INFO, WARNING, ERROR, CRITICAL
from logging.handlers import RotatingFileHandler
import os

def get_logger(name: str):
    # logger = getLogger(os.path.basename(os.getcwd()))
    logger = getLogger(name)
    logger.setLevel(DEBUG)  # 全ログデータの記録するレベル(DEBUG以上など)
    logger.propagate = False

    s_handler = StreamHandler()
    s_handler.setLevel(DEBUG)
    logger.addHandler(s_handler)  # コンソールに出力するメッセージのレベル(INFO以上など)

    now_timestamp = datetime.now().strftime("%m%dT%H%M")
    tsv_format = Formatter('%(asctime)s.%(msecs)d+09:00\t%(name)s\t%(filename)s\t%(lineno)d\t%(funcName)s\t%(levelname)s\t%(message)s', '%Y-%m-%dT%H:%M:%S')
    os.makedirs('log', exist_ok=True)
    f_handler = RotatingFileHandler('/boot/firmware/sc26_log/sc26_' + now_timestamp + '.log', maxBytes=100*1000, encoding='utf-8')  # 最大で100kBまで記録
    f_handler.setLevel(DEBUG)  # ファイルに記録するメッセージのレベル(INFO以上など)
    f_handler.setFormatter(tsv_format)
    logger.addHandler(f_handler)
    return logger

if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.debug("これはデバッグ時専用のメッセージです")
    logger.info("これはINFOです")
    logger.warning("これは警告です")
    logger.error("これはエラーメッセージです")
    logger.critical("これは致命的なエラーメッセージです")
    try:
        1/0
    except Exception as e:
        logger.exception(f"なんかエラーが起きました")  # 👈except内はこれを使って

# from log import logger  でloggerを読み込んで
# logger.info("aiu")      のように記録してください