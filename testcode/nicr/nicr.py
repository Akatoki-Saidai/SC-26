import pigpio
import time

if __name__ == "__main__":
    NiCr_GPIO = 6

    pi = pigpio.pi()

    # Stop
    pi.set_mode(NiCr_GPIO, pigpio.OUTPUT)
    pi.write(NiCr_GPIO, 0)  # 初期状態はOFF

    try:
        input("NiCrをONにしますか？ (y/n): ")
        user_input = input().strip().lower()
        if user_input == 'y':
            print("NiCrをONにします。")
            pi.write(NiCr_GPIO, 1)  # NiCrをONにする
            time.sleep(5)  # 5秒間ONにする
            pi.write(NiCr_GPIO, 0)  # NiCrをOFFにする
            print("NiCrをOFFにしました。")
        else:
            print("NiCrをONにしませんでした。")
            
    except KeyboardInterrupt:
        print("終了します")
        pi.write(NiCr_GPIO, 0)  # NiCrをOFFにする
        pi.stop()