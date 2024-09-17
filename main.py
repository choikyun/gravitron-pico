"""GRAVITRON PICO"""

__version__ = "1.0.0"
__author__ = "Choi Gyun 2024"

import _thread
import random
import utime
import gc
import machine

import ease
import gamedata as dat
import picogamelib as gl
import picolcd114 as lcd
import framebuf as buf


### 疑似3D表示
_VIEW_W = const(79)  # ビューサイズ
_VIEW_H = const(20)
_VIEW_RATIO_W = const(3)  # ビューとスクリーンの拡大比率 1px=3x3dot
_VIEW_RATIO_H = const(3)
_VIEW_X = const(-39)  # ビュー開始座標 -39 ... 39 (79)
_VIEW_X_END = const(39 + 1)
_VIEW_ANGLE_FIX = const(64)  # 0度が北（上）になるように補正

_PX_FIX = const(256)
_START_PX = const(_VIEW_X * _PX_FIX)  # X方向 描画開始座標
_START_PX2 = const((_VIEW_X + 1) * _PX_FIX)  # X方向 描画開始座標
_END_PX = const(_VIEW_X_END * _PX_FIX)  # X方向 描画終了座標

_FIX = const(10)  # 固定小数の桁 10bit
_MAX_RAD = const(256)  # 角度 256°
_H_RAD = const(_MAX_RAD // 2)  # 角度 1/2
_ATAN_SIZE = const(3)  # atanテーブルの長辺 基準の大きさ

_SCREEN_X = const(1)  # スクリーン描画 開始座標
_SCREEN_Y = const(75)

_SCREEN_W = const(240)  # スクリーンサイズ
_SCREEN_H = const(135)

_PIXEL_W = const(_VIEW_RATIO_W)  # 1ピクセルサイズ
_PIXEL_H = const(_VIEW_RATIO_H)

_COURSE_DATA_W = const(64)  # コースデータ 64 * 32
_COURSE_DATA_H = const(32)
_COURSE_RATIO = const(4)  # コースデータ 1byte = 16px

_COURSE_W = const(_COURSE_DATA_W << _COURSE_RATIO)  # コースの大きさ（論理値）
_COURSE_H = const(_COURSE_DATA_H << _COURSE_RATIO)
_COURSE_DATA_COL = const(6)  # コースデータ 1行 64px

### 描画スレッド
_COMM_VIEW = const(0)  # ビュー座標計算・描画
_COMM_SPRITE = const(1)  # スプライト描画
_COMM_LCD = const(2)  # LCDにバッファ転送
_COMM_EXIT = const(3)  # スレッド終了

_THREAD_SLEEP = const(0)
_THREAD_RUN = const(1)
_THREAD_EXIT = const(2)

# カラー
# インデックス
_COL_INDEX_BG = const(0)  # BG
_COL_INDEX_OUT = const(1)  # コース外
_COL_INDEX_G = const(7)  # 重力源
_COL_INDEX_DAMAGE = const(8)  # ダメージ
_COL_INDEX_RECOVERY = const(11)
_COL_INDEX_ACC = const(10)  # 加速
_COL_INDEX_CHECK = const(15)  # チェックポイント
_COL_INDEX_LAP = const(14)  # ラップ更新

# 565
_COL_BG = const(0)  # BGカラー
_COL_MINIMAP = const(0xFF9D)  # ミニマップ
_COL_BH = const(0xF809)  # ミニマップ上の重力源
_COL_MARKER = const(0xF809)  # ミニマップ上のマーカー
_COL_POWER_1 = const(0x0726)  # パワー
_COL_POWER_2 = const(0xFF64)
_COL_POWER_3 = const(0xF809)
_COL_POWER_OFF = const(0x042A)
_COL_OUT = const(0x194A)  # コース外
_COL_ALPHA = const(0x0726)  # スプライト透過色

_GAME_READY = const(0)  # スタート前
_GAME_PLAY = const(1)  # ゲーム中

### ゲームバランス調整

# 加速度用 補正 5bitの下駄
_ACC_FIX = const(5)

# アクセル
_SPEED_ACC_LIMIT = const(16)  # 加速度限界値
_ADD_SPEED_ACC = const(1)  # 加速度
_DEC_SPEED_ACC = const(-1)  # 減速 摩擦
_MAX_DEC_SPEED_ACC = const(-8)  # 減速 最大値

# ステアリング
_MAX_ANGLE = const(2 << _ACC_FIX)  # 最大角度
_ADD_DIR_ANGLE = const(8)  # 回転速度
_DEC_DIR_ANGLE = const(2)  # 回転減速

# スピード
_DEF_LIMIT_SPEED = const(3 << _ACC_FIX)  # 通常時の最高速度
_MAX_LIMIT_SPEED = const(6 << _ACC_FIX)  # バースト時時の最高速度

# 重力
_G_THRESHOLD = const(400)  # 重力の影響のしきい値
_MAX_LIMIT_G_SPEED = const(64)  # 重力加速度限界値

# パワー
_POWER_FIX = const(5)
_MAX_POWER = const(240 * _POWER_FIX)

_POWER_DOWN = const(-5)
_POWER_OUT = const(-40)
_POWER_RECOVERY = const(10)

# 自機
_SHIP_X = const(104)
_SHIP_Y = const(103)
_SHIP_W = const(32)
_SHIP_H = const(32)

# 爆風
_BOMB_X = const(_SHIP_X - 32)
_BOMB_Y = const(_SHIP_Y - 16)
_BOMB_X_RANGE = const(_SHIP_W + 32)
_BOMB_Y_RANGE = const(32)

# パワー
_POWER_W = const(4)
_POWER_H = const(4)

# ミニマップ
_MINIMAP_INTERVAL = const(5)

# ラップ
_LAP_X = const(80)
_LAP_Y = const(8)
_LAP_W = const(32)
_LAP_H = const(16)

_TIME_X = const(70)
_TIME_Y = const(0)
_TIME_W = const(40)
_TIME_H = const(16)

_LAP_NUM_X = const(34)
_LAP_NUM_Y = const(0)
_REC_NUM_X = const(70)
_REC_NUM_Y = const(18)

# メッセージ
_READY_DURATION = const(30 * 2)
_READY_INTERVAL = const(6)

# オブジェクトのサイズ
_OBJ_W = const(32)
_OBJ_H = const(32)

# 爆発
_BOMB_W = const(32)
_BOMB_H = const(32)

# 数字
_LAP_NUM_W = const(28)
_LAP_NUM_H = const(28)
_REC_NUM_W = const(12)
_REC_NUM_H = const(12)

### キャラクタ
# メイン
_CHR_SHIP = const(0)
_CHR_SHIP_L = const(1)
_CHR_SHIP_R = const(2)
_CHR_BOMB = const(3)  # ..6
_CHR_BURST = const(7)
_CHR_NUM = const(8)  # ..17
_CHR_LAPNUM = const(18)  # ..20
_CHR_LAP = const(22)
_CHR_READY = const(23)
_CHR_TIME = const(24)

# タイトル
_CHR_TITLE = const(0)
_CHR_CREDIT = const(1)

# ポーズ
_INFO_BRIGHT_W = const(44)
_INFO_BRIGHT_H = const(24)

# ゲームオーバー
_OVER_W = const(152)
_OVER_H = const(24)

# タイトル
_TITLE_W = const(240)
_TITLE_H = const(60)
_CREDIT_W = const(144)
_CREDIT_H = const(10)

# 重なり順
_POWER_Z = const(10)
_MAP_Z = const(10)
_LAP_Z = const(10)
_VIEW_Z = const(100)
_SHIP_Z = const(200)
_CRASH_Z = const(300)
_MES_Z = const(1000)

# イベント
_EV_UPDATE_POWER = const("ev_update_power")  # パワー更新
_EV_INIT_MINIMAP = const("ev_init_minimap")  # ミニマップ初期化
_EV_UPDATE_MINIMAP = const("ev_update_minimap")  # ミニマップ更新
_EV_RECORD_LAP = const("ev_record_lap")  # ラップ更新

# セーブデータ
_FILENAME = const("gv100.json")

# クロック 250MHz
machine.freq(250000000)


### 関数


def isqrt(a):
    """平方根の近似 整数"""
    a /= 2
    i = 1
    while a > 0:
        a -= i
        i += 1

    return i - 1


def cos_sin(angle):
    """角度から cos, sin 取得"""

    # 三角関数テーブル
    _s = 1
    if angle >= _H_RAD:
        _s = -1
        angle -= _H_RAD
    cos = dat.cos_tbl[angle] * _s
    sin = dat.sin_tbl[angle] * _s

    return (cos, sin)


def atan(x0, y0, x1, y1):
    """ざっくりしたアークタンジェント ２点間の方向と距離を求める"""

    tx = x1 - x0
    ty = y1 - y0
    q = 0

    if tx == 0 and ty == 0:
        return (-1, 0)

    if tx < 0 and ty >= 0:
        # 左下
        tx = -tx
        q = 1
    elif tx < 0 and ty < 0:
        # 左上
        tx = -tx
        ty = -ty
        q = 2
    elif tx >= 0 and ty < 0:
        # 右上
        ty = -ty
        q = 3

    if tx > ty:
        # x方向基準
        y = ty * _ATAN_SIZE // tx
        x = _ATAN_SIZE
    else:
        # y方向基準
        x = tx * _ATAN_SIZE // ty
        y = _ATAN_SIZE

    # テーブルから方向を求める
    d = dat.atan_tbl[x + (y << 2)]
    # 角度補正
    if q == 1:
        d = _H_RAD - d
    elif q == 2:
        d = _H_RAD + d
    elif q == 3:
        d = _MAX_RAD - d

    return (d & 0xFF, isqrt(tx * tx + ty * ty))


### スレッド


def thread_loop(data, lock):
    """別スレッド（コア）で実行される. 座標変換と描画"""

    if gl.DEBUG:
        print("thread start")

    while True:
        lock.acquire()
        queue = data[0]  # コマンドを取得
        lock.release()

        if len(queue) == 0:
            continue

        for cmd in queue:
            # ビュー描画
            if cmd[0] == _COMM_VIEW:
                thread_draw_view_v2(cmd)
            # スプライト描画
            elif cmd[0] == _COMM_SPRITE:
                thread_draw_sprite(cmd)
            # LCD転送
            elif cmd[0] == _COMM_LCD:
                thread_lcd(cmd)
            # 終了
            elif cmd[0] == _COMM_EXIT:
                if gl.DEBUG:
                    print("thread exit")
                _thread.exit()


def thread_draw_sprite(cmd):
    """スプライト描画"""

    cmd[4].blit(cmd[3], cmd[1], cmd[2], _COL_ALPHA)


@micropython.native
def thread_draw_view_v2(cmd):
    """ビュー 座標計算・描画"""

    # if gl.DEBUG:
    #     print("view2")

    _, vx, vz, d, field, buff = cmd

    # bg クリア
    buff.rect(_SCREEN_X, _SCREEN_Y, 238, 60, _COL_BG, True)

    d = (d + _VIEW_ANGLE_FIX) % _MAX_RAD  # 回転方向 補正
    cos, sin = cos_sin(d)  # cos, sin 固定小数
    pal = dat.palette565  # パレット
    by = _SCREEN_Y  # スクリーン描画開始Y

    for z, sx in zip(dat.z_index, dat.x_ratio):
        zcos = z * cos  # z座標の cos, sin
        zsin = z * sin
        bx = _SCREEN_X  # スクリーンの描画開始X座標
        px_w = _PIXEL_W  # ピクセル幅

        # 最初のピクセルを取得
        _x = _START_PX // sx  # -39 * 256
        pos_x = (((_x * cos - zsin) >> _FIX) + vx) >> _COURSE_RATIO
        pos_y = (
            (((_x * sin + zcos) >> _FIX) + vz) << 2
        ) & 0xFFC0  # y >> COURSE_RATIO * 64
        if pos_x >= 0 and pos_x < _COURSE_DATA_W and pos_y >= 0 and pos_y < 2048:
            prev_idx = field[pos_x + pos_y]
        else:
            prev_idx = _COL_INDEX_OUT

        for x in range(_START_PX2, _END_PX, _PX_FIX):  # -38*256 .. 39*256
            _x = x // sx  # x方向の拡縮
            # 回転 コースデータサイズに補正
            pos_x = (((_x * cos - zsin) >> _FIX) + vx) >> _COURSE_RATIO
            pos_y = ((((_x * sin + zcos) >> _FIX) + vz) << 2) & 0xFFC0  # y * 64

            if pos_x >= 0 and pos_x < _COURSE_DATA_W and pos_y >= 0 and pos_y < 2048:
                idx = field[pos_x + pos_y]
            else:
                idx = _COL_INDEX_OUT

            if idx == prev_idx:
                # 前回と同じ色
                px_w += _PIXEL_W  # 描画スキップ
            else:
                # 前回と違うので直前まで描画する BGと同じ場合はスキップ
                if prev_idx != _COL_INDEX_BG:
                    buff.rect(bx, by, px_w, _PIXEL_H, pal[prev_idx], True)
                prev_idx = idx
                bx += px_w  # 描画開始座標 更新
                px_w = _PIXEL_W

        # 最後のピクセル
        if idx == prev_idx and idx != _COL_BG:
            buff.rect(bx, by, px_w, _PIXEL_H, pal[prev_idx], True)

        # 1ライン終了
        by += _PIXEL_H


def thread_lcd(cmd):
    """LCD描画"""

    cmd[1].show()


### シーン


class TitleScene(gl.Scene):
    """タイトル画面
    ・ハイスコア表示
    """

    def __init__(self, name, key):
        super().__init__(name, key)

        # ステージ
        self.set_stage(TitleStage())

    def action(self):
        super().action()

        if self.active:
            # ゲーム開始
            if self.key.push & lcd.KEY_B:
                self.director.pop()  # 停止 リソース破棄
                self.director.push("main")


class MainScene(gl.Scene):
    """メイン"""

    def __init__(self, name, key):
        super().__init__(name, key)

        # ステージ（塗りつぶし無し）
        self.set_stage(ThreadStage())

    def enter(self):
        """各種初期化処理"""
        super().enter()

        # イベントリスナー
        # self.event.add_listener([_EV_GAMEOVER, self, True])
        self.gameover = False

    def action(self):
        """フレーム毎のアクション 30FPS"""
        super().action()


### ステージ


class TitleStage(gl.Stage):
    """タイトル画面のステージ"""

    def __init__(self):
        super().__init__("title", 0, 0, gl.BG_COLOR)

    def ready(self):
        """初回実行"""

        # スプライト作成 この時点では画像リソースは無い
        self.title = Title()
        self.add_child(self.title)
        super().ready()

    def enter(self):
        """初期化"""

        # バッファクリア
        gl.lcd.fill(_COL_BG)
        super().enter()
        self.title.enter()


class ThreadStage(gl.Stage):
    """メインシーン ステージ 描画は別スレッドに投げる"""

    ### クラス変数
    lock = _thread.allocate_lock()  # 共有ロック
    thread_data = [()]  # スレッドに渡すデータ

    def __init__(self):
        super().__init__("main", 0, 0, gl.ALPHA_COLOR)

        # 描画スレッドに投げるキュー
        self.stage_queue = []

    def ready(self):
        """初回実行"""

        self.status = _GAME_READY  # ゲーム開始前
        self.event.add_listener([gl.EV_ENTER_FRAME, self, True])

        ## スプライト この時点では画像リソースが無い（画像リソースの無いスプライトもある）
        self.ship = Ship()  # 自機
        self.add_child(self.ship)
        self.power = Power()  # パワー
        self.add_child(self.power)
        self.map = Minimap()  # ミニマップ
        self.add_child(self.map)
        self.lap = Lap()  # ラップ
        self.add_child(self.lap)
        self.view = View()  # 疑似3Dビュー
        self.add_child(self.view)

        super().ready()

    def enter(self):
        """初期化"""

        # バッファクリア
        gl.lcd.fill(_COL_BG)
        super().enter()

        self.ship.enter()  # スプライト有効化
        self.view.enter()

        # 開始前のデモ
        self.dir = self.view.dir
        self.view.dir = (self.view.dir - 64) % _MAX_RAD  # カメラ初期値
        self.ship.y += 64

        # 描画スレッド開始
        _thread.start_new_thread(
            thread_loop, (ThreadStage.thread_data, ThreadStage.lock)
        )

    def show(self):
        """ステージ更新
        ・描画は別スレッド（コア）に投げる
        """

        # キューをクリア
        self.stage_queue.clear()

        for s in self.sprite_list:
            s.show(gl.lcd, self.resources["images"], self.x, self.y)

        # lcd 転送
        self.stage_queue.append((_COMM_LCD, gl.lcd))

        # 描画スレッド強制終了
        if key.repeat & lcd.KEY_A:
            self.stage_queue.append((_COMM_EXIT,))

        # ステージのキューを別スレッドに送る
        # データは上書き
        ThreadStage.lock.acquire()
        ThreadStage.thread_data[0] = self.stage_queue
        ThreadStage.lock.release()

    def leave(self):
        # 描画スレッド停止
        ThreadStage.lock.acquire()
        ThreadStage.thread_data[0] = [(_COMM_EXIT,)]
        ThreadStage.lock.release()
        # スプライト無効化
        super().leave()

    def ev_enter_frame(self, type, sender, option):
        """ゲーム開始前のデモ？"""
        self.view.dir = (self.view.dir + 2) % _MAX_RAD  # カメラ回り込む
        self.ship.y -= 2
        if self.view.dir == self.dir:
            self.status = _GAME_PLAY
            self.power.enter()
            self.map.enter()
            self.lap.enter()
            self.event.remove_listener([gl.EV_ENTER_FRAME, self])


### スプライト


class ThreadSprite(gl.Sprite):
    """描画は別スレッドに投げる"""

    def __init__(self, chr_no, name, x, y, z, w, h):
        super().__init__()
        self.init_params(chr_no, name, x, y, z, w, h)

    def show(self, frame_buffer, images, x, y):
        if self.active:
            x += self.x
            y += self.y

            # 描画データをキュー 親を先に描画
            self.stage.stage_queue.append(
                (
                    _COMM_SPRITE,
                    x,
                    y,
                    images[self.chr_no + self.frame_index],
                    frame_buffer,
                )
            )
            # 子スプライト
            for sp in self.sprite_list:
                sp.show(frame_buffer, images, x, y)


class ThreadSpriteContainer(gl.SpriteContainer):
    """自分は描画しない"""

    def __init__(self, name, x, y, z):
        super().__init__()
        super().init_params(name, x, y, z)

    def show(self, frame_buffer, images, x, y):
        if self.active:
            x += self.x
            y += self.y

            # 子スプライト
            for sp in self.sprite_list:
                sp.show(frame_buffer, images, x, y)


class Ship(ThreadSprite):
    """自機クラス"""

    def __init__(self):
        super().__init__(_CHR_SHIP, "ship", _SHIP_X, _SHIP_Y, _SHIP_Z, _OBJ_W, _OBJ_H)

    def ready(self):
        # 爆発
        self.crash = Crash()
        self.add_child(self.crash)
        # バースト
        self.burst = Burst()
        self.add_child(self.burst)
        super().ready()

    def enter(self):
        super().enter()
        # イベントリスナー登録
        self.event.add_listener([gl.EV_ENTER_FRAME, self, True])

        self.shake = False  # 振動

    def show(self, frame_buffer, images, x, y):

        # 状態異常 振動
        if self.shake:
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)

        super().show(frame_buffer, images, x, y)

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""

        self.chr_no = _CHR_SHIP

        if key.repeat & lcd.KEY_RIGHT and key.repeat & lcd.KEY_B:
            self.chr_no = _CHR_SHIP_R
        elif key.repeat & lcd.KEY_LEFT and key.repeat & lcd.KEY_B:
            self.chr_no = _CHR_SHIP_L

    def start_crash(self):
        """クラッシュ"""
        self.crash.enter()

    def start_shake(self):
        """機体が振動"""
        self.shake = True

    def end_shake(self):
        self.shake = False

    def start_burst(self):
        """バースト状態のスプライト"""
        self.burst.enter()

    def end_burst(self):
        """スプライト停止"""
        self.burst.leave()


