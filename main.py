"""GRAVITRON PICO"""

__version__ = "1.0.0"
__author__ = "Choi Gyun 2024"

# import _thread
import random
import machine

import ease
import gamedata as dat
import picogamelib as gl
import picolcd114 as lcd
import framebuf as buf


### 疑似3D表示
_VIEW_W = const(59)  # ビューサイズ
_VIEW_H = const(20)
_VIEW_RATIO_W = const(4)  # ビューとスクリーンの拡大比率 1px=4x3dot
_VIEW_RATIO_H = const(3)
_VIEW_X = const(-29)  # ビュー開始座標 -29 ... 29 (59)
_VIEW_X_END = const(29)

_FIX = const(10)  # 固定小数の桁 10bit
_MAX_DIR = const(256)  # 方向 最大256°

_SCREEN_X = const(1)  # スクリーン描画 開始座標
_SCREEN_Y = const(75)

_SCREEN_W = const(238)  # スクリーンサイズ
_SCREEN_H = const(135)

_PIXEL_W = const(_VIEW_RATIO_W)  # 1ピクセルの大きさ
_PIXEL_H = const(_VIEW_RATIO_H)

_COURSE_RATIO = const(4)  # コースデータ 1px=16px
_COURSE_DATA_SIZE = const(32)  # コースデータの大きさ
_COURSE_W = const(_COURSE_DATA_SIZE << _COURSE_RATIO)  # コースの大きさ（論理値）
_COURSE_H = const(_COURSE_W)
_COURSE_DATA_FIX = const(5)  # コースデータ補正 32倍

_COL_OUT = const(1)  # コース外

### ゲームバランス調整
_ACC_LIMIT = const(32)  # マックス加速度
_ACC_FIX = const(5)  # 加速度 固定小数桁 5bit


### オブジェクトのサイズ
_OBJ_W = const(32)
_OBJ_H = const(32)

### 自機
_SHIP_X = const(103)  # 自機座標
_SHIP_Y = const(103)

### スコア
_SCORE_DIGIT = const(6)
_LINE_DIGIT = const(4)

### メッセージ
_READY_DURATION = const(30 * 2)
_READY_INTERVAL = const(6)

### キャラクタ
_CHR_SHIP = const(0)

### ビットマップ
_BMP_TITLE = const(0)
_BMP_OVER = const(1)
_BMP_HI = const(2)
_BMP_SCORE = const(3)
_BMP_LINES = const(4)
_BMP_INFO_BRIGHT = const(5)
_BMP_READY = const(6)
_BMP_NUM = const(8)
_BMP_CREDIT = const(18)
_BMP_EX = const(19)

### ポーズ画面
_SCORE_W = const(84)
_SCORE_H = const(20)
_HI_W = const(28)
_HI_H = const(20)
_LINES_W = const(76)
_LINES_H = const(20)
_INFO_BRIGHT_W = const(44)
_INFO_BRIGHT_H = const(24)

### 数字
_NUM_W = const(16)
_NUM_H = const(16)

### ゲームオーバー
_OVER_W = const(152)
_OVER_H = const(24)

### タイトル
_TITLE_W = const(240)
_TITLE_H = const(70)
_CREDIT_W = const(144)
_CREDIT_H = const(10)

### 重なり順
_VIEW_Z = const(10)
_SHIP_Z = const(100)

# イベント

# セーブデータ
_FILENAME = const("gv100.json")

# クロック 250MHz
machine.freq(250000000)


