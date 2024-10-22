# -*- coding:utf-8 -*-
"""
    png画像からインデックスカラー作成

    usage:
        png_to_dat.py [dir]

        [dir] 画像ファイルのあるフォルダ
        フォルダ名.dat として出力します
    
    in:
        png: 24bit-color
    out:
        [0] ファイル数
        ---------------------------
        [1] タイプ 0:スプライト 1:ビットマップ
        [2] width
        [3] height
        [3] 読み込みサイズ
        [4..] 画像データ
                スプライト: 2px = 1byte (4bit + 4bit)
                ビットマップ: 1px = 2bytes (16bit color) little-endian
        ---------------------------
        * 画像分繰り返し

"""

from PIL import Image
import sys
import os
import glob

IMG_FOLDER_PATH = "./png/"
SAVE_FILE_PATH = "./out/"

# フルカラーパレット
# PICO-8 16色
palette888 = (
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
)

# 透過色
trans_index = 0


def main():
    args = sys.argv
    if len(args) <= 1:
        print("Specify an image folder.")
        exit()

    img_list = sorted(glob.glob(IMG_FOLDER_PATH + args[1] + "/*"))  # 画像リストを取得

    # 画像がない場合は終了
    if len(img_list) == 0:
        return print("No image File!")

    print('""" フルカラー(RGB 24bit)PNG から ゲーム用バイナリデータ に変換 ver 1.00')

    file_count = 0
    f = open(SAVE_FILE_PATH + args[1] + ".dat", "wb")
    # ファイル数
    f.write(len(img_list).to_bytes(1, "big"))

    for fn in img_list:
        file_count += 1
        print("Loading... " + fn)

        # 画像ファイル読み込み
        image = Image.open(fn)
        width, height = image.size
        name = os.path.splitext(os.path.basename(fn))[0]

        # タイプ
        if "_sp_" in fn:
            # スプライト用
            img_type = b"\x00"
            f.write(img_type)
            # サイズ
            f.write(width.to_bytes(1, "big"))
            f.write(height.to_bytes(1, "big"))
            size = (width // 2) * height
            f.write(size.to_bytes(2, "big"))
            # 画像の色配列情報のバイナリを取得して書き込む
            image_bin = outputColorPixel(width, height, image)
            f.write(image_bin)
        else:
            img_type = b"\x01"
            f.write(img_type)
            # サイズ
            f.write(width.to_bytes(1, "big"))
            f.write(height.to_bytes(1, "big"))
            size = width * height * 2 # 1px 16bit
            f.write(size.to_bytes(2, "big"))
            # 画像の色配列情報のバイナリを取得して書き込む
            image_bin = outputColorPixel565(width, height, image)
            f.write(image_bin)
    
    f.close()
    print("Saved: " + SAVE_FILE_PATH + args[1] + ".dat")


# RGB値をインデクスカラー 4bit + 4bit のバイナリに変換する
# 2ピクセルを1バイトに変換
def conv4(rgb):
    col = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    index = palette888.index(col)
    out = index

    col = (rgb[3] << 16) | (rgb[4] << 8) | rgb[5]
    index = palette888.index(col)
    out |= index << 4

    return out


# RGB値を16bit のバイナリに変換する
# 1ピクセルを RGB565 2バイトに変換
def conv565(rgb):
    r5 = rgb[0] >> 3
    g6 = rgb[1] >> 2
    b5 = rgb[2] >> 3
    out = (r5 << 11) | (g6 << 5) | b5

    return out


def outputColorPixel(width, height, image):
    result = bytearray()

    step = 2
    for y in range(height):
        for x in range(0, width, step):
            pixel = image.getpixel((x, y))
            pixel += image.getpixel((x + 1, y))

            # 2ピクセル インデックスカラーに変換
            result.append(conv4(pixel))

    return result


def outputColorPixel565(width, height, image):
    result = bytearray()

    for y in range(height):
        for x in range(width):
            pixel = image.getpixel((x, y))

            # 1ピクセル RGB565に変換
            rgb565 = conv565(pixel)
            result.append(rgb565 & 0xFF)
            result.append(rgb565 >> 8)


    return result


if __name__ == "__main__":
    main()
