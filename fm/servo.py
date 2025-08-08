# このファイルは一時的にsc26のtestcode内のファイルをコピーしたものです

# https://0918.jp/wp/post-2658/ より引用
#!/usr/bin/python
import pigpio   # pigpioモジュールの読み込み
import time     # timeモジュールの読bみ込み

gpio_pwm = 18   # PWMピンのGPIO番号を定義

pig = pigpio.pi()
pig.set_mode(gpio_pwm, pigpio.OUTPUT)
                  # PWMピンを出力に設定
try:
  while True:
    pig.hardware_PWM(gpio_pwm, 50, 25000)
                      # PWM周波数を50Hz,dutyを2.5%(0.5mS)
    time.sleep(1)
    pig.hardware_PWM(gpio_pwm, 50, 50000)
                      # PWM周波数を50Hz,dutyを5%(2.5mS)
    time.sleep(1)
    pig.hardware_PWM(gpio_pwm, 50, 72500)
                      # PWM周波数を50Hz,dutyを7.25%(1.45mS)
    time.sleep(1)
    pig.hardware_PWM(gpio_pwm, 50, 100000)
                      # PWM周波数を50Hz,dutyを10%(2mS)
    time.sleep(1)
    pig.hardware_PWM(gpio_pwm, 50, 120000)
                      # PWM周波数を50Hz,dutyを12%(2.4mS)
    time.sleep(1)
except KeyboardInterrupt:
  pig.set_mode(gpio_pwm, pigpio.INPUT)
  pig.stop()