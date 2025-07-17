import cv2
import numpy as np
import matplotlib.pyplot as plt

#赤色は色相範囲において2つの領域またぐ（174～6で180をまたぐため174～180，0~6で設定）
low_color1 = np.array([0, 50, 50])  # 各最小値を指定
high_color1 = np.array([6, 255, 255])  # 各最大値を指定
low_color2 = np.array([174, 50, 50]) #第2領域の各最小値を指定
high_color2 = np.array([180, 255, 255])  # 第2領域の各最大値を指定

def detect_cone(img_name):#仮引数をimg_nameに設定（後に引数にカラーコーンの引数を渡す）
    img = cv2.imread(img_name)#画像を読み込む
    
    img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV) # RGB => YUV(YCbCr)
    clahe = cv2.createCLAHE(clipLimit = 2.0, tileGridSize = (8, 8)) # claheオブジェクトを生成
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0]) # 輝度にのみヒストグラム平坦化
    img = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR) # YUV => RGB
    
    img_blur = cv2.blur(img, (15, 15)) # 平滑化フィルタを適用
     
    hsv = cv2.cvtColor(img_blur, cv2.COLOR_BGR2HSV) # BGRからHSVに変換
    
    bin_img1 = cv2.inRange(hsv, low_color1, high_color1) # マスクを作成
    bin_img2 = cv2.inRange(hsv, low_color2, high_color2)
    mask = bin_img1 + bin_img2 # 必要ならマスクを足し合わせる
    masked_img = cv2.bitwise_and(img_blur, img_blur, mask= mask) # 元画像から特定の色を抽出
    
    out_img = masked_img
    num_labels, label_img, stats, centroids = cv2.connectedComponentsWithStats(mask) # 連結成分でラベリングする
    # 背景のラベルを削除
    num_labels = num_labels - 1
    stats = np.delete(stats, 0, 0)
    centroids = np.delete(centroids, 0, 0)

    if num_labels >= 1: # ラベルの有無で場合分け
        max_index = np.argmax(stats[:, 4]) # 最大面積のインデックスを取り出す
        # 以下最大面積のラベルについて考える
        x = stats[max_index][0]
        y = stats[max_index][1]
        w = stats[max_index][2]
        h = stats[max_index][3]
        s = stats[max_index][4]
        h1, w1 = img.shape[:2] # 画像の高さと幅を取得
        total_pixel = h1 * w1 # 画像の総ピクセル数を計算
        percentage_image = (s / total_pixel) * 100 # 画像中のコーンの占有率を計算
        mx = int(centroids[max_index][0]) # 重心のX座標
        my = int(centroids[max_index][1]) # 重心のY座標
        cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 255)) # ラベルを四角で囲む
        cv2.putText(img, "%d,%d"%(mx, my), (x-15, y+h+15), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 0)) # 重心を表示
        cv2.putText(img, "%d"%(percentage_image), (x, y+h+30), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 0)) # 面積の占有率を表示
    
    cv2.imwrite("img.jpg", img) # 書き出す
    if percentage_image > 10:
        print("ゴールしました")
        return True # ゴールした場合にはTrueを返す
    if num_labels < 1:
        print("目標物が見当たりません！！")
    
    
if __name__ == '__main__':
    detect_cone("cone_1.jpg") # ファイル名を入力"