class Crash(ThreadSpriteContainer):
    """クラッシュ"""

    def __init__(self):
        super().__init__("crash", 0, 0, _CRASH_Z)
        self.bombs = []  # 爆風

    def ready(self):
        # 爆発スプライト
        for _ in range(2):
            b = Bomb()
            self.add_child(b)
            self.bombs.append(b)
        super().ready()

    def enter(self):
        super().enter()
        self.event.add_listener([gl.EV_ENTER_FRAME, self, True])

        self.interval = 16  # 1回分の爆発のインターバル
        self.count = 3  # 爆発回数
        for b in self.bombs:
            b.enter()

    def ev_enter_frame(self, type, sender, option):
        """毎フレーム"""

        self.interval -= 1
        if self.interval == 0:
            self.interval = 16

            for i in range(2):
                self.bombs[i].reset()  # 次の爆風

            self.count -= 1
            if self.count == 0:
                # results failed
                # todo
                pass


class Bomb(ThreadSprite):
    """クラッシュ時の爆発"""

    def __init__(self):
        super().__init__(
            _CHR_BOMB,
            "bomb",
            _BOMB_X + random.randint(0, _BOMB_X_RANGE),
            _BOMB_Y + random.randint(0, _BOMB_Y_RANGE),
            _CRASH_Z,
            _BOMB_W,
            _BOMB_H,
        )
        # アニメ
        self.init_frame_params(4, 4)

    def reset(self):
        """リセット"""
        self.frame_index = 0
        self.x = _BOMB_X + random.randint(0, _BOMB_X_RANGE)
        self.y = _BOMB_Y + random.randint(0, _BOMB_Y_RANGE)


