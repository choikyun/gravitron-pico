"""GRAVITRON PICO"""

__version__ = "1.0.0"
__author__ = "Choi Gyun 2024"

import _thread
import random
import machine

import ease
import gamedata as dat
import picogamelib as gl
import picolcd114 as lcd
import framebuf as buf


### 疑似3D表示
_VIEW_W = const(79)  # ビューサイズ
_VIEW_H = const(20)
_VIEW_RATIO_W = const(3)  # ビューとスクリーンの拡大比率 1px=4x3dot
_VIEW_RATIO_H = const(3)
_VIEW_X = const(-39)  # ビュー開始座標 -39 ... 39 (79)
_VIEW_X_END = const(39 + 1)
_VIEW_ANGLE_FIX = const(64)  # 0度が北（上）になるように補正

_FIX = const(10)  # 固定小数の桁 10bit
_MAX_RAD = const(256)  # 角度 最大256°

_SCREEN_X = const(1)  # スクリーン描画 開始座標
_SCREEN_Y = const(75)

_SCREEN_W = const(237)  # スクリーンサイズ
_SCREEN_H = const(135)

_PIXEL_W = const(_VIEW_RATIO_W)  # 1ピクセルサイズ
_PIXEL_H = const(_VIEW_RATIO_H)

_COURSE_DATA_W = const(64)  # コースデータ 64px * 32px
_COURSE_DATA_H = const(32)
_COURSE_RATIO = const(4)  # コースデータ 1px=16px

_COURSE_W = const(_COURSE_DATA_W << _COURSE_RATIO)  # コースの大きさ（論理値）
_COURSE_H = const(_COURSE_DATA_H << _COURSE_RATIO)
_COURSE_DATA_COL = const(6)  # コースデータ 1行 64px

# カラー
_COL_INDEX_OUT = const(1)  # コース外
_COL_MINIMAP = const(0xFF9D) # ミニマップ
_COL_POWER_1 = const(0x0726) # パワー
_COL_POWER_2 = const(0x042A)


### ゲームバランス調整
_ACC_LIMIT = const(32)  # マックス加速度
_ACC_FIX = const(5)  # 加速度 固定小数桁 5bit

_MAX_ANGLE = const(3 << _ACC_FIX)  # ステアリングの最大角度
_MAX_SPEED = const(6 << _ACC_FIX)  # 最高速度

_POWER_FIX = const(10)
_MAX_POWER = const(240 * _POWER_FIX)

### オブジェクトのサイズ
_OBJ_W = const(32)
_OBJ_H = const(32)

### 自機
_SHIP_X = const(103)  # 自機座標
_SHIP_Y = const(103)

_POWER_W = const(4)
_POWER_H = const(4)

### ラップ
_LAP_W = const(32)
_LAP_H = const(16)

### スコア
_SCORE_DIGIT = const(6)
_LINE_DIGIT = const(4)

### メッセージ
_READY_DURATION = const(30 * 2)
_READY_INTERVAL = const(6)

### キャラクタ
_CHR_SHIP = const(0)
_CHR_SHIP_L = const(1)
_CHR_SHIP_R = const(2)
_CHR_BG = const(3)
_CHR_POWER_0 = const(4)
_CHR_POWER_1 = const(5)

### ビットマップ
_BMP_NUM = const(0)
_BMP_LAP = const(10)
_BMP_LAP_NUM = const(11)

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
_POWER_Z = const(20)
_MAP_Z = const(50)
_LAP_Z = const(50)
_MES_Z = const(50)
_SHIP_Z = const(100)

# イベント

# セーブデータ
_FILENAME = const("gv100.json")

# クロック 200MHz
machine.freq(200000000)


