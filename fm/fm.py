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
# from speaker import Speaker
import shutil

logger = sc_logging.get_logger(__name__)

NICR_PIN = 6  # ニクロム線のGPIO番号

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
        devices["motor"] = Motor(right_pin1=18, right_pin2=12, left_pin1=13, left_pin2=19, logger=logger)

        # サーボモーターのセットアップ
        devices["servo1"] = SG90(pin=20, min_angle=-90, max_angle=90, ini_angle=0, freq=50, logger=logger)
        devices["servo2"] = SG90(pin=21, min_angle=-90, max_angle=90, ini_angle=0, freq=50, logger=logger)

        # pigpioのセットアップ
        devices["raspi"] = pigpio.pi()
        # NiCr線のセットアップ
        devices["raspi"].set_mode(NICR_PIN, pigpio.OUTPUT)  # NiCrのピンを出力モードに設定
        devices["raspi"].write(NICR_PIN, 0)  # NiCrをオフにしておく

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
        
    except Exception as e:
        logger.exception(f"An error occured in setup and start camera: {e}")

# 待機フェーズ
def wait_phase(devices, data):
    try:
        logger.info("Entered wait phase")
        data["phase"] = "wait"

    except Exception as e:
        logger.exception(f"An error occured in Entering wait phase:{e}")
    
    # 高度が高くなるまで待つ
    while True:
        try:
            time.sleep(0.1)
            # ここに待機フェーズの処理を書いて
            # 高度が十分高い場合
            if 15 < data["alt"]:
                prev_alt = data["alt"]
                time.sleep(5)
                # ある程度時間が経過後も高度が十分高く、かつ少しでも高度が変化している場合、待機フェーズを終了
                if 15 < data["alt"] and prev_alt != data["alt"]:
                    print("\n\n")
                    logger.info("Ended wait phase")
                    print("\n\n")
                    break
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
        logger.exception(f"An error occured in Entering fall phase: {e}")
                         
    # 落下して静止するまで待つ
    while True:
        try:
            time.sleep(0.1)
            # ここに落下フェーズの処理を書いて
            # 地面近くで静止している場合
            if data["alt"] < 5 and sum(abs(line_accel_xyz) for line_accel_xyz in data["line_accel"]) < 0.5 and sum(abs(gyro_xyz) for gyro_xyz in data["line_accel"]) < 0.025:
                prev_line_accel, prev_gyro = copy.copy(data["line_accel"]), copy.copy(data["gyro"])
                time.sleep(5)
                # ある程度時間が経過後も地面近くで静止し、かつ少しでも高度が変化している場合、NiCr線を焼き切る
                if sum(abs(line_accel_xyz) for line_accel_xyz in data["line_accel"]) < 0.5 and sum(abs(gyro_xyz) for gyro_xyz in data["gyro"]) < 0.05 and prev_line_accel != data["line_accel"] and prev_gyro != data["gyro"]:
                    logger.info("Turn on to cut nicr")
                    devices["raspi"].write(NICR_PIN, 1) # NiCr線に電流を流す(ON)
                    time.sleep(5)
                    devices["raspi"].write(NICR_PIN, 0) # NiCr線に電流を流すのをストップ(OFF)
                    logger.info("Turn off nicr")
                    print("\n\n")
                    logger.info("Ended fall phase")
                    print("\n\n")
                    break
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
        if data["gyro"][2] < 0:
            start_time = time.time()
            devices["motor"].turn(0) # 0度(前進)に向く
            logger.info("muki_hantai")
            while data["gyro"][2] < 0 and time.time() - start_time < 5:
                pass
            devices["motor"].turn(0) # 0度(前進)に向く
    except Exception as e:
        logger.exception(f"An error occured in muki_hantai: {e}")
    
    # ゴールから離れている間，ゴールに向かって進む
    while True:
        try:
            time.sleep(0.1)
            devices["motor"].turn(data["goal_angle"]) # 回転する
            
            # GPSがタイムアウト
            if time.time() - long_start_time > 360 and data["goal_angle"] is None:
                break
            
            # ゴールが近づいたら遠距離フェーズを終了
            if data["goal_distance"] < 5:
                print("\n\n")
                logger.info("Ended long phase")
                print("\n\n")
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
            if camera_order.value == 0: # コーンが見つからなかった場合
                devices["motor"].turn(90)
                time.sleep(0.3)
                devices["motor"].stop()
                time.sleep(0.7)
            elif camera_order.value == 1: # コーンが正面にあった場合
                devices["motor"].turn(0)
            elif camera_order.value == 2: # コーンが右にあった場合
                devices["motor"].turn(90)
            elif camera_order.value == 3: # コーンが左にあった場合
                devices["motor"].turn(270)
            elif camera_order.value == 4: #コーンが十分に大きく見えた場合、近距離フェーズを終了
                print("\n\n")
                logger.info("Ended short phase")
                print("\n\n")
                break
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
            "servo1": None,
            "servo2": None,
            "raspi": None
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