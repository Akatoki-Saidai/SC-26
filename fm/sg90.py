import pigpio  # pigpioでPWM出力
import time

from logging import getLogger, StreamHandler  # ログを記録するため

"""
参考にしたサイト
コード全体：https://qiita.com/Marusankaku_E/items/7cc1338fbab04291a296
SG90のデータシート：https://akizukidenshi.com/goodsaffix/SG90_a.pdf
S35 STDの仕様について：https://qiita.com/yukima77/items/cb640ce99c9fd624a308
上同：https://akizukidenshi.com/catalog/g/g108305/
"""

# pigpioが動かないときはpigpioが有効化されていないかもしれません．
# sudo pigpiod を実行

class SG90:
    """SG90を制御するクラス

    pin: GPIOのピン番号
    max_angle: 最大移動角度
    min_angle: 最小移動角度
    angle: 現在の角度
    ini_angle: 初期設定角度
    pi: gpio制御
    """
    def __init__(self, pin, min_angle=0, max_angle=180, ini_angle=0, freq=50, logger=None):
        """サーボモータをセットアップ"""

        # もしloggerが渡されなかったら，ログの記録先を標準出力にする
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)
        self._logger = logger

        self._pin = pin
        self._max_angle = max_angle
        self._min_angle = min_angle
        self._angle = 0
        self._ini_angle = ini_angle
        self._freq = freq
        self._range = 255

        self._pi = pigpio.pi()
        self._pi.set_mode(self._pin, pigpio.OUTPUT)

        self.set_ini_angle()
    
    def __del__(self):
        """サーボモータを終了"""
        if self._pi.connected:
            self._pi.set_mode(self._pin, pigpio.INPUT)
            # self._pi.stop()

    def get_angle(self):
        """サーボモータの角度を取得"""
        return self._angle

    #set_servo_pulsewidthを使わない方法(案)
    def set_angle(self, target_angle):
        """サーボモータの角度を特定の角度に動かす"""
        if target_angle < self._min_angle or target_angle > self._max_angle:
            self._logger.warning(f"角度は{self._min_angle}から{self._max_angle}度の間で指定してください。")
            return
        
        # target_angleを_min_angle次第で修正
        target_angle = target_angle - self._min_angle

        #角度[degree]→パルス幅[μs]に変換
        pulse_width = ((target_angle)/180.0) * 1900.0+500.0
        self._angle = target_angle
        #duty比[%]を計算(周期：20ms=20000μs)
        pwm_duty = 100.0 * (pulse_width/20000.0)
        #duty比をhardware_PWMに使える形に変換(1,000,000を100%と考えて数値を指定するらしい.整数で表したいとかなんとか.)
        duty_cycle = int(pwm_duty * 1000000 / 100)
        frequency = int(self._freq)
        
        #PWM出力
        # hardware-PWM バージョン
        # self.pi.hardware_PWM(self.pin,frequency,duty_cycle)
        # software-PWM バージョン
        self._pi.set_PWM_frequency(self._pin, frequency)
        self._pi.set_PWM_range(self._pin, self._range)
        self._pi.set_PWM_dutycycle(self._pin, int((pwm_duty / 100) * self._range))

        self._logger.info(f"servo_angle: {self._angle}")
    
    def set_ini_angle(self):
        self.angle = self._ini_angle
    
    

if __name__ == "__main__":
    # 動作サンプル

    sg90 = SG90(pin=26, min_angle=0, max_angle=180, ini_angle=90, freq=50)
    time.sleep(2)

    for angle in range(90, 180, 5):
        # 現在の角度を表示
        print(f"kakudo_now: {sg90.get_angle()}")
        # 角度をセット
        sg90.set_angle(angle)
        time.sleep(0.5)
    
    for angle in range(180, 0, 10):
        # 現在の角度を表示
        print(f"kakudo_now: {sg90.get_angle()}")
        # 角度をセット
        sg90.set_angle(angle)
        time.sleep(0.5)
    
    sg90.set_angle(90)
    time.sleep(0.5)
    sg90.set_angle(95)
    time.sleep(0.5)
    sg90.set_angle(100)
    time.sleep(0.5)
    sg90.set_angle(105)
    time.sleep(0.5)

    
    sg90.set_angle(90)
    time.sleep(0.5)
    sg90.set_angle(85)
    time.sleep(0.5)
    sg90.set_angle(80)
    time.sleep(0.5)
    sg90.set_angle(75)
    time.sleep(0.5)

    
    sg90.set_angle(90)
    
    #del sg90  # サーボモータをストップ(delしなくても勝手に止まる)