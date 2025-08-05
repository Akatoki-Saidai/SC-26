# このプログラムはsc26のtestcode内のファイルをコピーしたものです

# このプログラムはSC25のFM内のファイルをコピーしたものです

# BMP280の受信コード
# 公式マニュアル: https://www.bosch-sensortec.com/products/environmental-sensors/pressure-sensors/bmp280/
# CSBピンは3V3に繋ぐ
# SDOピンはGNDに繋ぐとI2Cアドレスが0x76になり(デフォルト)，3V3に繋ぐとi2Cアドレスが0x77になる


# このコードの動かし方
# 1. ラズパイを起動
# 2. ターミナル(黒い画面)を開く
# 3. 次のコマンドを実行
#   cd ~/sc26_project
#   .  sc26_env/bin/activate           <==必ず実行！！！ 仮想環境に入る
#   cd SC-26
#   git pull
#   python testcode/bmp280/bmp280.py

# もし，次のエラーが表示されたら
#   ModuleNotFoundError: No module named 'smbus2'
# 仮想環境内で!!! 次のコードを実行
#   pip install smbus2

# もし，次のエラーが表示されたら
#  FileNotFoundError: [Errno 2] No such file or directory: '/dev/i2c-1'
# ターミナルで次のコマンドを実行
#   sudo raspi-config
# Interface Options を選択した後に，I2Cを有効化する


import time  # sleepなどを使うため
from logging import getLogger, StreamHandler  # ログを記録するため

# smbus2がインストールされていない場合は仮想環境で以下を実行
# sudo pip install smbus2
from smbus2 import SMBus

