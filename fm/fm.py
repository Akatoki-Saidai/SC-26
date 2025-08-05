import copy
import os
from threading import Thread
from multiprocessing import Process, Value
import time

import pigpio

from bmp280 import BMP280
from bno055 import BNO055
from camera import Camera
from gnss import GNSS
from sg90 import SG90
import sc_logging
from motor import Motor
from speaker import Speaker
import start_gui
import shutil

logger = sc_logging.get_logger(__name__)

NICR_PIN = 10  # ニクロム線のGPIO番号

GOAL_LAT = 30.3741583  # ゴールの緯度(2025/03/08/08:27)
GOAL_LON = 130.960075  # ゴールの経度(2025/03/08/08:27)

# 各デバイスのセットアップ devices引数の中身を変更します
def setup(devices):
    try:
        # BMPをセットアップ
        devices["bmp"] = BMP280(logger=logger)

        # BNOをセットアップ
        devices["bno"] = BNO055(logger=logger)
        if not devices["bno"].begin():
            logger.critical('Failed to initialize BNO055! Is the sensor connected?')

        # GNSS (BE-180) をセットアップ
        devices["gnss"] = GNSS(logger=logger)

        # モーターをセットアップ
        devices["motor"] = Motor(right_pin1=20, right_pin2=21, left_pin1=5, left_pin2=7, logger=logger)

        # サーボモーターのセットアップ
        devices["servo"] = SG90(pin=26, min_angle=-90, max_angle=90, ini_angle=0, freq=50, logger=logger)

        # pigpioのセットアップ(omusubi0はpigpio自動有効化設定済)
        devices["pi"] = pigpio.pi()
        # NiCr線のセットアップ
        devices["pi"].set_mode(NICR_PIN, pigpio.OUTPUT)  # NiCrのピンを出力モードに設定
        devices["pi"].write(NICR_PIN, 0)  # NiCrをオフにしておく

        # スピーカーのセットアップ (ピンは19, 18)
        devices["speaker"] = Speaker(logger=logger)
        devices["speaker"].audio_play("Windows7_boot.wav")

        # LEDのセットアップ
        ## 基板にLEDをつけ忘れた...
    except Exception as e:
        logger.exception(f"An error occured in setup device: {e}")

# カメラの処理が重いので，カメラだけ完全に分離してセットアップ+撮影
def camera_setup_and_start(camera_order, show=False):
    try:
        camera = Camera(logger, show=show, save=True)  # セットアップ
        camera.start()  # 起動
        # カメラで画像認識し続ける
        camera_thread = Thread(target=camera.get_forever, args=(devices, camera_order, show,))
        camera_thread.start()

        # GUIに定期的に書き込む
        gui_thread = Thread(target=start_gui.write_to_gui, args=(devices, data,), kwargs={'logger': logger})
        gui_thread.start()
        
    except Exception as e:
        logger.exception(f"An error occured in setup and start camera: {e}")

# 待機フェーズ
def wait_phase(devices, data):
    try:
        logger.info("Entered wait phase")
        data["phase"] = "wait"
        # shutil.copy("./phase_pic/camera_wait.jpg", "./camera_wait_temp.jpg")
        # os.rename("./camera_wait_temp.jpg", "camera.jpg")

    except Exception as e:
        logger.exception(f"An error occured in Entering wait phase:{e}")
    
    # 高度が高くなるまで待つ
    while True:
        try:
            time.sleep(0.1)
            # ここに待機フェーズの処理を書いて
            #
            #
            #
        except Exception as e:
            logger.exception(f"An error occured in wait phase:{e}")

# 落下フェーズ
def fall_phase(devices, data):
    try:
        logger.info("Entered fall phase")
        data["phase"] = "fall"
        # shutil.copy("./phase_pic/camera_fall.jpg", "./camera_fall_temp.jpg")
        # os.rename("./camera_fall_temp.jpg", "camera.jpg")
        # devices["speaker"].audio_play("totsugeki_rappa.wav")
    except Exception as e:
        logger.exception(f"An error occured in Entering wait phase: {e}")
                         
    # 落下して静止するまで待つ
    while True:
        try:
            time.sleep(0.1)
            # ここに落下フェーズの処理を書いて
            #
            #
            #
        except Exception as e:
            logger.exception(f"An error occured in fall phase: {e}")

