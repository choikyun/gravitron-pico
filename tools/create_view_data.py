"""パースがついて見えるように台形に座標変換"""

# ビューの高さ Y座標
vh = 20
v = vh - 1
# 初期スケール
s = 0.1
# 固定小数8bit
fix = 256

for _ in range(vh):
    z = (v - (v / s))
    x = s * 2.5 * fix
    s += 0.0474

    # Z方向の拡縮, X方向の拡縮
    print(round(z) , round(x))
