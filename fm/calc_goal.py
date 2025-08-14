import math
import numpy as np


def calc_goal(data):
    """機体及びゴールの緯度経度から，ゴールの向きと距離を計算
    
    goal_angleはゴールが機体の前だったら0/360, 右だったら90, 後だったら180, 左だったら270
    """

    goal_latitude, goal_longitude, now_latitude, now_longitude, mag = data["goal_lat"], data["goal_lon"], data["lat"], data["lon"], data["mag"]

    if goal_latitude is None or goal_longitude is None or now_latitude is None or now_longitude is None or mag[0] is None:
        return
    
    #1.ゴールの緯度経度をCanSat中心のxy座標で表す。
    goal_xy = _calc_xy(goal_latitude,goal_longitude,now_latitude,now_longitude)

    #2.緯度経度→→→ゴールと機体の距離を求める
    distance = float(np.sqrt((goal_xy[1])**2 + (goal_xy[0])**2))

    #3.機体の正面と北の向きの関係＋北の向きとゴールの向きの関係→→→機体の正面とゴールの向きの関係を求める
    #やってることとしては東西南北の基底→CanSatの基底に座標変換するために回転行列を使ってる感じ
    #north_angle_rad - math.piは、平面直交座標のx軸(西)と北の向きを表すときのx軸(機体の正面)が何度ずれているかを表している
    north_angle_rad = np.arctan2(mag[0], mag[1])  ##############<==##########要確認#############################
    cansat_to_goal = _rotation_clockwise_xy(goal_xy,north_angle_rad)
    
    #4.CanSatの正面とゴールの向きの関係を角度で表現している(radian→degreeの変換も行う)。ただし、角度の定義域は(0<=degree<=360)。正面は0と360で真後ろが180。
    cansat_to_goal_angle = np.arctan2(cansat_to_goal[1],cansat_to_goal[0])
    cansat_to_goal_angle_degree = float(math.degrees(cansat_to_goal_angle) + 180)

    data["goal_distance"] = distance
    data["goal_angle"] = cansat_to_goal_angle_degree


def _calc_xy(phi_deg, lambda_deg, phi0_deg, lambda0_deg):
    """ 緯度経度を平面直角座標に変換する
    - input:
        (phi_deg, lambda_deg): 変換したい緯度・経度[度]（分・秒でなく小数であることに注意）
        (phi0_deg, lambda0_deg): 平面直角座標系原点の緯度・経度[度]（分・秒でなく小数であることに注意）
    - output:
        x: 変換後の平面直角座標[m]
        y: 変換後の平面直角座標[m]
    """
    # 緯度経度・平面直角座標系原点をラジアンに直す
    phi_rad = np.deg2rad(phi_deg)
    lambda_rad = np.deg2rad(lambda_deg)
    phi0_rad = np.deg2rad(phi0_deg)
    lambda0_rad = np.deg2rad(lambda0_deg)

    # 補助関数
    def A_array(n):
        A0 = 1 + (n**2)/4. + (n**4)/64.
        A1 = -     (3./2)*( n - (n**3)/8. - (n**5)/64. ) 
        A2 =     (15./16)*( n**2 - (n**4)/4. )
        A3 = -   (35./48)*( n**3 - (5./16)*(n**5) )
        A4 =   (315./512)*( n**4 )
        A5 = -(693./1280)*( n**5 )
        return np.array([A0, A1, A2, A3, A4, A5])

    def alpha_array(n):
        a0 = np.nan # dummy
        a1 = (1./2)*n - (2./3)*(n**2) + (5./16)*(n**3) + (41./180)*(n**4) - (127./288)*(n**5)
        a2 = (13./48)*(n**2) - (3./5)*(n**3) + (557./1440)*(n**4) + (281./630)*(n**5)
        a3 = (61./240)*(n**3) - (103./140)*(n**4) + (15061./26880)*(n**5)
        a4 = (49561./161280)*(n**4) - (179./168)*(n**5)
        a5 = (34729./80640)*(n**5)
        return np.array([a0, a1, a2, a3, a4, a5])

    # 定数 (a, F: 世界測地系-測地基準系1980（GRS80）楕円体)
    M0 = 0.9999 
    A = 6378137.
    F = 298.257222101

    # (1) n, A_i, alpha_iの計算
    n = 1.0 / (2*F - 1)
    A_array = A_array(n)
    alpha_array = alpha_array(n)

    # (2), S, Aの計算
    A_ = ( (M0*A)/(1.+n) )*A_array[0] # [m]
    S_ = ( (M0*A)/(1.+n) )*( A_array[0]*phi0_rad + np.dot(A_array[1:], np.sin(2*phi0_rad*np.arange(1,6))) ) # [m]

    # (3) lambda_c, lambda_sの計算
    lambda_c = np.cos(lambda_rad - lambda0_rad)
    lambda_s = np.sin(lambda_rad - lambda0_rad)

    # (4) t, t_の計算
    t = np.sinh( np.arctanh(np.sin(phi_rad)) - ((2*np.sqrt(n)) / (1+n))*np.arctanh(((2*np.sqrt(n)) / (1+n)) * np.sin(phi_rad)) )
    t_ = np.sqrt(1 + t*t)

    # (5) xi', eta'の計算
    xi2  = np.arctan(t / lambda_c) # [rad]
    eta2 = np.arctanh(lambda_s / t_)

    # (6) x, yの計算
    x = A_ * (xi2 + np.sum(np.multiply(alpha_array[1:],
                                       np.multiply(np.sin(2*xi2*np.arange(1,6)),
                                                   np.cosh(2*eta2*np.arange(1,6)))))) - S_ # [m]
    y = A_ * (eta2 + np.sum(np.multiply(alpha_array[1:],
                                        np.multiply(np.cos(2*xi2*np.arange(1,6)),
                                                    np.sinh(2*eta2*np.arange(1,6)))))) # [m]
    # return
    return (x, y)  # [m]


def _rotation_clockwise_xy(vec_xy,radian):
    """平面直角座標系におけるゴール座標と機体からみた北の向きから，機体の座標系におけるゴール座標を計算"""
    sin_rad = np.sin(radian)
    cos_rad = np.cos(radian)
    new_vector_x = vec_xy[0]*cos_rad + vec_xy[1]*sin_rad
    new_vector_y = vec_xy[1]*cos_rad - vec_xy[0]*sin_rad
    new_vector = (new_vector_x,new_vector_y)

    return new_vector