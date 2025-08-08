import pigpio
import time
from logging import getLogger, StreamHandler  # ログを記録するため

class MotorChannel(object):
    # 1つのモーターの制御クラス
    # inverseとreverseどちらか一方のピンにのみPWM出力を行う
    
    def __init__(self, pi, pin1, pin2, logger=None):
        # もしloggerが渡されなかったら，ログの記録先を標準出力に設定
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)
        self._logger = logger

        self.pi = pi
        self.pin_inverse = pin1
        self.pin_reverse = pin2
        self.MOTOR_RANGE = 100  # 0～255の範囲で設定
        self.FREQUENCY = 4000  # pigpioのデフォルトサンプリングレートは5→8000,4000,2000,1600,1000,800,500,400,320のいずれか
        self.delta_duty = 0.1

        # PWM設定
        self.pi.set_PWM_frequency(self.pin_inverse, self.FREQUENCY)
        self.pi.set_PWM_range(self.pin_inverse, self.MOTOR_RANGE)

        self.pi.set_PWM_frequency(self.pin_reverse, self.FREQUENCY)
        self.pi.set_PWM_range(self.pin_reverse, self.MOTOR_RANGE)

        # 初期状態は停止
        self.current_duty = 0.0   # 0～1の割合
        self.current_direction = 0  # 1: 正転, -1: 逆転, 0: 停止
        self.target_duty = 0.0
        self.target_direction = 0
        self.update_mode = 0
        self._apply_duty()
    
    def __del__(self):
        # オブジェクトの削除時のクリーンアップ
        if self.pi.connected:
            self._pi.set_mode(self.pin_inverse, pigpio.INPUT)
            self._pi.set_mode(self.pin_reverse, pigpio.INPUT)
            # self._pi.stop()

    def _apply_duty(self):
        # PWM出力を更新(片側)

        if self.current_direction == 1:
            # 正転：inverseに duty、reverseは0
            self.pi.set_PWM_dutycycle(self.pin_inverse, int(self.current_duty * self.MOTOR_RANGE))
            self.pi.set_PWM_dutycycle(self.pin_reverse, 0)
        elif self.current_direction == -1:
            # 逆転：reverseに duty、inverseは0
            self.pi.set_PWM_dutycycle(self.pin_inverse, 0)
            self.pi.set_PWM_dutycycle(self.pin_reverse, int(self.current_duty * self.MOTOR_RANGE))
        else:
            # 停止
            self.pi.set_PWM_dutycycle(self.pin_inverse, 0)
            self.pi.set_PWM_dutycycle(self.pin_reverse, 0)


    def set_target(self, target_inverse, target_reverse):
        # 目標のduty値を設定
        # target_inverse, target_reverse は [0,1]の値。両方同時に0より大きい場合はエラー

        if target_inverse > 0 and target_reverse > 0:
            self._logger.error(f"pin1:{self.pin_inverse}, pin2:{self.pin_reverse}: Both pin over 0 voltage: {target_inverse}, {target_reverse}")    
            raise ValueError(f"pin1:{self.pin_inverse}, pin2:{self.pin_reverse}: Both pin over 0 voltage: {target_inverse}, {target_reverse}")
        
        if target_inverse > 0:
            self.target_direction = 1
            self.target_duty = target_inverse
        elif target_reverse > 0:
            self.target_direction = -1
            self.target_duty = target_reverse
        else:
            self.target_direction = 0
            self.target_duty = 0.0

        # 方向が変わる場合は、まず停止後に加速するので update_mode を "accelerate" とする
        if self.current_direction != self.target_direction:
            if self.target_duty > 0:
                self.update_mode = 1
            else:
                self.update_mode = 0
                
        else:
            # 同じ方向なら、現在値と目標値の大小でモードを判定
            if self.target_duty > self.current_duty:
                self.update_mode = 1
            elif self.target_duty < self.current_duty:
                self.update_mode = -1
            else:
                self.update_mode = 0

    def update_step(self):
        # 1ステップ分現在のdutyを目標へ変更
        try:
            if self.current_direction != self.target_direction:
                if self.current_duty > 0:
                    self.current_duty = max(self.current_duty - self.delta_duty, 0)
                else:
                    self.current_direction = self.target_direction

            else:
                # 全てのピンは現在0(の予定)
                # 現在の duty から目標 duty 1ステップ分変化
                # 加速
                if self.current_duty < self.target_duty:
                    self.current_duty = min(self.current_duty + self.delta_duty, self.target_duty)
                # 減速
                elif self.current_duty > self.target_duty:
                    self.current_duty = max(self.current_duty - self.delta_duty, self.target_duty)

            self._apply_duty()
        
        except Exception as e:
            self._logger.exception("An error occured in motor update_step")

    
    def at_target(self):
        # 現在の duty が目標値に達しているかを判定

        if self.current_direction != self.target_direction:
            return False
        if self.target_duty == 0:
            return self.current_duty == 0
        if self.update_mode > 0:
            return self.current_duty >= self.target_duty
        elif self.update_mode < 0:
            return self.current_duty <= self.target_duty
        
        return self.current_duty == self.target_duty

