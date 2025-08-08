import pigpio
import time

# GPIOピン番号（BCM番号）
LED1_PIN = 27
LED2_PIN = 22

# pigpioインスタンスを作成
pi = pigpio.pi()

# pigpioデーモンに接続できているか確認
if not pi.connected:
    print("pigpioデーモンに接続できません。pigpiodが起動しているか確認してください。")
    exit()

# 出力モードに設定
pi.set_mode(LED1_PIN, pigpio.OUTPUT)
pi.set_mode(LED2_PIN, pigpio.OUTPUT)

try:
    print("LEDを3回点滅させます...")
    for _ in range(3):
        pi.write(LED1_PIN, 1)  # ON
        time.sleep(1)
        pi.write(LED1_PIN, 0)  # OFF
        time.sleep(1)
    for _ in range(3):
        pi.write(LED2_PIN, 1)  # ON
        time.sleep(1)
        pi.write(LED2_PIN, 0)  # OFF
        time.sleep(1)

    print("終了します。")
finally:
    # LEDを消して、pigpioインスタンスを解放
    pi.write(LED1_PIN, 0)
    pi.write(LED2_PIN, 0)
    pi.stop()
