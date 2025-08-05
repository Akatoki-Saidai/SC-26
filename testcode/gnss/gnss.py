from logging import getLogger, StreamHandler
from threading import Thread
import time
from micropyGPS import MicropyGPS
import serial
# import calc_goal

class GNSS:
    def __init__(self, logger=None):
        # ログ設定
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)  # DEBUGレベル
        self._logger = logger

        # シリアル通信設定（GNSSモジュールと接続）
        self._uart = serial.Serial('/dev/serial0', 9600, timeout=10)

        # GPSパーサの設定（MicropyGPS）
        self._pygps = MicropyGPS(9, 'dd')  # JST（UTC+9）、度（dd）表記

        # GNSSデータ読み取りスレッド開始
        self._read_thread = Thread(target=self._update, daemon=True)
        self._read_thread.start()

    def _update(self):
        """GNSSモジュールからのデータをリアルタイムで読み取り、MicropyGPSに渡す"""
        while True:
            read_str = self._uart.read(self._uart.in_waiting).decode('utf-8', errors='ignore')
            print(read_str, end='')  # NMEA文を確認できるように表示
            for char in read_str:
                if 10 <= ord(char) <= 126:
                    # print(char, end='')  # NMEA文を確認できるように表示
                    self._pygps.update(char)

    def get_forever(self, data: dict):
        """常に最新の位置情報をdata辞書に格納"""
        while True:
            try:
                if self._pygps.parsed_sentences > 0:
                    lat = self._pygps.latitude[0]
                    lon = self._pygps.longitude[0]
                    date = self._pygps.date
                    time_ = self._pygps.timestamp
                    offset = self._pygps.local_offset
                    datetime_gnss = f"20{date[2]:02}-{date[1]:02}-{date[0]:02}T{time_[0]:02}:{time_[1]:02}:{time_[2]:05.2f}{offset:+03}:00"

                    self._logger.debug(f"lat: {lat}, lon: {lon}, alt: {self._pygps.altitude}, speed: {self._pygps.speed}, gnss_datetime: {datetime_gnss}")

                    data.update({
                        "lat": lat,
                        "lon": lon,
                        "datetime_gnss": datetime_gnss
                    })

                    # 目標地点までの計算
                    # calc_goal.calc_goal(data)
                time.sleep(1)
            except Exception as e:
                self._logger.exception(f"Error in GNSS loop: {e}")

if __name__ == "__main__":
    try:
        gnss = GNSS()
        data = {"lat": None, "lon": None}
        gnss.get_forever(data)
    except KeyboardInterrupt:
        print("終了します。最終データ:", data)
    except Exception as e:
        print(f"致命的なエラー: {e}")

