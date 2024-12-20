# -*- coding:utf-8 -*-
"""
    png画像からコースデータ作成
    
    in:
        png: 64 * 32 pixel 24bit-color
    out:
        bin: 8bit index
"""

from PIL import Image
import os
import glob

IMG_FOLDER_PATH = "./png/course/*"  # pngのあるフォルダ
SAVE_FILE_PATH = "./out/"  # 書き出し先

# フルカラーパレット
# PICO-8 16色中8色
palette888 = (
    0x000000,
    0x1D2B53,
    0xFFF1E8,
    0xFF004D,
    0xFFEC27,
    0x00E436,
    0xFF77A8,
    0xFFCCAA,
)

# 手動で調整したパレット
palette888_2 = (
    0x1E1E1E,
    0x3B4971,
    0xFFFFFC,
    0xFF1E6B,
    0xFFFF3B,
    0x0AEE40,
    0xFF8BBC,
    0xFFE0BE,
)
palette888_3 = (
    0x3C3C3C,
    0x59678F,
    0xFFFFFF,
    0xFF327F,
    0xFFFF4F,
    0x14F84A,
    0xFF9FD0,
    0xFFF4D2,
)
palette888_4 = (
    0x909090,
    0x7785AD,
    0xFFFFFF,
    0xFF4693,
    0xFFFF63,
    0x1EFF54,
    0xFFB3E4,
    0xFFFFE6,
)

pals = (palette888, palette888_2, palette888_3, palette888_4)

# 一律で自動調整
pal_vals = (0, 20, 40, 60)


def main():
    print("フルカラー(RGB 888)PNG から コースデータ を作成 ver 1.00\n")
    print("画像サイズは 64pixel * 32pixel です。")
    print(
        "1pixel を 1byte(8bit) のインデックスにします。 パレットはRGB565で出力します。 \n\n"
    )

    ### コース用 565パレット作成
    # 手動で調整したパレット
    conv_palette565()
    # 自動で調整したパレット
    # create_palette565()

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
        f = open(SAVE_FILE_PATH + name + ".dat", "wb")
        image_bin = outputColorPixel(width, height, image)
        f.write(image_bin)
        f.close()
        print("Saved: " + SAVE_FILE_PATH + name + ".dat")


# RGB値をインデクスカラー（16color）のバイナリに変換する
# 1ピクセルを1バイトに変換
def conv(rgb):
    col = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]

    return palette888.index(col)


def outputColorPixel(width, height, image):
    result = bytearray()

    for y in range(height):
        for x in range(width):
            # インデックスカラーに変換
            pixel = image.getpixel((x, y))
            result.append(conv(pixel))

    return result


def conv_palette565():
    f = open(SAVE_FILE_PATH + "conv_pals565.txt", "w")
    print("processing... palette RGB888 to RGB565")

    for i, pal in enumerate(pals):
        f.write("# converte palette RGB565 {:0>2d}\n".format(i))

        for p in pal:

            r5 = (p >> 16) & 0xFF
            r5 >>= 3

            g6 = (p >> 8) & 0xFF
            g6 >>= 2

            b5 = p & 0xFF
            b5 >>= 3

            rgb565 = (r5 << 11) | (g6 << 5) | b5
            f.write("0x{:0>4x},\n".format(rgb565))

        f.write("\n")
    f.close()
    print("saved: " + SAVE_FILE_PATH + "conv_pals565.txt")


# コースデータ用のパレット作成
def create_palette565():
    f = open(SAVE_FILE_PATH + "create_pals565.txt", "w")
    print("processing... palette RGB888 to RGB565")

    for i, v in enumerate(pal_vals):
        f.write("# create palette RGB565 {:0>2d}\n".format(i))

        for p in palette888:
            r5 = min(((p >> 16) & 0xFF) + v, 255)
            r5 >>= 3

            g6 = min(((p >> 8) & 0xFF) + v, 255)
            g6 >>= 2

            b5 = min((p & 0xFF) + v, 255)
            b5 >>= 3

            rgb565 = (r5 << 11) | (g6 << 5) | b5
            f.write("0x{:0>4x},\n".format(rgb565))

        f.write("\n")

    f.close()
    print("saved: " + SAVE_FILE_PATH + "create_pals565.txt")


if __name__ == "__main__":
    main()