class Burst(ThreadSprite):
    """加速時の爆風"""

    def __init__(self):
        super().__init__(
            _CHR_BURST, "burst", _SHIP_X + 7, _SHIP_Y + 7, _CRASH_Z, 16, 16
        )

    def show(self, frame_buffer, images, x, y):
        if self.active:
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)
            super().show(frame_buffer, images, x, y)


class View(ThreadSprite):
    """コースの疑似3D表示 スプライトとして処理する"""

    def __init__(self):
        super().__init__(0, "view", 0, 0, _VIEW_Z, _VIEW_W, _VIEW_H)

    def enter(self):
        super().enter()

        # イベントリスナー登録
        self.event.add_listener([gl.EV_ENTER_FRAME, self, True])

        # コース初期化
        self.course_no = game_status["course"]
        self.load_course_data(self.course_no)

        # ビュー初期化
        self.init_view()
        # 背景
        self.init_bg()

    def action(self):
        super().action()

    def show(self, frame_buffer, images, x, y):
        """フレームバッファに描画"""

        # 描画データをキュー
        self.stage.stage_queue.append(
            (
                _COMM_VIEW,  # ビュー座標計算と描画
                self.vx >> _FIX,
                self.vz >> _FIX,
                self.dir,
                self.course_dat,
                frame_buffer,
            )
        )

    def init_view(self):
        """ビュー初期化"""
        self.vx_acc = 0  # ビュー XZ加速度
        self.vz_acc = 0
        self.speed = 0  # 移動速度（アクセル）
        self.speed_limit = _DEF_LIMIT_SPEED  # 速度上限
        self.speed_acc = 0  # 移動加速度
        self.dir_angle = 0  # 方向 角度
        self.g_speed = 0  # 重力加速度
        self.prev_pixel = 0  # 前フレームの路面

    def init_bg(self):
        """背景"""
        # 手抜きBG LINEで表現
        gl.lcd.rect(1, 42, 238, 10, 0x194A, True)
        gl.lcd.rect(1, 52, 238, 8, 0x83B3, True)
        gl.lcd.rect(1, 60, 238, 6, 0xFE75, True)
        gl.lcd.rect(1, 66, 238, 6, 0xFF9D, True)
        gl.lcd.rect(1, 70, 238, 2, 0x2D7F, True)

    def ev_enter_frame(self, type, sender, key):
        """イベント:毎フレーム"""

        if self.stage.status == _GAME_READY:
            return

        # 移動
        self.move(key)
        # 地形効果判定
        self.apply_field_effects()

    def move(self, key):
        """自機移動"""

        # アクセル
        if key.repeat & lcd.KEY_B:
            self.speed_acc += _ADD_SPEED_ACC  # 加速度
            if self.speed_acc >= _SPEED_ACC_LIMIT:
                self.speed_acc = _SPEED_ACC_LIMIT
            # パワー消費
            power = -1
            if self.speed_limit > _DEF_LIMIT_SPEED:
                power = -2
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    gl.EV_PRIORITY_MID,
                    0,
                    self,
                    power,
                ]
            )

        # 減速
        else:
            # ブースト リセット
            self.speed_limit = _DEF_LIMIT_SPEED

            self.speed_acc += _DEC_SPEED_ACC
            if self.speed_acc <= _MAX_DEC_SPEED_ACC:
                self.speed_acc = _MAX_DEC_SPEED_ACC

        # 最高速以外は重力の影響受ける
        self.gravity_effect(self.speed, self.speed_limit)

        # 左右移動（回転）
        if key.repeat & lcd.KEY_RIGHT and self.speed != 0:
            self.dir_angle += _ADD_DIR_ANGLE
            if self.dir_angle >= _MAX_ANGLE:
                self.dir_angle = _MAX_ANGLE
        elif key.repeat & lcd.KEY_LEFT and self.speed != 0:
            self.dir_angle -= _ADD_DIR_ANGLE
            if self.dir_angle <= -_MAX_ANGLE:
                self.dir_angle = -_MAX_ANGLE
        else:
            if self.dir_angle > 0:
                self.dir_angle -= _DEC_DIR_ANGLE  # 減衰
            elif self.dir_angle < 0:
                self.dir_angle += _DEC_DIR_ANGLE
        # 角度
        self.dir = (self.dir + (self.dir_angle >> _ACC_FIX)) % _MAX_RAD

        # 加速
        self.speed += self.speed_acc
        if self.speed >= self.speed_limit:
            self.speed = self.speed_limit
        elif self.speed <= 0:
            self.speed = 0

        d = self.dir
        cos, sin = cos_sin(d)
        self.vx += cos * (self.speed >> _ACC_FIX)  # XZ成分の加速度
        self.vz += sin * (self.speed >> _ACC_FIX)

        # 加速パネルでの加速を減速
        if self.speed_limit > _DEF_LIMIT_SPEED:
            self.speed_limit -= 1
            if self.speed_limit <= _DEF_LIMIT_SPEED:  # バースト表示終了
                self.stage.ship.end_burst()

        # ミニマップマーカー更新
        self.event.post(
            [
                _EV_UPDATE_MINIMAP,
                gl.EV_PRIORITY_MID,
                0,
                self,
                (
                    self.course_dat,
                    self.vx >> (_FIX + _COURSE_RATIO),
                    self.vz >> (_FIX + _COURSE_RATIO),
                ),
            ]
        )

    def apply_field_effects(self):
        """地形効果"""
        x = self.vx >> (_FIX + _COURSE_RATIO)
        z = self.vz >> (_FIX + _COURSE_RATIO)
        self.stage.ship.end_shake()

        # 範囲チェック
        if x < 0 or x >= _COURSE_DATA_W or z < 0 or z >= _COURSE_DATA_H:
            self.speed_limit = _DEF_LIMIT_SPEED  # 速度リセット
            self.prev_pixel = _COL_INDEX_OUT
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    gl.EV_PRIORITY_MID,
                    0,
                    self,
                    -20,
                ]
            )
            self.stage.ship.start_shake()  # 振動
            return

        pixel = self.course_dat[x + z * _COURSE_DATA_W]
        # コースアウト
        if pixel == _COL_INDEX_OUT:
            self.speed_limit = _DEF_LIMIT_SPEED  # 速度リセット
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    gl.EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_OUT,
                ]
            )
            self.stage.ship.start_shake()  # 振動
        # パワーダウン
        elif pixel == _COL_INDEX_DAMAGE:
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    gl.EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_DOWN,
                ]
            )
            self.stage.ship.start_shake()  # 振動
        # パワーアップ（回復）
        elif pixel == _COL_INDEX_RECOVERY:
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    gl.EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_RECOVERY,
                ]
            )
        # 加速
        elif pixel == _COL_INDEX_ACC:
            self.speed_limit = _MAX_LIMIT_SPEED  # バースト
            self.speed = _MAX_LIMIT_SPEED
            self.stage.ship.start_burst()

        # LAP判定
        prev_pixel = pixel
        if (
            pixel == _COL_INDEX_LAP
            and self.prev_pixel != _COL_INDEX_LAP
            and self.dir >= self.lap[0]
            and self.dir <= self.lap[1]
        ):
            # ラップ更新
            self.event.post(
                [
                    _EV_RECORD_LAP,
                    gl.EV_PRIORITY_MID,
                    0,
                    self,
                    None,
                ]
            )

        self.prev_pixel = prev_pixel

    def gravity_effect(self, speed, limit):
        """最高速以外は重力の影響受ける"""
        # 重力源の方向
        d, f = atan(self.vx >> _FIX, self.vz >> _FIX, self.g_src[0], self.g_src[1])

        if d == -1:
            return

        # ある程度近かったら
        if f < _G_THRESHOLD and speed < limit:
            self.g_speed += f >> 5  # 近いほど強い
            if self.g_speed > _MAX_LIMIT_G_SPEED:
                self.g_speed = _MAX_LIMIT_G_SPEED
            cos, sin = cos_sin(d)
            self.vx += cos * (self.g_speed >> _ACC_FIX)
            self.vz += sin * (self.g_speed >> _ACC_FIX)
        else:
            self.g_speed = 0

    def load_course_data(self, num):
        """コースデータ読み込み 外部バイナリファイル"""
        data = course_datafile[num]
        f = open(data[0], "rb")
        self.course_dat = f.read()
        f.close()

        self.vx = data[1][0] << _FIX
        self.vz = data[1][1] << _FIX
        self.dir = data[1][2]
        self.g_src = data[2]
        self.lap = data[3]  # ゴール範囲


