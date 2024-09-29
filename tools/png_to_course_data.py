# -*- coding:utf-8 -*-
"""
    png画像からコースデータ作成
    
    in:
        png: 64 * 32 pixel 24bit-color
    out:
        bin: 8bit index
"""

from PIL import Image
import sys
import os
import glob

IMG_FOLDER_PATH = "./png/course/*" # pngのあるフォルダ
SAVE_FILE_PATH = "./out/" # 書き出し先

# フルカラーパレット
# PICO-8 16色
pallet888 = [
    0x000000,
    0x1D2B53,
    0x7E2553,
    0x008751,
    0xAB5236,
    0x5F574F,
    0xC2C3C7,
    0xFFF1E8,
    0xFF004D,
    0xFFA300,
    0xFFEC27,
    0x00E436,
    0x29ADFF,
    0x83769C,
    0xFF77A8,
    0xFFCCAA,
]

def main():
    print("フルカラー(RGB 24bit)PNG から コースデータ を作成 ver 1.00\n")
    print("画像サイズは 64pixel * 32pixel です。")
    print("1pixel を 1byte(8bit) のインデックスにします。 パレットは16色です。\n\n")


    img_list = sorted(glob.glob(IMG_FOLDER_PATH))  # 画像リストを取得

    # 画像がない場合は終了
    if len(img_list) == 0:
        return print("No image File!")

    for fn in img_list:        
        print("processing... " + fn)

        # 画像ファイル読み込み
        image = Image.open(fn)
        width, height = image.size
        name = os.path.splitext(os.path.basename(fn))[0]

        # 画像の色配列情報のバイナリを取得して書き込む
        f = open(SAVE_FILE_PATH + name + ".dat", 'wb')
        image_bin = outputColorPixel(width, height, image)
        f.write(image_bin)
        f.close()
        print("Saved: " + SAVE_FILE_PATH + name + ".dat")


# RGB値をインデクスカラー（16color）のバイナリに変換する
# 1ピクセルを1バイトに変換
def conv(rgb):
    col = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    index = pallet888.index(col)

    return index


def outputColorPixel(width, height, image):
    result = bytearray()

    for y in range(height):
        for x in range(width):
            # インデックスカラーに変換
            pixel = image.getpixel((x, y))
            result.append(conv(pixel))

    return result


if __name__ == "__main__":
    main()