class MainScene(gl.Scene):
    """メイン"""

    def __init__(self, name, key):
        # イベントマネージャ
        event = gl.EventManager()
        # ステージ（塗りつぶし無し）
        stage = gl.Stage(
            self, event, "stage", 0, 0, 0, lcd.LCD_W, lcd.LCD_H, gl.trans_color
        )
        super().__init__(name, event, stage, key)

        # イベントリスナー
        # self.event.add_listner([_EV_GAMEOVER, self, True])

        # スプライト作成
        # 自機
        self.ship = Ship(
            self.stage, _CHR_SHIP, "ship", _SHIP_X, _SHIP_Y, _SHIP_Z, _OBJ_W, _OBJ_H
        )
        # ビュー
        self.view = View(self.stage, 0, "view", 0, 0, _VIEW_Z, _VIEW_W, _VIEW_H)

    def enter(self):
        """ゲームの初期化処理"""
        # イベントのクリア
        self.event.clear_queue()
        # 全てのリスナーを有効
        self.event.enable_listners()

        self.gameover = False

        super().enter()

    def action(self):
        """フレーム毎のアクション 30FPS"""
        super().action()


class Ship(gl.Sprite):
    """自機クラス"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        # イベントリスナー登録
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])

    def enter(self):
        super().enter()

    def action(self):
        super().action()
        # 点滅

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""


class View(gl.Sprite):
    """コースの3D表示 スプライトとして処理する"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        # イベントリスナー登録
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])

        # ビュー初期化
        self.init_view()

        # 描画ピクセル初期化
        self.init_pixels()
        # 背景
        self.init_bg()

    def init_view(self):
        """ビュー初期化"""

        self.vx = 480 << _ACC_FIX  # ビューの原点 XZ座標
        self.vz = 256 << _ACC_FIX
        self.vx_acc = 0  # ビュー XZ加速度
        self.vz_acc = 0
        self.speed = 0  # 移動速度（アクセル）
        self.dir = 191 << _ACC_FIX  # 方向（初期値 上）
        self.dir_acc = 0  # 方向 加速度

        # 別スレッドで共有する変数をセット
        gl.lock.acquire()
        self.thread_vals[0] = self.vx
        self.thread_vals[1] = self.vy
        self.thread_vals[2] = self.dir

        # スクリーン ピクセルのインデックスが入る
        self.screen = bytearray(_VIEW_W * _VIEW_H)
        gl.lock.release()

    def init_pixels(self):
        """画面に描画するピクセルの初期化"""

        self.pixels = []
        for p in dat.palette565:
            b = buf.FrameBuffer(
                bytearray(_PIXEL_W * _PIXEL_H * 2), _PIXEL_W, _PIXEL_H, buf.RGB565
            )
            b.fill(p)
            self.pixels.append(b)

    def init_bg(self):
        """背景"""

        # 手抜き LINEで表現
        gl.lcd.rect(1, 45, 237, 12, 0x194A, True)
        gl.lcd.rect(1, 57, 237, 10, 0x83B3, True)
        gl.lcd.rect(1, 67, 237, 8, 0x2D7F, True)

    def enter(self):
        super().enter()

    def action(self):
        super().action()

    def thread_action(self):
        """別スレッド（コア）で実行されるアクション"""
        super().thread_action()

        if len(self.thread_vals) == 0:
            return

        vx = self.thread_vals[0] >> _ACC_FIX  # ビューの原点 xz座標
        vz = self.thread_vals[1] >> _ACC_FIX
        d = self.thread_vals[3] >> _ACC_FIX  # 回転方向

        pixs = self.pixels
        field = dat.course1

        cos = dat.cos_tbl[d]
        sin = dat.sin_tbl[d]

        # 座標変換
        i = 0
        ix = 0
        for z in dat.z_index:
            z_cos = z * cos  # cos, sin 先に計算
            z_sin = z * sin
            sx = dat.x_ratio[ix]  # X方向の拡大率
            for x in range(_VIEW_X, _VIEW_X_END):
                _x = (x << 8) // sx
                # 回転
                px = (_x * cos - z_sin) >> _FIX
                pz = (_x * sin + z_cos) >> _FIX

                px = (px + vx) >> _COURSE_RATIO  # 論理座標をコースデータの座標に変換
                pz = (pz + vz) >> _COURSE_RATIO

                col = _COL_OUT
                if (
                    px >= 0
                    and px < _COURSE_DATA_SIZE
                    and pz >= 0
                    and pz < _COURSE_DATA_SIZE
                ):
                    # コースデータからピクセルを取得
                    col = field[px + (pz << _COURSE_DATA_FIX)]

                # ピクセル書き込み
                self.screen[i] = col
                i += 1
            ix += 1

    def show(self, frame_buffer, x, y):
        """スクリーン（ピクセルのマップ）をフレームバッファに描画"""

        i = 0
        for y in range(_SCREEN_Y, _SCREEN_H, _PIXEL_H):
            for x in range(_SCREEN_X, _SCREEN_W, _PIXEL_W):
                col = self.screen[i]
                # ピクセル書き込み
                frame_buffer.blit(pixs[col], x, y)
                i += 1

    def ev_enter_frame(self, type, sender, key):
        """イベント:毎フレーム"""

        # 移動
        self.move(key)

    def move(self, key):
        """自機移動"""

        # 左右移動（回転）
        if key.repeat & lcd.KEY_RIGHT:
            self.dir_acc += 16
            if self.dir_acc >= _ACC_LIMIT:
                self.dir_acc = _ACC_LIMIT
            self.dir = self.dir + self.dir_acc
        elif key.repeat & lcd.KEY_LEFT:
            self.dir_acc -= 16
            if self.dir_acc <= -_ACC_LIMIT:
                self.dir_acc = -_ACC_LIMIT
            self.dir = self.dir + self.dir_acc
        else:
            self.dir_acc //= 2  # 原則

        # アクセル
        if key.repeat & lcd.KEY_A:
            self.speed += 8
            if self.speed >= _ACC_LIMIT:
                self.speed = _ACC_LIMIT
        else:
            self.speed //= 2

        # 加速
        d = self.dir >> _ACC_FIX
        s = self.speed >> _ACC_FIX
        self.vx_acc = dat.cos_tbl[d] * s  # スピードからXZ成分の加速度
        self.vz_acc = dat.sin_tbl[d] * s

        self.vx += self.vx_acc
        self.vz += self.vz_acc


