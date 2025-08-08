#引用元(https://www.radical-dreamer.com/programming/raspberry-pi-pwm-motordriver/)コミット
import pigpio
import time

IN1_GPIO = 18
IN2_GPIO = 19

pi = pigpio.pi()

while True:
    # Forward 20% 
    # IN2 - HI75% : LO25%
    pi.hardware_PWM(IN2_GPIO, 200000, 1000000)
    # IN1 - HI100% : LO0%
    pi.hardware_PWM(IN1_GPIO, 200000, 1000000)
    time.sleep(60)

    # Stop
    pi.hardware_PWM(IN2_GPIO, 0, 0)
    pi.hardware_PWM(IN1_GPIO, 0, 0)
    time.sleep(30)

pi.stop()