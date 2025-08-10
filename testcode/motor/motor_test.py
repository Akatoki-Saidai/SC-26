#引用元(https://www.radical-dreamer.com/programming/raspberry-pi-pwm-motordriver/)コミット
import pigpio
import time

R1_GPIO = 18
R2_GPIO = 12
L1_GPIO = 13
L2_GPIO = 19

pi = pigpio.pi()

# Stop
pi.set_PWM_frequency(R1_GPIO, 1000)  # 1kHz
pi.set_PWM_frequency(R2_GPIO, 1000)  # 1kHz
pi.set_PWM_frequency(L1_GPIO, 1000)  # 1kHz
pi.set_PWM_frequency(L2_GPIO, 1000)  # 1kHz
# time.sleep(30)

try:
    while True:
        # Forward 100%
        input("move?")
        pi.set_PWM_dutycycle(R1_GPIO, 1 * 255)
        pi.set_PWM_dutycycle(L2_GPIO, 1 * 255)
        time.sleep(4)

        # Stop
        pi.set_PWM_dutycycle(R1_GPIO, 0 * 255)
        pi.set_PWM_dutycycle(L2_GPIO, 0 * 255)
        time.sleep(0.5)
except KeyboardInterrupt:
    print("終了します。PWMを停止します。")
    pi.set_PWM_dutycycle(R1_GPIO, 0)
    pi.set_PWM_dutycycle(R2_GPIO, 0)
    pi.set_PWM_dutycycle(L1_GPIO, 0)
    pi.set_PWM_dutycycle(L2_GPIO, 0)
    pi.stop()