class Minimap(ThreadSpriteContainer):
    """ミニマップ表示 スプライトを描画しない"""

    def __init__(self):
        super().__init__("map", 4, 7, _MAP_Z)

        # 前回のマーカー表示の座標
        self.prev = [0] * 2

    def enter(self):
        super().enter()
        # イベントリスナー登録
        self.event.add_listener([_EV_INIT_MINIMAP, self, True])
        self.event.add_listener([_EV_UPDATE_MINIMAP, self, True])

        self.show_flg = 1  # 点滅用
        self.interval = _MINIMAP_INTERVAL  # 点滅インターバル

        # ミニマップ初期化
        self.init_minimap(
            self.stage.view.course_dat,
            self.stage.view.vx >> (_FIX + _COURSE_RATIO),
            self.stage.view.vz >> (_FIX + _COURSE_RATIO),
        )

    def show(self, frame_buffer, images, x, y):
        """描画"""
        # なにもしない
        pass

    def init_minimap(self, course, vx, vz):
        """コースデータを描画"""

        i = 0
        _x = self.x
        _w = _x + _COURSE_DATA_W
        _y = self.y
        _h = _y + _COURSE_DATA_H
        for y in range(_y, _h):
            for x in range(_x, _w):
                p = course[i]
                i += 1
                if p == _COL_INDEX_OUT:
                    continue
                col = _COL_MINIMAP
                gl.lcd.pixel(x, y, col)

        self.prev[0] = vx  # 前回の座標
        self.prev[1] = vz

        # マーカー描画
        gl.lcd.rect(
            self.prev[0] + self.x, self.prev[1] + self.y, 4, 4, _COL_MARKER, True
        )

    def ev_update_minimap(self, type, sender, data):
        """現在位置を更新"""

        # 前回を復元
        _x = self.prev[0]
        _y = self.prev[1]
        field = data[0]
        for y in range(_y, _y + 4):
            for x in range(_x, _x + 4):
                col = 0
                idx = field[x + (y << _COURSE_DATA_COL)]
                if idx != _COL_INDEX_OUT:
                    col = _COL_MINIMAP
                gl.lcd.pixel(x + self.x, y + self.y, col)

        x = data[1]
        y = data[2]
        # マーカー位置補正
        if x < 0:
            x = 0
        elif x > _COURSE_DATA_W - 4:
            x = _COURSE_DATA_W - 4
        if y < 0:
            y = 0
        elif y > _COURSE_DATA_H - 4:
            y = _COURSE_DATA_H - 4

        # 今回の座標バックアップ
        self.prev[0] = x
        self.prev[1] = y

        self.interval -= 1
        if self.interval < 0:
            self.interval = _MINIMAP_INTERVAL
            self.show_flg ^= 1

        if self.show_flg:
            # マーカー描画
            gl.lcd.rect(x + self.x, y + self.y, 4, 4, _COL_MARKER, True)