# 遠距離フェーズ
def long_phase(devices, data):
    try:
        logger.info("Entered long phase")
        data["phase"] = "long"
        # shutil.copy("./phase_pic/camera_long.jpg", "./camera_long_temp.jpg")
        # os.rename("./camera_long_temp.jpg", "camera.jpg")
        # devices["speaker"].audio_play("starwars.wav")
        long_start_time = time.time()

    except Exception as e:
        logger.exception(f"An error occured in Entering long phase: {e}")

    # 機体がひっくり返っていたら回る
    try:
        # ここに機体の向きを判定する処理を書く
        pass
    except Exception as e:
        logger.exception(f"An error occured in muki_hantai: {e}")
    
    # ゴールから離れている間，ゴールに向かって進む
    while True:
        try:
            time.sleep(0.1)
            # ここに長距離フェーズの処理を書いて
            #
            #
            #
        except Exception as e:
            logger.exception(f"An error occured in long phase approaching: {e}")

# 近距離フェーズ
def short_phase(devices, data, camera_order):
    try:
        logger.info("Entered short phase")
        data["phase"] = "short"        
        # shutil.copy("./phase_pic/camera_short.jpg", "./camera_short_temp.jpg")
        # os.rename("./camera_short_temp.jpg", "camera.jpg")
        # devices["speaker"].audio_play("Harry_Potter.wav")
    except Exception as e:
        logger.exception(f"An error occured in entering short phase: {e}")

    while True:
        try:
            time.sleep(0.1)
            # ここに近距離フェーズの処理を書いて
            #
            #
        except Exception as e:
            logger.exception(f"An error occured in short phase moving: {e}")


# ゴールフェーズ
def goal_phase(devices, data):
    try:
        logger.info("Entered goal phase")
        data["phase"] = "goal"
        # devices["speaker"].audio_play("GLaDOS_escape_02_entry-00.wav")
        # while True:
        #     time.sleep(3)
        #     devices["speaker"].audio_play("hotaru_no_hikari.wav")
    except Exception as e:
        logger.exception(f"An error occured in goal phase: {e}")


if __name__ == "__main__":

    try:
        # 使用するデバイス  変数の中身をこの後変更する
        devices = {
            "bmp": None,
            "bno": None,
            "gnss": None,
            "motor": None,
            "servo": None,
            "pi": None,
            "speaker":None
        }

        # 各デバイスのセットアップ  devicesの中に各デバイスのインスタンスを入れる
        setup(devices)

        # 取得したデータ  新たなデータを取得し次第，中身を更新する
        data = {"phase": None, "lat": None, "lon": None, "datetime_gnss": None, "alt": None, "temp": None, "press": None, "accel": [None, None, None], "line_accel": [None, None, None], "mag": [None, None, None], "gyro": [None, None, None], "grav": [None, None, None], "goal_distance": None, "goal_angle": None, "goal_lat": GOAL_LAT, "goal_lon": GOAL_LON}

        # 風で適当に取った位置の仮のGPS情報
        # data["lat"] = 30.374499
        # data["lon"] = 130.960034

        # 並行処理でBMP280による測定をし続け，dataに代入し続ける
        bmp_thread = Thread(target=devices["bmp"].get_forever, args=(data,))
        bmp_thread.start()  # BMP280による測定をスタート
        
        # 並行処理でBNO055による測定をし続け，dataに代入し続ける
        bno_thread = Thread(target=devices["bno"].get_forever, args=(data,))
        bno_thread.start()  # BNO055による測定をスタート

        # 並行処理でGNSSによる測定をし続け，dataに代入し続ける
        gnss_thread = Thread(target=devices["gnss"].get_forever, args=(data,))
        gnss_thread.start()  # GNSSによる測定をスタート

        # GUI用のサーバーを起動
        server_thread = Thread(target=start_gui.start_server, kwargs={'logger': logger})
        server_thread.start()

        # 並列処理でGUIの表示データを更新
        gui_thread = Thread(target=start_gui.write_to_gui, args=(devices, data,), kwargs={'logger': logger})
        gui_thread.start()  # GUIの更新をスタート

        # 待機フェーズを実行
        wait_phase(devices, data)

        # 落下フェーズを実行
        fall_phase(devices, data)

        # 遠距離フェーズを実行
        long_phase(devices, data)

        # 並列処理でカメラをセットアップして撮影開始（並行処理ではない）
        # 画像認識の結果を camera_order.value ，colorcone_xに代入し続ける
        # 別のプロセスとデータをやり取りするcamera_oederとcolorcone_xは特殊な扱い
        camera_order = Value('i', 0)
        camera_process = Process(target=camera_setup_and_start, args=(camera_order, True))
        camera_process.start()  # 画像認識スタート

        # 短距離フェーズを実行
        short_phase(devices, data, camera_order)

        # ゴールフェーズを実行
        goal_phase(devices, data)

    except Exception as e:
        logger.exception("An unexpected error occured")