class BlinkMessage(gl.BitmapSprite):
    """点滅メッセージ表示
    一定期間で消える

    Attributes:
        duration (int): 表示時間
        interval (int): 点滅間隔 0の時は点滅しない
    """

    def __init__(self, parent, bitmap, duration, interval, name, x, y, z, w, h):
        super().__init__(parent, bitmap, name, x, y, z, w, h)
        self.duration = duration
        self.interval = interval

    def enter(self):
        return super().enter()

    def leave(self):
        self.visible = False
        super().leave()

    def action(self):
        super().action()

        if self.interval != 0 and self.duration % self.interval == 0:
            self.visible = not self.visible

        # 一定時間で消える
        self.duration -= 1
        if self.duration == 0:
            self.leave()


# インデックスカラースプライト
chr_data = [
    (dat.ship_0, _OBJ_W, _OBJ_H),  # 自機
]
# イメージバッファ生成
gl.create_image_buffers(dat.palette565, chr_data)

# ビットマップスプライト
bmp_data = []

# ステータスをロード
game_status = gl.load_status(_FILENAME)

if game_status is None:
    # デフォルト
    game_status = {
        "mode": 0,
        "score": 0,
        "hi_ex": 0,
        "hi": 0,
        "time": 0,
        "brightness": 2,
    }
    gl.save_status(game_status, _FILENAME)

# LCDの明るさ
gl.lcd.brightness(game_status["brightness"])

# キー入力 シーン共通
key = lcd.InputKey()

# 各シーンの作成
main = MainScene("main", key)
scenes = [main]

# 描画スレッド
# _thread.start_new_thread(gl.thread_send_buf_to_lcd, ())

# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.push("main")
director.play()