class Power(ThreadSpriteContainer):
    """パワー表示 スプライトを描画しない"""

    def __init__(self):
        super().__init__("power", 0, 0, _POWER_Z)

    def enter(self):
        super().enter()
        # イベントリスナー登録
        self.event.add_listener([_EV_UPDATE_POWER, self, True])

        self.power = _MAX_POWER
        self.update_power()

    def update_power(self):
        """パワーゲージを描画"""

        w = self.power // _POWER_FIX
        col = _COL_POWER_1
        if w < 60:
            col = _COL_POWER_3
        if w < 120:
            col = _COL_POWER_2

        if w > 0:
            gl.lcd.rect(0, 0, w - 1, 3, col, True)
        if w < 240:
            gl.lcd.rect(w, 0, 239, 3, _COL_POWER_OFF, True)

    def show(self, frame_buffer, images, x, y):
        """描画 なにもしない"""
        pass

    def ev_update_power(self, type, sender, v):
        """イベント:パワー更新"""

        self.power += v
        if self.power <= 0:
            self.power = 0
        elif self.power >= _MAX_POWER:
            self.power = _MAX_POWER

        self.update_power()

        # ゼロになったら爆発
        if self.power == 0:
            self.stage.ship.start_crash()


class Title(gl.Sprite):
    """タイトル"""

    def __init__(self):
        super().__init__()
        self.init_params(_CHR_TITLE, "title", 0, 6, _MES_Z, _TITLE_W, _TITLE_H)

    def ready(self):
        # アニメ
        self.anime = gl.Animator("title_anime", self.event, ease.out_elastic)
        # クレジット
        self.credit = gl.Sprite().init_params(
            _CHR_CREDIT, "choi", 48, 125, _MES_Z, _CREDIT_W, _CREDIT_H
        )
        self.add_child(self.credit)
        super().ready

    def enter(self):
        super().enter()

        self.event.add_listener([gl.EV_ANIME_COMPLETE, self, True])
        # アニメのパラメータ初期化
        self.anime.attach()
        self.y = 100
        self.anime.start = self.y
        self.anime.delta = -100
        self.anime.total_frame = 60
        self.anime.play()

    def action(self):
        super().action()

        if self.anime.is_playing:
            self.y = int(self.anime.value)

    def leave(self):
        self.anime.stop()
        self.anime.detach()
        super().leave()

    def ev_anime_complete(self, type, sender, option):
        """アニメ終了"""
        # クレジット表示
        self.credit.enter()