def thread_loop():
    """別スレッド（コア）で実行される. 座標変換"""

    print("thread start")
    while True:
        lock.acquire()
        if len(queue) == 0:
            lock.release()
            continue

        # キューからコマンド（タプル）を取得
        val = queue.pop(0)
        lock.release()

        vx = val[0]  # ビューの原点 xz座標
        vz = val[1]
        d = (val[2] + _VIEW_ANGLE_FIX) % _MAX_RAD  # 回転方向（要補正）
        screen = val[3]  # 現在バックグランドのスクリーン

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

                col = _COL_INDEX_OUT
                if px >= 0 and px < _COURSE_DATA_W and pz >= 0 and pz < _COURSE_DATA_H:
                    # コースデータからピクセルを取得
                    col = field[px + (pz << _COURSE_DATA_COL)]

                # ピクセル書き込み
                screen[i] = col
                i += 1
            ix += 1


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
        # パワー
        self.map = Power(self.stage, 0, "power", 0, 0, _POWER_Z, _POWER_W, _POWER_H)
        # ミニマップ
        self.map = Minimap(
            self.stage, 0, "map", 4, 7, _MAP_Z, _COURSE_DATA_W, _COURSE_DATA_H
        )
        # ラップ
        # self.lap = Lap(self.stage, 1, "lap", 120, 9, _MAP_Z)
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

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""

        self.chr_no = _CHR_SHIP

        if key.repeat & lcd.KEY_RIGHT and key.repeat & lcd.KEY_B:
            self.chr_no = _CHR_SHIP_R
        elif key.repeat & lcd.KEY_LEFT and key.repeat & lcd.KEY_B:
            self.chr_no = _CHR_SHIP_L


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

        self.vx = 976 << _FIX  # ビューの原点 XZ座標
        self.vz = 272 << _FIX
        self.vx_acc = 0  # ビュー XZ加速度
        self.vz_acc = 0
        self.speed = 0  # 移動速度（アクセル）
        self.speed_acc = 0  # 移動加速度
        self.dir = 191  # 方向（初期値 上）
        self.dir_angle = 0  # 方向 角度

        # 描画するピクセルのマップ 2画面
        self.screen = (
            bytearray(_VIEW_W * _VIEW_H),
            bytearray(_VIEW_W * _VIEW_H),
        )
        self.current_screen = 0  # 現在のスクリーン

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

        # 手抜きBG LINEで表現
        y = 42
        for x in range(0, 240, 4):
            gl.lcd.blit(gl.image_buffers[_CHR_BG], x, y)

    def enter(self):
        super().enter()

    def action(self):
        super().action()

    def show(self, frame_buffer, x, y):
        """スクリーン（ピクセルのマップ）をフレームバッファに描画"""

        # カレントスクリーンを描画する
        screen = self.screen[self.current_screen]

        # キューが空なら次をセット
        lock.acquire()
        if len(queue) == 0:
            # 別のスクリーンに描画する
            self.current_screen ^= 1
            queue.append(
                (
                    self.vx >> _FIX,
                    self.vz >> _FIX,
                    self.dir,
                    self.screen[self.current_screen],
                )
            )
        lock.release()

        pixs = self.pixels
        i = 0
        for y in range(_SCREEN_Y, _SCREEN_H, _PIXEL_H):
            for x in range(_SCREEN_X, _SCREEN_W, _PIXEL_W):
                col = screen[i]
                i += 1
                # ピクセル書き込み
                frame_buffer.blit(pixs[col], x, y)

    def ev_enter_frame(self, type, sender, key):
        """イベント:毎フレーム"""

        # 移動
        self.move(key)

    def move(self, key):
        """自機移動"""

        # アクセル
        if key.repeat & lcd.KEY_B:
            self.speed_acc += 8
            if self.speed_acc >= _ACC_LIMIT:
                self.speed_acc = _ACC_LIMIT
        # 減速
        else:
            self.speed_acc -= 2
            if self.speed_acc <= -_ACC_LIMIT:
                self.speed_acc = -_ACC_LIMIT

        # 左右移動（回転）
        if key.repeat & lcd.KEY_RIGHT and self.speed != 0:
            self.dir_angle += 16
            if self.dir_angle >= _MAX_ANGLE:
                self.dir_angle = _MAX_ANGLE
        elif key.repeat & lcd.KEY_LEFT and self.speed != 0:
            self.dir_angle -= 16
            if self.dir_angle <= -_MAX_ANGLE:
                self.dir_angle = -_MAX_ANGLE
        else:
            if self.dir_angle > 0:
                self.dir_angle -= 4  # 減衰
            elif self.dir_angle < 0:
                self.dir_angle += 4
        # 角度
        self.dir = (self.dir + (self.dir_angle >> _ACC_FIX)) % _MAX_RAD

        # 加速
        self.speed += self.speed_acc
        if self.speed >= _MAX_SPEED:
            self.speed = _MAX_SPEED
        elif self.speed <= 0:
            self.speed = 0

        d = self.dir
        s = self.speed >> _ACC_FIX
        self.vx_acc = dat.cos_tbl[d] * s  # XZ成分の加速度
        self.vz_acc = dat.sin_tbl[d] * s

        self.vx += self.vx_acc
        self.vz += self.vz_acc


class Minimap(gl.Sprite):
    """ミニマップ表示"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        # イベントリスナー登録
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])

        self.init_map()

    def init_map(self):
        """コースデータを描画"""

        d = dat.course1
        i = 0
        _x = self.x
        _w = self.w
        _y = self.y
        _h = self.h
        for y in range(_y, _y + _h):
            for x in range(_x, _x + _w):
                p = d[i]
                i += 1
                if p == _COL_INDEX_OUT:
                    continue

                gl.lcd.pixel(x, y, _COL_MINIMAP)

    def show(self, frame_buffer, x, y):
        """描画"""

    def ev_enter_frame(self, type, sender, key):
        """イベント:毎フレーム"""


class Power(gl.Sprite):
    """パワー表示"""

    def __init__(self, parent, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(parent, chr_no, name, x, y, z, w, h)

        self.power = _MAX_POWER

        # イベントリスナー登録
        self.event.add_listner([gl.EV_ENTER_FRAME, self, True])

        self.update_power()

    def update_power(self):
        """パワーゲージを描画"""

        w = self.power // _POWER_FIX
        gl.lcd.rect(0, 0, w, 3, _COL_POWER_1, True)

        if w < 239:
            gl.lcd.rect(w, 0, 240-w, 3, _COL_POWER_2, True)


    def show(self, frame_buffer, x, y):
        """描画 なにもしない"""

    def ev_enter_frame(self, type, sender, key):
        """イベント:毎フレーム"""


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
    (dat.ship, _OBJ_W, _OBJ_H),  # 自機
    (dat.ship_l, _OBJ_W, _OBJ_H),  # 自機 左
    (dat.ship_r, _OBJ_W, _OBJ_H),  # 自機 右
    (dat.bg, 4, 32),  # BG
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


# 座標変換スレッド
# 共有ロック
lock = _thread.allocate_lock()
queue = []  # 変数受け渡し用キュー
_thread.start_new_thread(thread_loop, ())


# ディレクターの作成
director = gl.Director(scenes)
# シーン実行
director.push("main")
director.play()