class Motor(object):
    # 各モーターはMotorChannelで管理
    
    def __init__(self, right_pin1=21, right_pin2=20, left_pin1=7, left_pin2=5, logger=None):
        # もしloggerが渡されなかったら，ログの記録先を標準出力に設定
        if logger is None:
            logger = getLogger(__name__)
            logger.addHandler(StreamHandler())
            logger.setLevel(10)
        self._logger = logger
        
        self.pi = pigpio.pi()
        if not self.pi.connected:
            self._logger.error("Failed to connect to pigpio daemon in motor")
            raise RuntimeError("Failed to connect to pigpio daemon in motor")
        
        self.right_motor = MotorChannel(self.pi, right_pin1, right_pin2, logger=self._logger)
        self.left_motor  = MotorChannel(self.pi, left_pin1, left_pin2, logger=self._logger)
        self.delta_time = 0.05

    
    def Speedup(self, right_inverse, right_reverse, left_inverse, left_reverse):
        # 両モーターの目標値を設定、同時に更新
        
        self.right_motor.set_target(right_inverse, right_reverse)
        self.left_motor.set_target(left_inverse, left_reverse)
        # 両モーターが目標状態に達するまで同時に1ステップずつ更新
        while not (self.right_motor.at_target() and self.left_motor.at_target()):
            self.right_motor.update_step()
            self.left_motor.update_step()
            time.sleep(self.delta_time)

    def accel(self):
        # 正転
        try:
            self.Speedup(1, 0, 1, 0)
        except Exception as e:
            self._logger.exception("An error occured in motor accel")

    def stop(self):
        # 惰性ブレーキ
        try:
            self.Speedup(0, 0, 0, 0)
        except Exception as e:
            self._logger.exception("An error occured in motor stop")

    def brake(self):
        # 短絡ブレーキ(モーターには負荷)
        try:
            self.pi.set_PWM_dutycycle(self.right_motor.pin_inverse, int(1 * self.right_motor.MOTOR_RANGE))
            self.pi.set_PWM_dutycycle(self.right_motor.pin_reverse, int(1 * self.right_motor.MOTOR_RANGE))
            self.pi.set_PWM_dutycycle(self.left_motor.pin_inverse, int(1 * self.left_motor.MOTOR_RANGE))
            self.pi.set_PWM_dutycycle(self.left_motor.pin_reverse, int(1 * self.left_motor.MOTOR_RANGE))

            # 状態更新
            self.right_motor.current_duty = 0
            self.right_motor.current_direction = 0
            self.left_motor.current_duty = 0
            self.left_motor.current_direction = 0
        except Exception as e:
            self._logger.exception("An error occured in short brake")

    def leftturn(self):
        # 左回転(右を向く)
        try:
            self.Speedup(1, 0, 0, 1)
        except Exception as e:
            self._logger.exception("An error occured in motor leftturn")

    def rightturn(self):
        # 右回転(左を向く)
        try:
            self.Speedup(0, 1, 1, 0)
        except Exception as e:
            self._logger.exception("An error occured in motor rightturn")

    def leftcurve(self):
        # 左前に進む
        try:
            self.Speedup(1, 0, 0.6, 0)
        except Exception as e:
            self._logger.exception("An error occured in motor leftcurve")

    def rightcurve(self):
        # 右前に進む
        try:
            self.Speedup(0.6, 0, 1, 0)
        except Exception as e:
            self._logger.exception("An error occured in motor rightcurve")

    def back(self):
        # 後ろ
        try:
            self.Speedup(0, 1, 0, 1)
        except Exception as e:
            self._logger.exception("An error occured in motor back")

    def cleanup(self):
        try:
            self.pi.stop()
        except Exception as e:
            self._logger.exception("An error occured in motor cleanup")

    def getPWMduty(self):
        try:
            right_pin1_duty = self.right_motor.pi.get_PWM_dutycycle(self.right_motor.pin_inverse)
            right_pin2_duty = self.right_motor.pi.get_PWM_dutycycle(self.right_motor.pin_reverse)
            left_pin1_duty = self.left_motor.pi.get_PWM_dutycycle(self.left_motor.pin_inverse)
            left_pin2_duty = self.left_motor.pi.get_PWM_dutycycle(self.left_motor.pin_reverse)

            return right_pin1_duty, right_pin2_duty, left_pin1_duty, left_pin2_duty
        
        except Exception as e:
            self._logger.exception("Anerror occured in motor getPWM")


def main():
    motor = Motor(right_pin1=21, right_pin2=20, left_pin1=7, left_pin2=5)
    print("motor initialized\nstart?")
    input()

    print("accel")
    motor.accel()
    time.sleep(2)

    print("stop")
    motor.stop()
    time.sleep(1)

    print("rightturn")
    motor.rightturn()
    time.sleep(2)

    print("leftturn")
    motor.leftturn()
    time.sleep(2)

    print("stop")
    motor.stop()
    time.sleep(1)

    print("accel")
    motor.accel()
    time.sleep(2)

    print("brake")
    motor.brake()
    time.sleep(2)

    print("back")
    motor.back()
    time.sleep(2)

    print("stop")
    motor.stop()
    time.sleep(1)
    
    print("test movement end")
    motor.cleanup()

if __name__ == '__main__':
    main()