class Lap(ThreadSprite):
    """ラップ"""

    def __init__(self):
        super().__init__(_CHR_LAP, "lap", _LAP_X, _LAP_Y, _MES_Z, _LAP_W, _LAP_H)

        # スタートタイム
        self.start_time = 0
        # ラップ
        self.lap_count = 0
        self.lap_time = [0] * 3  # 3周

    def ready(self):
        # ラップ表示
        self.lap_nums = Nums(
            1, (_CHR_LAPNUM, _LAP_NUM_W, _LAP_NUM_H), _LAP_NUM_X, _LAP_NUM_Y
        )
        self.add_child(self.lap_nums)
        # タイム表示
        self.time = ThreadSprite(_CHR_TIME, "time", _TIME_X, _TIME_Y, _MES_Z, _TIME_W, _TIME_H)
        self.add_child(self.time)
        self.rec_nums = Nums(
            6, (_CHR_NUM, _REC_NUM_W, _REC_NUM_H), _REC_NUM_X, _REC_NUM_Y
        )
        self.add_child(self.rec_nums)
        super().ready()

    def enter(self):
        super().enter()
        self.lap_nums.enter()
        self.time.enter()
        self.rec_nums.enter()

    def ev_record_lap(self, type, sender, option):
        """ラップ更新 周回数 タイム"""
        if self.lap_count == 0:
            # 計測開始
            self.start_time = utime.ticks_ms()
        else:
            time = utime.ticks_ms()
            self.lap_time[self.lap_count] = time - self.start_time
            self.start_time = time
            self.rec_nums.update_num(self.conv_time(self.lap_time[self.lap_count]))

        # todo lap == 3 -> result

        self.lap_count += 1
        self.lap_nums.update_num(self.lap_count)

    def conv_time(self, val):
        """msを 分:秒:ミリ秒 に変換"""
        m = val // 1000 // 60
        s = val // 1000
        ms = (val % 1000) // 10

        return m * 10000 + s * 100 + ms


