from picamera2 import Picamera2
import cv2
import time

picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
conf = picam2.create_preview_configuration(main = {"size": (640, 480)}) # プレビューの設定
picam2.configure(conf)
picam2.start()
number = 0
try:
    while True:
        picam2.capture_file(f"cone_{number}.jpg") # 画像を撮影後cone_0,1,2.jpgという連番の名前で保存
        print("画像を保存しました")
        img = cv2.imread(f"cone_{number}.jpg") # 撮影した画像を読み込む
        cv2.imshow("Captured Image", img) # 画像を表示
        cv2.waitKey(0)
        time.sleep(1) # 5秒待機
        number += 1

except KeyboardInterrupt: #ctrl+cで安全に終了
    print("撮影を終了します")
    picam2.stop()
    cv2.destroyAllWindows() # ウィンドウを閉じる
    print("終了しました")
    exit