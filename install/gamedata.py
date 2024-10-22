""" GRAVITRON PICO"""

__version__ = "1.0.1"
__author__ = "Choi Gyun 2024"

from micropython import const


# RBG565 パレット PICO-8風
palette565 = const(
    (
        0x0000,
        0x194A,
        0x792A,
        0x042A,
        0xAA86,
        0x5AA9,
        0xC618,
        0xFF9D,
        0xF809,
        0xFD00,
        0xFF64,
        0x0726,
        0x2D7F,
        0x83B3,
        0xFBB5,
        0xFE75,
    )
)

# コース用 565パレット 奥に行くほど明るくなる
c_pal0 = const(
    (
        0x0000,
        0x194A,
        0xFF9D,
        0xF809,
        0xFF64,
        0x0726,
        0xFBB5,
        0xFE75,
    )
)
c_pal1 = const(
    (
        0x0861,
        0x29CC,
        0xFFFE,
        0xF86B,
        0xFFC6,
        0x0F88,
        0xFC36,
        0xFED7,
    )
)
c_pal2 = const(
    (
        0x2945,
        0x428F,
        0xFFFF,
        0xF94E,
        0xFFE9,
        0x2FEB,
        0xFCFA,
        0xFFBA,
    )
)
c_pal3 = const(
    (
        0x528A,
        0x6BD4,
        0xFFFF,
        0xFA93,
        0xFFEE,
        0x57F0,
        0xFE3F,
        0xFFFF,
    )
)


# コース用パレットリスト
pal_tbl = const(
    (
        c_pal3,
        c_pal3,
        c_pal2,
        c_pal2,
        c_pal2,
        c_pal1,
        c_pal1,
        c_pal1,
        c_pal1,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
        c_pal0,
    )
)

# サイン・コサインテーブル
# 半周分
sin_tbl = const(
    (
        0,
        25,
        50,
        75,
        100,
        125,
        150,
        175,
        200,
        224,
        249,
        273,
        297,
        321,
        345,
        369,
        392,
        415,
        438,
        460,
        483,
        505,
        526,
        548,
        569,
        590,
        610,
        630,
        650,
        669,
        688,
        706,
        724,
        742,
        759,
        775,
        792,
        807,
        822,
        837,
        851,
        865,
        878,
        891,
        903,
        915,
        926,
        936,
        946,
        955,
        964,
        972,
        980,
        987,
        993,
        999,
        1004,
        1009,
        1013,
        1016,
        1019,
        1021,
        1023,
        1024,
        1024,
        1024,
        1023,
        1021,
        1019,
        1016,
        1013,
        1009,
        1004,
        999,
        993,
        987,
        980,
        972,
        964,
        955,
        946,
        936,
        926,
        915,
        903,
        891,
        878,
        865,
        851,
        837,
        822,
        807,
        792,
        775,
        759,
        742,
        724,
        706,
        688,
        669,
        650,
        630,
        610,
        590,
        569,
        548,
        526,
        505,
        483,
        460,
        438,
        415,
        392,
        369,
        345,
        321,
        297,
        273,
        249,
        224,
        200,
        175,
        150,
        125,
        100,
        75,
        50,
        25,
    )
)

cos_tbl = const(
    (
        1024,
        1024,
        1023,
        1021,
        1019,
        1016,
        1013,
        1009,
        1004,
        999,
        993,
        987,
        980,
        972,
        964,
        955,
        946,
        936,
        926,
        915,
        903,
        891,
        878,
        865,
        851,
        837,
        822,
        807,
        792,
        775,
        759,
        742,
        724,
        706,
        688,
        669,
        650,
        630,
        610,
        590,
        569,
        548,
        526,
        505,
        483,
        460,
        438,
        415,
        392,
        369,
        345,
        321,
        297,
        273,
        249,
        224,
        200,
        175,
        150,
        125,
        100,
        75,
        50,
        25,
        0,
        -25,
        -50,
        -75,
        -100,
        -125,
        -150,
        -175,
        -200,
        -224,
        -249,
        -273,
        -297,
        -321,
        -345,
        -369,
        -392,
        -415,
        -438,
        -460,
        -483,
        -505,
        -526,
        -548,
        -569,
        -590,
        -610,
        -630,
        -650,
        -669,
        -688,
        -706,
        -724,
        -742,
        -759,
        -775,
        -792,
        -807,
        -822,
        -837,
        -851,
        -865,
        -878,
        -891,
        -903,
        -915,
        -926,
        -936,
        -946,
        -955,
        -964,
        -972,
        -980,
        -987,
        -993,
        -999,
        -1004,
        -1009,
        -1013,
        -1016,
        -1019,
        -1021,
        -1023,
        -1024,
    )
)

# 奥行きの拡縮
z_scale_tbl = const(
    (
        171,
        110,
        79,
        59,
        47,
        37,
        30,
        25,
        21,
        17,
        14,
        12,
        9,
        8,
        6,
        4,
        3,
        2,
        1,
        0,
    )
)

# 水平方向の拡縮（8bit固定小数）
h_scale_tbl = const(
    (
        64,
        94,
        125,
        155,
        185,
        216,
        246,
        276,
        307,
        337,
        367,
        398,
        428,
        458,
        489,
        519,
        549,
        580,
        610,
        640,
    )
)

# arc tan 3 * 3
# ざっくりした方向
atan_tbl = const(
    (
        -1,  # エラー
        0,
        0,
        0,
        64,
        32,
        19,
        13,
        64,
        45,
        32,
        24,
        64,
        51,
        40,
        32,
    )
)