class Nums(ThreadSpriteContainer):
    """数値表示コンテナ
    Params:
        digit (int): 桁
        font(tupple): chr, width, height
        x(int):
        y(int):
    """

    def __init__(self, digit, font, x, y):
        super().__init__("nums", x, y, _MES_Z)
        self.digit = digit
        self.nums = []
        self.font = font

    def ready(self):
        # 数字スプライト 2桁毎にスペース
        x = 0
        for i in range(self.digit):
            s = Num(self.font, x, 0, 0)
            x += self.font[1] + 2 + (i & 1) * 2
            self.add_child(s)
            self.nums.append(s)
        super().ready()

    def enter(self):
        super().enter()
        for s in self.nums:
            s.enter()

    def update_num(num):
        for i in range(self.digit - 1, -1, -1):
            val = num % 10
            num //= 10
            self.nums[i].set_num(val)


class Num(ThreadSprite):
    """数値スプライト
    Params:
        font(tupple): chr, width, height
        x(int):
        y(int):
        val(int): 初期数値

    """

    def __init__(self, font, x, y, val):
        super().__init__(font[0] + val, "num", x, y, _MES_Z, font[1], font[2])
        self.font = font

    def set_num(self, val):
        self.chr_no = self.font[0] + val


class BlinkMessage(gl.BitmapSprite):
    """点滅メッセージ表示
    一定期間で消える

    Attributes:
        duration (int): 表示時間
        interval (int): 点滅間隔 0の時は点滅しない
    """

    def __init__(self, bitmap, duration, interval, name, x, y, z, w, h):
        super().__init__(bitmap, name, x, y, z, w, h)
        self.duration = duration
        self.interval = interval

    def enter(self):
        return super().enter()

    def action(self):
        super().action()

        if self.interval != 0 and self.duration % self.interval == 0:
            self.active = not self.active

        # 一定時間で消える
        self.duration -= 1
        if self.duration == 0:
            self.leave()


### グローバル

# ステータスをロード
game_status = gl.load_status(_FILENAME)

if game_status is None:
    # デフォルト
    game_status = {
        "course": 0,
        "bestlap": [0] * 3,
        "brightness": 2,
    }
    gl.save_status(game_status, _FILENAME)

# コースデータファイル
# ファイル名, (スタート座標 方向), (重力源座標), (ゴール方向範囲),
course_datafile = (
    ("course1.dat", (880, 32, 128), (496, 240), (65, 191)),
    ("course2.dat", (32, 112, 64), (208, 224), (1, 127)),
    ("course3.dat", (976, 368, 192), (496, 384), (129, 255)),
)

# LCDの明るさ
gl.lcd.brightness(game_status["brightness"])

# シーン
key = lcd.InputKey()
main = MainScene("main", key)
title = TitleScene("title", key)
# ディレクター
director = gl.Director((title, main))
director.push("title")
director.play()
