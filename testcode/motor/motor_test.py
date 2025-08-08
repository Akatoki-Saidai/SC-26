#引用元(https://www.radical-dreamer.com/programming/raspberry-pi-pwm-motordriver/)コミット
import pigpio
import time

R1_GPIO = 18
R2_GPIO = 12
L1_GPIO = 13
L2_GPIO = 19

pi = pigpio.pi()

# Stop
pi.hardware_PWM(R1_GPIO, 0, 0)
pi.hardware_PWM(R2_GPIO, 0, 0)
pi.hardware_PWM(L1_GPIO, 0, 0)
pi.hardware_PWM(L2_GPIO, 0, 0)
# time.sleep(30)

while True:
    # Forward 20% 
    # IN2 - HI75% : LO25%
    input("move?")
    pi.hardware_PWM(L2_GPIO, 200000, 1000000)
    # IN1 - HI100% : LO0%
    pi.hardware_PWM(R1_GPIO, 200000, 1000000)
    time.sleep(4)

    # Stop
    pi.hardware_PWM(L2_GPIO, 0, 0)
    pi.hardware_PWM(R1_GPIO, 0, 0)
    time.sleep(0.5)

pi.stop()