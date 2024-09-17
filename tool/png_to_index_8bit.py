# -*- coding:utf-8 -*-
"""
    png画像からインデックスカラー作成
    
    in:
        png: 24bit-color
    out:
        text: rgb565-palette, 4bit+4bit index
"""

from PIL import Image
import sys
import os
import glob

IMG_FOLDER_PATH = "./png/8/*"
SAVE_FILE_PATH = "./out/indexed-color_8bit.py"

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

# 透過色
trans_index = 0


def main():
    img_list = sorted(glob.glob(IMG_FOLDER_PATH))  # 画像リストを取得

    # 画像がない場合は終了
    if len(img_list) == 0:
        return print("No image File!")

    f = open(SAVE_FILE_PATH, "w")
    f.write('"""\n フルカラー(RGB 24bit)PNG から 256色インデックスカラー に変換 ver 1.00\n')
    f.write("1pixel を 1byte(8bit) のインデックスにします。 パレットは16色です。\n\n")

    # パレット出力
    f.write(" パレット:\n")
    pal = convert_pallet565()
    f.write(pal + '"""\n')

    file_count = 0
    for fn in img_list:
        file_count += 1
        print("Loading... " + fn)

        # 画像ファイル読み込み
        image = Image.open(fn)
        width, height = image.size
        name = os.path.splitext(os.path.basename(fn))[0]

        # 画像の色配列情報の文字列を取得して書き込む
        image_hex = outputColorPixel(width, height, image)
        f.write("{} = \\\n".format(name))
        f.write(image_hex)

        f.write("\n")

    # 最後の括弧とセミコロンを書き込んで閉じる
    f.write("\n")
    f.close()

    print("Saved: " + SAVE_FILE_PATH)


# フルカラーパレットから565のパレット生成
def convert_pallet565():
    result = "pallets565 = (\n"
    for col in pallet888:
        rgb565 = (
            (((col & 0xFF0000) >> 3) & 0x1F0000) >> 5
            | (((col & 0x00FF00) >> 2) & 0x003F00) >> 3
            | ((col & 0x0000FF) >> 3) & 0x00001F
        )
        result += "    0x{:0>4x},\n".format(rgb565)

    return result + ")\n"


# RGB値をインデクスカラー（256color）のテキストに変換する
# 1ピクセルを1バイトに変換
def conv(rgb):
    col = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
    index = pallet888.index(col)

    return "\\x{:0>2x}".format(index)


def outputColorPixel(width, height, image):
    result_str = ""

    px_step = 1
    for y in range(height):
        for x in range(0, width, px_step):
            #  行の先頭に空白を入れる
            if x == 0:
                result_str += "    b'"
            pixel = image.getpixel((x, y))

            # 1ピクセル インデックスカラーに変換
            result_str += conv(pixel)

            # 行末
            if x >= width - px_step:
                result_str += "' \\\n"

    return result_str[:-2] + "\n"


if __name__ == "__main__":
    main()