# BMP280を扱うためのクラス(BME280もこのプログラムで扱える)
class BMP280:
    # 測定値を受信
    def read(self):
        try:
            # 測定値の生データを受信
            data = []
            for i in range (0xF7, 0xF7+8):
                data.append(self.bus.read_byte_data(self.I2C_ADDRESS,i))
            
            pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
            temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
            hum_raw  = (data[6] << 8)  |  data[7]
            
            # 測定値を℃単位やhPa単位に補正
            temperature = float(self._compensate_T(temp_raw))
            pressure = float(self._compensate_P(pres_raw))
            humidity = float(self._compensate_H(hum_raw))

            # 高度を算出
            altitude = self._get_altitude(temperature, pressure)

            self._logger.info(f"pressure : {pressure:4.3f} hPa, temperature : {temperature: 2.2f} ℃, humidity : {humidity:3.0f} %, altitude : {altitude: 4.2f} m")
            # (f文字列の:の後のスペースには意味があります  https://docs.python.org/ja/3/library/string.html#formatspec )

            return temperature, pressure, humidity, altitude
        except Exception as e:
            self._logger.exception("An error occured in read bmp280")

    # BMP280の起動時の処理
    def __init__(self, logger = None):
        # もしloggerが渡されなかったら，ログの記録先を標準出力に設定
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)
        self._logger = logger

        self.BUS_NUMBER  = 1  # I2C1を使用(デフォルト)
        self.I2C_ADDRESS = 0x76  # BMP280のI2Cアドレス．通信先のセンサの電話番号のようなもの．0x76(デフォルト)または0x77
        self.bus = SMBus(self.BUS_NUMBER)  # I2Cを扱うsmbusを定義

        self._setup()  # 測定方法や補正方法を設定
        self._get_calib_param()  # 補正用パラメータの読み取りと保存
        self._qnh = 1013.25
        
        # 起動直後は測定が終わっておらず値が異常なので空受信
        for i in range(20):
            self.read()
            time.sleep(0.1)
        self._get_qnh()  # 高度0m地点とする場所の気圧を保存

    # 測定方法や補正方法を設定
    def _setup(self):
        try:
            osrs_t = 1  # 気温のオーバーサンプリング (複数回測定すると精度が上がり測定にかかる時間が伸びる．0:測定しない, 1:1回, 2:2回, 3:4回, 4:8回, 5:16回)
            osrs_p = 2  # 気圧のオーバーサンプリング (複数回測定すると精度が上がり測定にかかる時間が伸びる．0:測定しない, 1:1回, 2:2回, 3:4回, 4:8回, 5:16回)
            osrs_h = 1  # 湿度のオーバーサンプリング (複数回測定すると精度が上がり測定にかかる時間が伸びる．0:測定しない, 1:1回, 2:2回, 3:4回, 4:8回, 5:16回) (BME280では使うがBMP280では不使用)
            mode   = 3  # 電力モード (0:sleep, 1:forced(1回だけすばやく測定), 3:normal(t_sb間隔で何度も測定))
            t_sb   = 1  # normalモードにおける測定(データの更新)間隔  (0:0.5ms, 1:62.5ms, 2:125ms, 3:250ms, 4:500ms, 5:1000ms, 6:2000ms, 7:4000ms)
            filter = 1  # ノイズを除去するIIRフィルタ (0:off, 1,2,3,4:on(数字が増えると精度が上がり消費電力も上がる))
            spi3w_en = 0  # 3線式SPIを有効にするか (I2Cを使うので無効化しておく)

            # 設定データを送信用のバイト列に加工
            ctrl_meas_reg = (osrs_t << 5) | (osrs_p << 2) | mode
            config_reg    = (t_sb << 5) | (filter << 2) | spi3w_en
            ctrl_hum_reg  = osrs_h

            # 設定を送信
            self._writeReg(0xF2,ctrl_hum_reg)
            self._writeReg(0xF4,ctrl_meas_reg)
            self._writeReg(0xF5,config_reg)
        except Exception as e:
            self._logger.exception("An error occured in setup bmp280")
    
    # I2CにてBME280にデータを送信
    def _writeReg(self, reg_address, data):
        try:
            self.bus.write_byte_data(self.I2C_ADDRESS,reg_address,data)  # smbusを使用しI2Cでデータを送信 (i2cアドレスは誰宛のデータかを示す，レジスタアドレスはセンサのメモリ内の番地を表す)
        except Exception as e:
            self._logger.exception("An error occured in write bmp280")

    # 補正用パラメータを受信して保存 (測定開始前に必ず実行すること!)
    def _get_calib_param(self):
        try:
            # 補正用パラメータを初期化
            self._digT = [0, 0, 0]  # 温度の補正パラメータ
            self._digP = [0, 0, 0, 0, 0, 0, 0, 0, 0]  # 気圧の補正パラメータ
            self._digH = [0, 0, 0, 0, 0, 0]  # 湿度の補正パラメータ(BME280の名残で書いてあるだけで，BMP280では不使用)
            self._t_fine = 0.0  # 気圧の補正に使う気温の値

            calib = []  # 受信した補正用生データをここに格納
        
            # 補正用パラメータを受信
            for i in range (0x88,0x88+24):
                calib.append(self.bus.read_byte_data(self.I2C_ADDRESS,i))
            calib.append(self.bus.read_byte_data(self.I2C_ADDRESS,0xA1))
            for i in range (0xE1,0xE1+7):
                calib.append(self.bus.read_byte_data(self.I2C_ADDRESS,i))

            # 受信した補正用生データを加工して保存
            self._digT[0] = ((calib[1] << 8) | calib[0])  # 気温補正データ
            self._digT[1] = ((calib[3] << 8) | calib[2])
            self._digT[2] = ((calib[5] << 8) | calib[4])
            self._digP[0] = ((calib[7] << 8) | calib[6])  # 気圧補正データ
            self._digP[1] = ((calib[9] << 8) | calib[8])
            self._digP[2] = ((calib[11]<< 8) | calib[10])
            self._digP[3] = ((calib[13]<< 8) | calib[12])
            self._digP[4] = ((calib[15]<< 8) | calib[14])
            self._digP[5] = ((calib[17]<< 8) | calib[16])
            self._digP[6] = ((calib[19]<< 8) | calib[18])
            self._digP[7] = ((calib[21]<< 8) | calib[20])
            self._digP[8] = ((calib[23]<< 8) | calib[22])
            self._digH[0] = ( calib[24] )  # 湿度補正データ(BME280では使うがBMP280では不使用)
            self._digH[1] = ((calib[26]<< 8) | calib[25])
            self._digH[2] = ( calib[27] )
            self._digH[3] = ((calib[28]<< 4) | (0x0F & calib[29]))
            self._digH[4] = ((calib[30]<< 4) | ((calib[29] >> 4) & 0x0F))
            self._digH[5] = ( calib[31] )
            
            # 補正用パラメータを適切な形式に変換
            ## この部分を削除すると気圧が1090hPaくらいの異常値になります
            for i in range(1,2):
                if self._digT[i] & 0x8000:
                    self._digT[i] = (-self._digT[i] ^ 0xFFFF) + 1

            for i in range(1,8):
                if self._digP[i] & 0x8000:
                    self._digP[i] = (-self._digP[i] ^ 0xFFFF) + 1

            for i in range(0,6):
                if self._digH[i] & 0x8000:
                    self._digH[i] = (-self._digH[i] ^ 0xFFFF) + 1  
        except Exception as e:
            self._logger.exception("An error occured in caliblation bmp280")

    # QNH(高度0m地点の気圧)を測定
    def _get_qnh(self):
        try:
            qnh_values = []
            qnh_size = 20

            # 気圧を複数回測定し，平均値を求める
            for i in range(qnh_size):
                _, pressure, _, _ = self.read()
                qnh_values.append(pressure)
                time.sleep(0.1)

            self._qnh = sum(qnh_values) / len(qnh_values)
            self._logger.info(f"qnh: {self._qnh}")
        except Exception as e:
            self._logger.exception("An error occured in bmp280 getting qnh")
    
    # 気温と気圧から高度を算出
    def _get_altitude(self, temperature, pressure):
        try:
            # qnh = 高度0m地点の気圧.
            
            # 気圧のみを使って高度を算出 (推奨)
            altitude = (((1 - (pow((pressure / self._qnh), 0.190284))) * 145366.45) / 0.3048 ) / 10
            
            # 気圧と温度を使って高度を算出 (直射日光によるセンサの温度上昇の影響を受けるため非推奨)
            # altitude = ((pow((self.qnh / pressure), (1.0 / 5.257)) - 1) * (temperature + 273.15)) / 0.0065

            return altitude
        except Exception as e:
            self._logger.exception("An error occured in bmp280 getting altitude")

    # 気温の生データを℃単位に補正
    def _compensate_T(self, adc_T):
        try:
            v1 = (adc_T / 16384.0 - self._digT[0] / 1024.0) * self._digT[1]
            v2 = (adc_T / 131072.0 - self._digT[0] / 8192.0) * (adc_T / 131072.0 - self._digT[0] / 8192.0) * self._digT[2]
            self._t_fine = v1 + v2
            temperature = self._t_fine / 5120.0

            return temperature
        except Exception as e:
            self._logger.exception("An error occured in bmp280 getting temperture")

    # 気圧の生データをhPa単位に補正
    def _compensate_P(self, adc_P):
        try:
            pressure = 0.0
            
            v1 = (self._t_fine / 2.0) - 64000.0
            v2 = (((v1 / 4.0) * (v1 / 4.0)) / 2048) * self._digP[5]
            v2 = v2 + ((v1 * self._digP[4]) * 2.0)
            v2 = (v2 / 4.0) + (self._digP[3] * 65536.0)
            v1 = (((self._digP[2] * (((v1 / 4.0) * (v1 / 4.0)) / 8192)) / 8)  + ((self._digP[1] * v1) / 2.0)) / 262144
            v1 = ((32768 + v1) * self._digP[0]) / 32768
            
            if v1 == 0:
                return 0
            pressure = ((1048576 - adc_P) - (v2 / 4096)) * 3125
            if pressure < 0x80000000:
                pressure = (pressure * 2.0) / v1
            else:
                pressure = (pressure / v1) * 2
            v1 = (self._digP[8] * (((pressure / 8.0) * (pressure / 8.0)) / 8192.0)) / 4096
            v2 = ((pressure / 4.0) * self._digP[7]) / 8192.0
            pressure = pressure + ((v1 + v2 + self._digP[6]) / 16.0)  

            return pressure / 100
        except Exception as e:
            self._logger.exception("An error occured in bmp280 getting pressure")
    
    # 湿度の生データを%単位に補正
    def _compensate_H(self, adc_H):
        v1 = self._t_fine - 76800.0
        if v1 != 0:
            v1 = (adc_H - (self._digH[3] * 64.0 + (self._digH[4] / 16384.0) * v1)) * (
                self._digH[1] / 65536.0 * (1.0 + (self._digH[5] / 67108864.0) * v1 * (1.0 + (self._digH[2] / 67108864.0) * v1)))

        humidity = v1 * (1.0 - self._digH[0] * v1 / 524288.0)
        if humidity > 100.0:
            humidity = 100.0
        elif humidity < 0.0:
            humidity = 0.0
        
        return humidity
    
    # ずっと測定し続ける
    def get_forever(self, data):
        while True:
            try:
                data["temp"], data["press"], _, data["alt"] = self.read()
                time.sleep(0.1)
            except Exception as e:
                self._logger.exception(f"An error occured in bmp280 get_forever: {e}")


if __name__ == '__main__':
    bmp = BMP280()  # BMP280のインスタンスを作成
    
    while True:
        try:
            temperature, pressure, _, altitude = bmp.read()  # 温度，気圧(，湿度), 高度を読み取り
            time.sleep(1)
        except Exception as e:
            print(f"Unexpected error occcured: {e}")