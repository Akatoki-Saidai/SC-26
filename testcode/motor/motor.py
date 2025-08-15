#引用元(https://www.radical-dreamer.com/programming/raspberry-pi-pwm-motordriver/)コミット
from logging import getLogger, StreamHandler
import pigpio
import time

class Motor:
    def __init__(self, right_pin1=18, right_pin2=12, left_pin1=13, left_pin2=19, logger=None):
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)  # DEBUGレベル
        self._logger = logger

        self._right_pin1 = right_pin1
        self._right_pin2 = right_pin2
        self._left_pin1 = left_pin1
        self._left_pin2 = left_pin2
        
        self._pi = pigpio.pi()

        # Stop
        self._pi.set_PWM_frequency(self._right_pin1, 1000)  # 1kHz
        self._pi.set_PWM_frequency(self._right_pin2, 1000)  # 1kHz
        self._pi.set_PWM_frequency(self._left_pin1, 1000)  # 1kHz
        self._pi.set_PWM_frequency(self._left_pin2, 1000)  # 1kHz
    
    def set_right(self, speed):
        """右モーターの速度を設定"""
        if speed > 1:
            speed = 255
        else:
            speed = int(speed * 255)

        if speed >= 0:
            self._pi.set_PWM_dutycycle(self._right_pin2, speed)
            self._pi.set_PWM_dutycycle(self._right_pin1, 0)
        elif speed < 0:
            self._pi.set_PWM_dutycycle(self._right_pin1, speed)
            self._pi.set_PWM_dutycycle(self._right_pin2, 0)
    
    def set_left(self, speed):
        """左モーターの速度を設定"""
        if speed > 1:
            speed = 255
        else:
            speed = int(speed * 255)

        if speed >= 0:
            self._pi.set_PWM_dutycycle(self._left_pin1, speed)
            self._pi.set_PWM_dutycycle(self._left_pin2, 0)
        elif speed < 0:
            self._pi.set_PWM_dutycycle(self._left_pin2, speed)
            self._pi.set_PWM_dutycycle(self._left_pin1, 0)
    
    def stop(self):
        """モーターを停止"""
        self._pi.set_PWM_dutycycle(self._right_pin1, 0)
        self._pi.set_PWM_dutycycle(self._right_pin2, 0)
        self._pi.set_PWM_dutycycle(self._left_pin1, 0)
        self._pi.set_PWM_dutycycle(self._left_pin2, 0)

    def turn(self, angle):
        """指定した角度だけ回転
        angle: 0~360度，0:前進，90:右旋回，...
        """
        angle %= 360  # 角度を0~360の範囲に正規化
        self._logger.debug(f"Turning to angle: {angle}")
        if 0 <= angle and angle < 180:
            self.set_right(1 - angle / 90)
            self.set_left(1)
        elif 180 <= angle and angle <= 360:
            self.set_right(1)
            self.set_left(1 - (angle - 180) / 90)
        else:
            self.set_right(0)
            self.set_left(0)
    
    def __del__(self):
        """インスタンスが削除されるときにモーターを停止"""
        self.stop()
        self._pi.stop()


if __name__ == "__main__":
    motor = Motor()

    try:
        while True:
            # Forward
            motor.turn(0)
            time.sleep(2)

            # Stop
            motor.stop()
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("終了します。PWMを停止します。")
        motor.stop()