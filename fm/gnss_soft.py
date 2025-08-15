from logging import getLogger, StreamHandler
from threading import Thread
import time
from micropyGPS import MicropyGPS
import pigpio  # pigpioライブラリを使用してソフトUART
import sys
import calc_goal

class GNSS_Soft:
    def __init__(self, tx_pin=16, rx_pin=26, baudrate=9600, logger=None):
        # ログ設定
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)  # DEBUG
        self._logger = logger

        # pigpio 初期化
        self._pi = pigpio.pi()
        if not self._pi.connected:
            self._logger.error("pigpioデーモンに接続できません。`sudo pigpiod` を実行してください。")
            sys.exit(1)

        # ソフトウェアUART設定
        self._rx_pin = rx_pin
        self._baudrate = baudrate
        self._pi.set_mode(self._rx_pin, pigpio.INPUT)
        self._pi.bb_serial_read_open(self._rx_pin, self._baudrate)

        # GPSパーサ設定
        self._pygps = MicropyGPS(9, 'dd')

        # GNSSデータ読み取りスレッド
        self._read_thread = Thread(target=self._update, daemon=True)
        self._read_thread.start()

    def _update(self):
        """ソフトUART経由でGNSSデータを取得"""
        while True:
            (count, data) = self._pi.bb_serial_read(self._rx_pin)
            # print(f"{count=}")
            if count > 0:
                try:
                    text = data.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    continue

                print(text, end='')  # NMEA文確認用
                for char in text:
                    if 10 <= ord(char) <= 126:
                        self._pygps.update(char)
            time.sleep(0.01)  # CPU負荷軽減

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

                    self._logger.debug(f"lat2: {lat}, lon2: {lon}, alt2: {self._pygps.altitude}, speed2: {self._pygps.speed}, gnss_datetime2: {datetime_gnss}")

                    data.update({
                        "lat2": lat,
                        "lon2": lon,
                        "datetime_gnss2": datetime_gnss
                    })

                    # 目標地点までの計算
                    calc_goal.calc_goal(data)

                time.sleep(1)
            except Exception as e:
                self._logger.exception(f"Error in GNSS loop: {e}")

if __name__ == "__main__":
    try:
        gnss = GNSS_Soft(rx_pin=20, baudrate=38400)  # RXピン番号を環境に合わせて変更
        data = {"lat": None, "lon": None}
        gnss.get_forever(data)
    except KeyboardInterrupt:
        print("終了します。最終データ:", data)
    except Exception as e:
        print(f"致命的なエラー: {e}")
