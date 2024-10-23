"""GRAVITRON"""

__version__ = "1.0.1"
__author__ = "Choi Gyun 2024"

import _thread
from random import randint
from utime import ticks_ms
from machine import freq
from gc import collect

from ease import linear, inout_elastic
from gamedata import cos_tbl, sin_tbl, atan_tbl, z_scale_tbl, h_scale_tbl, pal_tbl
from picolcd114 import (
    KEY_A,
    KEY_B,
    KEY_UP,
    KEY_DOWN,
    KEY_RIGHT,
    KEY_LEFT,
    KEY_CENTER,
    LCD_BRIGHTNESS_MAX,
    InputKey,
)

from picogamelib import (
    EV_ENTER_FRAME,
    EV_ANIME_ENTER_FRAME,
    EV_PRIORITY_MID,
    lcd,
    def_bg_color,
    def_alpha_color,
    EV_ANIME_COMPLETE,
    Director,
    Scene,
    Stage,
    Sprite,
    SpriteContainer,
    Animator,
    load_status,
    save_status,
)


### 疑似3D表示

_VIEW_W = const(79)  # ビューサイズ
_VIEW_H = const(20)
_VIEW_RATIO_W = const(3)  # ビューとスクリーンの拡大比率（1ピクセル=3x3ピクセル）
_VIEW_RATIO_H = const(3)
_VIEW_W_START = const(-39)  # ビュー水平方向 開始・終了座標 -39 ... 39 (79ピクセル)
_VIEW_W_END = const(39 + 1)

_SCREEN_X = const(1)  # スクリーン描画 開始座標
_SCREEN_Y = const(75)
_PIXEL_W = const(_VIEW_RATIO_W)  # 1ピクセルサイズ
_PIXEL_H = const(_VIEW_RATIO_H)

_PX_FIX = const(256)  # 描画用 固定小数
_START_PX = const(_VIEW_W_START * _PX_FIX)  # 水平方向 描画開始座標
_START_PX2 = const((_VIEW_W_START + 1) * _PX_FIX)  # 水平方向 描画開始座標
_END_PX = const(_VIEW_W_END * _PX_FIX)  # 水平方向 描画終了座標

_FIX = const(10)  # 固定小数 10bit
_MAX_RAD = const(256)  # 最大角度 256度
_H_RAD = const(_MAX_RAD // 2)  # 半周角度
_ATAN_SIZE = const(3)  # atanテーブルの長辺 基準の大きさ

_COURSE_DATA_W = const(64)  # コースデータ 64 * 32
_COURSE_DATA_H = const(32)
_COURSE_RATIO = const(4)  # コースデータ（1byte=16px）
_COURSE_DATA_COL = const(6)  # コースデータ 1行 64px
_MAX_COURSE = const(6)  # コース数

### 描画コマンド

_COMM_VIEW = const(0)  # ビュー座標計算・描画
_COMM_SPRITE = const(1)  # スプライト描画
_COMM_LCD = const(2)  # LCDにバッファ転送
_COMM_EXIT = const(3)  # スレッド終了

### カラー

# インデックス
_COL_INDEX_OUT = const(1)  # コース外
_COL_INDEX_DAMAGE = const(3)  # ダメージ
_COL_INDEX_ACC = const(4)  # 加速
_COL_INDEX_RECOVERY = const(5)  # 回復
_COL_INDEX_LAP = const(6)  # ラップ更新
# 565
_COL_BG = const(0)  # BGカラー
_COL_MINIMAP = const(0x0726)  # ミニマップ
_COL_MARKER = const(0xF809)  # ミニマップ上のマーカー
_COL_POWER_1 = const(0x0726)  # パワー
_COL_POWER_2 = const(0xFF64)
_COL_POWER_3 = const(0xF809)
_COL_POWER_FLASH = const(0xFF9D)
_COL_POWER_OFF = const(0x042A)

_COL_ALPHA = const(0x0726)  # スプライト透過色
_COL_TITLEMAP1 = const(0x0726)  # タイトル画面のコースマップ

### ゲームステータス

_GAME_READY = const(0)  # スタート前
_GAME_PLAY = const(1)  # ゲーム中
_GAME_PAUSE = const(2)  # ポーズ
_GAME_FINISH = const(3)  # 終了

### ゲームバランス調整

# 加速度用 5bitの固定小数
_ACC_FIX = const(5)

# アクセル
_SPEED_ACC_LIMIT = const(16)  # 加速度限界値
_ADD_SPEED_ACC = const(1)  # 加速度
_DEC_SPEED_ACC = const(-1)  # 減速 摩擦
_MAX_DEC_SPEED_ACC = const(-4)  # 減速 最大値

# ステアリング
_MAX_DIR_ANGLE = const(2 << _ACC_FIX)  # 最大角度
_ADD_DIR_ANGLE = const(8)  # 回転速度
_DEC_DIR_ANGLE = const(2)  # 回転減速

# スピード
_DEF_LIMIT_SPEED = const(3 << _ACC_FIX)  # 通常時の最高速度
_MAX_LIMIT_SPEED = const(6 << _ACC_FIX)  # バースト時の最高速度

# 重力
_G_THRESHOLD = const(256)  # 重力の影響のしきい値
_MAX_LIMIT_G_SPEED = const(32)  # 通常モード 重力加速度限界値
_MAX_LIMIT_G_SPEED_EX = const(48)  # EXモード 重力加速度限界値

# クラッシュ
_CRASH_COUNT = const(3)  # 爆発回数 この間に回復できたらセーフ

# パワー
_POWER_FIX = const(6)
_MAX_POWER = const(240 * _POWER_FIX)

_POWER_OUT = const(-40)
_POWER_DAMAGE = const(-4)
_POWER_RECOVERY = const(20)


### スプライト


# 基本オブジェクトサイズ
_SP_W = const(32)
_SP_H = const(32)

# 自機
_SHIP_X = const(104)
_SHIP_Y = const(103)

# 爆風
_BOMB_X = const(-32)
_BOMB_Y = const(-16)
_BOMB_X_RANGE = const(32)  # X方向範囲
_BOMB_Y_RANGE = const(0)
_BOMB_NUM = const(3)  # 爆風の数

# ミニマップ
_MINIMAP_INTERVAL = const(5)  # 点滅インターバル

# ラップ タイム
_LAP_X = const(74)
_LAP_Y = const(7)
_TIME_X = const(65)
_TIME_Y = const(0)

# 数字
_LAP_NUM_X = const(35)
_LAP_NUM_Y = const(2)
_REC_NUM_X = const(70)
_REC_NUM_Y = const(18)
_REC_NUM_W = const(16)
_REC_NUM_H = const(16)

# 看板
_READY_X = const(78)
_READY_Y = const(76)
_READY_W = const(84)
_READY_H = const(28)

# クレジット
_CREDIT_W = const(144)
_CREDIT_H = const(10)


### キャラクタ番号

# メイン
_CHR_SHIP = const(0)
_CHR_SHIP_L = const(1)
_CHR_SHIP_R = const(2)
_CHR_BOMB = const(3)  # <=6
_CHR_BURST = const(7)
_CHR_NUM = const(8)  # <=17
_CHR_LAPNUM = const(18)  # <=20
_CHR_LAP = const(22)
_CHR_TIME = const(23)
_CHR_PAUSE_MES = const(24)
_CHR_READY = const(25)  # <=8

# タイトル
_CHR_TITLE = const(0)  # <=6
_CHR_CREDIT = const(7)
_CHR_SUB = const(8)
_CHR_TITLENUM = const(9)  # <=17
_CHR_R_AR = const(19)
_CHR_L_AR = const(20)
_CHR_PLANET = const(21)
_CHR_EX = const(22)
_CHR_DEBUG = const(23)

# リザルト
_CHR_RESULTS = const(0)  # <=2
_CHR_RESULTNUM = const(3)  # <=12
_CHR_LAP1 = const(13)  # <=16
_CHR_NEW = const(17)
_CHR_FAIL = const(18)

# 重なり順
_BG_Z = const(10)  # lap mapなど
_VIEW_Z = const(100)
_SHIP_Z = const(200)
_CRASH_Z = const(300)
_MES_Z = const(1000)


### イベント

_EV_UPDATE_POWER = const("ev_update_power")  # パワー更新
_EV_INIT_MINIMAP = const("ev_init_minimap")  # ミニマップ初期化
_EV_UPDATE_MINIMAP = const("ev_update_minimap")  # ミニマップ更新
_EV_RECORD_LAP = const("ev_record_lap")  # ラップ更新
_EV_FINISH = const("ev_finish")  # フィニッシュ
_EV_REVERSE = const("ev_reverse")  # 逆走

### セーブデータ
_FILENAME = const("gv100.json")


### クロック 250MHz 大丈夫？
freq(250000000)


### 関数


def isqrt(a):
    """平方根の近似 整数"""
    a //= 2
    i = 1
    while a > 0:
        a -= i
        i += 1

    return i - 1


def cos_sin(angle):
    """cos, sin 取得"""

    # 三角関数テーブル
    if angle >= _H_RAD:
        return (cos_tbl[angle - _H_RAD] * -1, sin_tbl[angle - _H_RAD] * -1)
    else:
        return (cos_tbl[angle], sin_tbl[angle])


def atan(x0, y0, x1, y1):
    """ざっくりしたアークタンジェント
    ２点間の方向と距離を求める"""

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
    d = atan_tbl[x + (y << 2)]
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
    """別スレッド（コア）で実行される座標変換と描画"""

    while True:
        lock.acquire()
        queue = data[0]  # コマンドを取得
        lock.release()

        if len(queue) == 0:
            continue

        for cmd in queue:
            # ビュー描画
            c = cmd[0]
            if c == _COMM_VIEW:
                draw_view_v3(cmd)
            # スプライト描画
            elif c == _COMM_SPRITE:
                cmd[4].blit(cmd[3], cmd[1], cmd[2], _COL_ALPHA)
            # LCD転送
            elif c == _COMM_LCD:
                cmd[1].show()
            # 終了
            elif c == _COMM_EXIT:
                _thread.exit()


def draw_view_v3(cmd):
    """座標計算・描画"""
    _, vx, vz, cos, sin, field, buff = cmd

    buff_rect = buff.rect  # メソッドを変数に代入しておく
    # ビュー部分(画面の下半分)クリア
    buff_rect(_SCREEN_X, _SCREEN_Y, 238, 60, _COL_BG, True)

    scr_y = _SCREEN_Y  # スクリーン描画開始Y
    for z, h, pal in zip(z_scale_tbl, h_scale_tbl, pal_tbl):
        zcos = z * cos  # z座標（奥行き）の cos, sin
        zsin = z * sin
        scr_x = _SCREEN_X  # スクリーンの描画開始X座標
        pw = _PIXEL_W  # ピクセル幅
        col_out = pal[_COL_INDEX_OUT]

        # 最初のピクセルを取得
        _y = _START_PX // h  # -39 * 256 // h
        pos_x = (((zcos - _y * sin) >> _FIX) + vx) >> _COURSE_RATIO
        # pos_y はあらかじめ64倍
        pos_y = ((((zsin + _y * cos) >> _FIX) + vz) << 2) & 0xFFC0
        if pos_x < 0 or pos_x >= _COURSE_DATA_W or pos_y < 0 or pos_y >= 2048:
            prev_col = col_out
        else:
            prev_col = pal[field[pos_x + pos_y]]

        for y in range(_START_PX2, _END_PX, _PX_FIX):  # -38*256 <= y <= 39*256
            _y = y // h  # 水平方向の拡縮
            # 回転 コースデータサイズに補正
            pos_x = (((zcos - _y * sin) >> _FIX) + vx) >> _COURSE_RATIO
            pos_y = ((((zsin + _y * cos) >> _FIX) + vz) << 2) & 0xFFC0
            if pos_x < 0 or pos_x >= _COURSE_DATA_W or pos_y < 0 or pos_y >= 2048:
                col = col_out
            else:
                col = pal[field[pos_x + pos_y]]

            if col == prev_col:
                # 前回と同じ色
                pw += _PIXEL_W  # 描画スキップ
            else:
                # 前回と違うので直前まで描画する BGと同じ場合はスキップ
                if prev_col != _COL_BG:
                    buff_rect(scr_x, scr_y, pw, _PIXEL_H, prev_col, True)
                prev_col = col
                scr_x += pw  # 描画開始座標 更新
                pw = _PIXEL_W

        # 最後のピクセル
        if col == prev_col and col != _COL_BG:
            buff_rect(scr_x, scr_y, pw, _PIXEL_H, prev_col, True)

        # 1ライン終了
        scr_y += _PIXEL_H


### シーン


class TitleScene(Scene):
    """タイトル画面
    コース選択 ベストタイム表示
    """

    def __init__(self, name, key):
        super().__init__(name, key)

        # ステージ
        self.set_stage(TitleStage())

    def action(self):
        super().action()

        if self.active:
            # debug
            if self.key.push & KEY_CENTER and self.key.push & KEY_A:
                game_status["mode"] ^= 2
                if game_status["mode"] & 2 == 2:
                    print(";) debug mode on - No damage while debugging.")
                    self.stage.title.d.active = True
                else:
                    print(";) debug mode off")
                    self.stage.title.d.active = False
            # ゲーム開始 シーンの切り替えはaction後
            elif self.key.push & KEY_B:
                d = self.director
                d.pop()  # 停止 リソース破棄
                d.push("main")
            # モード変更
            elif self.key.push & KEY_A:
                game_status["mode"] ^= 1


class ResultsScene(Scene):
    """画面
    ・ラップ表示
    """

    def __init__(self, name, key):
        super().__init__(name, key)

        # ステージ
        self.set_stage(ResultsStage())

    def action(self):
        super().action()

        if self.active:
            # タイトルへ戻る
            if self.key.push & KEY_B:
                d = self.director
                d.pop()  # 停止 リソース破棄

                d.push("title")


class MainScene(Scene):
    """ゲームメイン"""

    def __init__(self, name, key):
        super().__init__(name, key)

        # ステージ（塗りつぶし無し）
        self.set_stage(ThreadStage())

        # ポーズ中の経過時間
        self.pause_time = 0
        # 画面停止時間
        self.freeze_time = 30

    def action(self):
        super().action()

        if self.active:
            if self.stage.status == _GAME_PLAY:
                # ポーズ
                if self.key.push & KEY_A:
                    self.pause_time = ticks_ms()  # 計測開始
                    self.stage.status = _GAME_PAUSE
                    self.stage.pause_mes.enter()
                    self.event.disable_listeners((EV_ENTER_FRAME, EV_ANIME_ENTER_FRAME))
            elif self.stage.status == _GAME_PAUSE:
                # ポーズ解除
                if self.key.push & KEY_B:
                    self.pause_time = ticks_ms() - self.pause_time  # 計測終了
                    self.stage.status = _GAME_PLAY
                    self.stage.pause_mes.active = False
                    self.event.enable_listeners((EV_ENTER_FRAME, EV_ANIME_ENTER_FRAME))
                    self.stage.lap.fix_pause_time(self.pause_time)  # ラップタイム修正
                # タイトルに戻る
                elif self.key.push & KEY_A:
                    director.pop()
                    director.push("title")
            # レース終了
            elif self.stage.status == _GAME_FINISH:
                self.freeze_time -= 1
                if self.freeze_time == 0:
                    director.pop()
                    director.push("results")


### ステージ


class TitleStage(Stage):
    """タイトル画面のステージ"""

    def __init__(self):
        super().__init__("title", 0, 0, def_bg_color)

    def enter(self):
        # バッファクリア
        lcd.fill(_COL_BG)
        super().enter()

        self.title = Title()
        self.add_child(self.title)
        self.title.enter()

        # デバッグモードはオフ
        game_status["mode"] &= 1

    def leave(self):
        super().leave()


class ResultsStage(Stage):
    """リザルトのステージ"""

    def __init__(self):
        super().__init__("results", 0, 0, 0x194A)

    def enter(self):
        super().enter()

        self.add_child(ResultRecords()).enter()


class ThreadStage(Stage):
    """メインシーンのステージ このステージだけ描画を別スレッドに投げる"""

    def __init__(self):
        super().__init__("main", 0, 0, def_alpha_color)

        self.lock = _thread.allocate_lock()  # 共有ロック
        self.thread_data = [()]  # スレッドに渡すデータ

    def enter(self):
        super().enter()

        # バッファクリア
        lcd.fill(_COL_BG)

        # ゲームモード
        self.mode = game_status["mode"]  # 0 通常 1 EXモード 2 DEBUG

        # スプライト
        self.ship = Ship()  # 自機
        self.add_child(self.ship).enter()
        self.power = Power()  # パワー
        self.add_child(self.power)
        self.map = Minimap()  # ミニマップ
        self.add_child(self.map)
        self.lap = Lap()  # ラップ
        self.add_child(self.lap)
        self.readygo = ReadyGo()  # ready表示
        self.add_child(self.readygo)
        self.pause_mes = PauseMes()  # ポーズ中メッセージ
        self.add_child(self.pause_mes)
        self.view = View()  # 疑似3Dビュー
        self.add_child(self.view).enter()

        self.event.add_listener([_EV_FINISH, self, True])
        self.event.add_listener([EV_ENTER_FRAME, self, True])

        # 開始前のデモ
        self.status = _GAME_READY  # ゲーム開始前
        self.dir = self.view.dir
        self.view.dir = (self.view.dir - 64) % _MAX_RAD  # カメラ初期値
        self.ship.y += 64

        # 描画スレッド開始
        self.start_thread()

    def show(self):
        """ステージ更新
        ・描画は別スレッド（コア）に投げる
        """
        self.stage_queue = []  # キューを新規作成

        # スプライト
        for s in self.sprite_list:
            s.show(lcd, self.resources["images"], self.x, self.y)

        # lcd 転送
        self.stage_queue.append((_COMM_LCD, lcd))

        # 描画スレッド
        self.lock.acquire()
        self.thread_data[0] = self.stage_queue
        self.lock.release()

    def action(self):
        if self.status == _GAME_PLAY:
            super().action()

    def leave(self):
        self.stop_thread()
        super().leave()

    def start_thread(self):
        """描画スレッド開始"""
        collect()
        _thread.start_new_thread(thread_loop, (self.thread_data, self.lock))

    def stop_thread(self):
        """描画スレッド停止"""
        self.lock.acquire()
        self.thread_data[0] = [(_COMM_EXIT,)]
        self.lock.release()

    def ev_enter_frame(self, type, sender, option):
        # 開始前
        if self.status == _GAME_READY:
            self.view.dir = (self.view.dir + 2) % _MAX_RAD  # カメラ回り込む演出
            self.ship.y -= 2
            if self.view.dir == self.dir:
                self.power.enter()
                self.map.enter()
                self.lap.enter()
                self.readygo.enter()  # ready! 表示
                self.status = _GAME_PLAY
                self.event.remove_listener([EV_ENTER_FRAME, self])  # リスナーはずす

    def ev_finish(self, type, sender, option):
        # ゲーム終了
        self.status = _GAME_FINISH
        self.stage.scene.director.values[2] = option  # 通常ゴール 5 | 失敗 1..3
        self.event.disable_listeners(
            (EV_ENTER_FRAME, EV_ANIME_ENTER_FRAME)
        )  # 一定時間停止


### スプライト


class ThreadSprite(Sprite):
    """描画は別スレッドに投げるスプライト"""

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
            for sp in self.sprite_list:
                sp.show(frame_buffer, images, x, y)


class ThreadSpriteContainer(ThreadSprite):
    """コンテナ 自分は描画しない"""

    def __init__(self, name, x, y, z):
        super().__init__(0, name, x, y, z, 0, 0)

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
        super().__init__(_CHR_SHIP, "ship", _SHIP_X, _SHIP_Y, _SHIP_Z, _SP_W, _SP_H)

    def enter(self):
        super().enter()

        # 爆発
        self.crash = Crash()
        self.add_child(self.crash).enter()
        # バースト
        self.burst = Burst()
        self.add_child(self.burst).enter()

        # イベントリスナー登録
        self.event.add_listener([EV_ENTER_FRAME, self, True])

        self.shake = False  # 振動
        self.is_crash = False  # クラッシュ中か

    def show(self, frame_buffer, images, x, y):
        # 状態異常 振動
        if self.shake and self.stage.status == _GAME_PLAY:
            x += randint(-2, 2)
            y += randint(-2, 2)

        super().show(frame_buffer, images, x, y)

    def ev_enter_frame(self, type, sender, option):
        """イベント:毎フレーム"""
        self.chr_no = _CHR_SHIP

        if key.repeat & KEY_RIGHT and key.repeat & KEY_B:
            self.chr_no = _CHR_SHIP_R
        elif key.repeat & KEY_LEFT and key.repeat & KEY_B:
            self.chr_no = _CHR_SHIP_L

    def start_crash(self):
        """クラッシュ"""
        self.crash.start()
        self.start_shake()
        self.end_burst()
        self.is_crash = True

    def end_crash(self):
        """クラシュ終了"""
        self.crash.end()
        self.is_crash = False

    def start_shake(self):
        """機体が振動"""
        self.shake = True

    def end_shake(self):
        self.shake = False

    def start_burst(self):
        """バースト状態のスプライト"""
        self.burst.active = True

    def end_burst(self):
        """スプライト停止"""
        self.burst.active = False


class Crash(ThreadSpriteContainer):
    """クラッシュ"""

    def __init__(self):
        super().__init__("crash", 0, 0, _CRASH_Z)
        self.bombs = []  # 爆風

    def enter(self):
        super().enter()

        # 爆発スプライト
        for _ in range(_BOMB_NUM):
            b = Bomb()
            self.add_child(b).enter()
            self.bombs.append(b)

        self.event.add_listener([EV_ENTER_FRAME, self, True])
        self.active = False

    def ev_enter_frame(self, type, sender, option):
        """毎フレーム"""

        if self.active:
            self.interval -= 1
            if self.interval == 0:
                self.interval = 16

                for i in range(_BOMB_NUM):
                    self.bombs[i].reset()  # 次の爆風

                self.count -= 1
                if self.count == 0:
                    # 終了
                    self.event.post(
                        [
                            _EV_FINISH,
                            EV_PRIORITY_MID,
                            0,
                            self,
                            self.stage.lap.lap_count,  # 失敗したラップ
                        ]
                    )

    def start(self):
        """爆発開始"""
        self.interval = 16  # 1回分の爆発のインターバル
        self.count = _CRASH_COUNT  # 爆発回数
        for i in range(_BOMB_NUM):
            self.bombs[i].reset()

        self.active = True

    def end(self):
        """爆発終了"""
        self.active = False


class Bomb(ThreadSprite):
    """爆発"""

    def __init__(self):
        super().__init__(
            _CHR_BOMB,
            "bomb",
            randint(_BOMB_X, _BOMB_X_RANGE),
            randint(_BOMB_Y, _BOMB_Y_RANGE),
            _CRASH_Z,
            _SP_W,
            _SP_H,
        )
        # アニメ
        self.init_frame_params(4, 3)

    def show(self, frame_buffer, images, x, y):
        if self.active:
            if self.stage.status == _GAME_PLAY:
                x += randint(-2, 2)
                y += randint(-2, 2)

            super().show(frame_buffer, images, x, y)

    def reset(self):
        """リセット"""
        self.frame_index = 0
        self.x = randint(_BOMB_X, _BOMB_X_RANGE)
        self.y = randint(_BOMB_Y, _BOMB_Y_RANGE)


class Burst(ThreadSprite):
    """加速時の爆風"""

    def __init__(self):
        super().__init__(_CHR_BURST, "burst", 7, 7, _CRASH_Z, 16, 16)

    def enter(self):
        super().enter()

        self.active = False

    def show(self, frame_buffer, images, x, y):
        if self.active:
            if self.stage.status == _GAME_PLAY:
                x += randint(-2, 2)
                y += randint(-2, 2)

            super().show(frame_buffer, images, x, y)


class View(ThreadSprite):
    """コースの疑似3D表示 スプライトとして処理"""

    def __init__(self):
        super().__init__(0, "view", 0, 0, _VIEW_Z, _VIEW_W, _VIEW_H)

    def enter(self):
        super().enter()

        # イベントリスナー登録
        self.event.add_listener([EV_ENTER_FRAME, self, True])

        # ビュー初期化
        self.init_view()
        # 背景
        self.init_bg()

        # コース初期化
        self.course_no = game_status["course"]
        self.load_course_data(self.course_no)

    def show(self, frame_buffer, images, x, y):
        """フレームバッファに描画"""
        # 描画データをキュー
        self.stage.stage_queue.append(
            (
                _COMM_VIEW,  # ビュー座標計算と描画
                self.vx >> _FIX,
                self.vz >> _FIX,
                self.camera_cos,
                self.camera_sin,
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
        self.g_speed = 0  # 重力加速度
        # self.dir = 0  # 進行方向
        self.dir_angle = 0  # 進行方向角度
        self.camera_cos = 0  # 描画用 cos sin
        self.camera_sin = 0
        self.prev_pixel = 0  # 前フレームの路面

    def init_bg(self):
        """背景"""
        # 手抜きBG LINEで表現
        if randint(0, 1) == 0:
            lcd.rect(1, 43, 238, 10, 0x194A, True)
            lcd.rect(1, 53, 238, 8, 0x83B3, True)
            lcd.rect(1, 59, 238, 6, 0xFE75, True)
            lcd.rect(1, 65, 238, 6, 0xFF9D, True)
            lcd.rect(1, 71, 238, 2, 0x2D7F, True)
        else:
            lcd.rect(1, 43, 238, 10, 0x2D7F, True)
            lcd.rect(1, 53, 238, 8, 0xFF9D, True)
            lcd.rect(1, 59, 238, 6, 0xC618, True)
            lcd.rect(1, 65, 238, 6, 0xFD00, True)
            lcd.rect(1, 71, 238, 2, 0xFF64, True)

    def ev_enter_frame(self, type, sender, key):
        """イベント:毎フレーム"""
        # 操作
        self.operate(key)
        # 移動
        self.move()
        # 地形効果判定
        self.apply_field_effects()

    def operate(self, key):
        """操作"""
        if self.stage.status == _GAME_PLAY:
            # アクセル
            if key.repeat & KEY_B:
                self.speed_acc += _ADD_SPEED_ACC  # 加速度

                if self.speed_acc >= _SPEED_ACC_LIMIT:
                    self.speed_acc = _SPEED_ACC_LIMIT
                # パワー消費
                ex = 1 + (self.stage.mode & 1)
                power = -1 * ex
                if self.speed_limit > _DEF_LIMIT_SPEED:
                    power = -3 * ex
                self.event.post(
                    [
                        _EV_UPDATE_POWER,
                        EV_PRIORITY_MID,
                        0,
                        self,
                        power,
                    ]
                )
            # 減速
            else:
                self.speed_acc += _DEC_SPEED_ACC
                if self.speed_acc <= _MAX_DEC_SPEED_ACC:
                    self.speed_acc = _MAX_DEC_SPEED_ACC

            # 左右移動（回転）
            if key.repeat & KEY_RIGHT and self.speed != 0:
                self.dir_angle += _ADD_DIR_ANGLE
                if self.dir_angle >= _MAX_DIR_ANGLE:
                    self.dir_angle = _MAX_DIR_ANGLE
            elif key.repeat & KEY_LEFT and self.speed != 0:
                self.dir_angle -= _ADD_DIR_ANGLE
                if self.dir_angle <= -_MAX_DIR_ANGLE:
                    self.dir_angle = -_MAX_DIR_ANGLE
            else:
                if self.dir_angle > 0:
                    self.dir_angle -= _DEC_DIR_ANGLE  # 減衰
                elif self.dir_angle < 0:
                    self.dir_angle += _DEC_DIR_ANGLE
            # 角度
            self.dir = (self.dir + (self.dir_angle >> _ACC_FIX)) % _MAX_RAD

    def move(self):
        """移動"""
        # 重力
        self.gravity_effect(self.speed)

        # 加速
        self.speed += self.speed_acc
        if self.speed >= self.speed_limit:
            self.speed = self.speed_limit
        elif self.speed <= 0:
            self.speed = 0

        cos, sin = cos_sin(self.dir)
        self.vx += cos * (self.speed >> _ACC_FIX)  # XZ成分の加速度
        self.vz += sin * (self.speed >> _ACC_FIX)
        self.camera_cos = cos
        self.camera_sin = sin

        # 加速パネルでの加速を減速
        if self.speed_limit > _DEF_LIMIT_SPEED:
            self.speed_limit -= 1
            if self.speed_limit <= _DEF_LIMIT_SPEED:  # バースト表示終了
                self.stage.ship.end_burst()

        # ミニマップ マーカー更新
        self.event.post(
            [
                _EV_UPDATE_MINIMAP,
                EV_PRIORITY_MID,
                0,
                self,
                (
                    self.course_dat,
                    self.vx >> (_FIX + _COURSE_RATIO),
                    self.vz >> (_FIX + _COURSE_RATIO),
                ),
            ]
        )

    def crash(self):
        """クラッシュ状態"""
        self.speed_limit == _DEF_LIMIT_SPEED  # バースト表示終了
        self.stage.ship.end_burst()

    def apply_field_effects(self):
        """地形効果"""
        x = self.vx >> (_FIX + _COURSE_RATIO)
        z = self.vz >> (_FIX + _COURSE_RATIO)
        self.stage.ship.end_shake()

        # 範囲チェック
        if x < 0 or x >= _COURSE_DATA_W or z < 0 or z >= _COURSE_DATA_H:
            # コースアウト
            self.speed_limit = _DEF_LIMIT_SPEED  # 速度リセット
            self.prev_pixel = _COL_INDEX_OUT
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_OUT,
                ]
            )
            self.stage.ship.end_burst()
            self.stage.ship.start_shake()  # 振動
            return

        pixel = self.course_dat[x + z * _COURSE_DATA_W]
        # コースアウト
        if pixel == _COL_INDEX_OUT:
            self.speed_limit = _DEF_LIMIT_SPEED  # 速度リセット
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_OUT,
                ]
            )
            self.stage.ship.end_burst()
            self.stage.ship.start_shake()  # 振動
        # ダメージレーン
        elif pixel == _COL_INDEX_DAMAGE:
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_DAMAGE,
                ]
            )
            self.stage.ship.start_shake()  # 振動
        # 回復レーン
        elif pixel == _COL_INDEX_RECOVERY:
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_RECOVERY,
                ]
            )
        # 加速バー
        elif pixel == _COL_INDEX_ACC:
            self.speed_limit = _MAX_LIMIT_SPEED  # バースト
            self.speed = _MAX_LIMIT_SPEED
            self.stage.ship.start_burst()
            self.event.post(
                [
                    _EV_UPDATE_POWER,
                    EV_PRIORITY_MID,
                    0,
                    self,
                    _POWER_RECOVERY * 2,
                ]
            )

        # LAP判定
        prev_pixel = pixel
        if pixel == _COL_INDEX_LAP and self.prev_pixel != _COL_INDEX_LAP:
            if self.dir >= self.lap[0] and self.dir <= self.lap[1]:
                # ラップ更新
                self.event.post(
                    [
                        _EV_RECORD_LAP,
                        EV_PRIORITY_MID,
                        0,
                        self,
                        None,
                    ]
                )
                self.event.post(
                    [
                        _EV_UPDATE_POWER,
                        EV_PRIORITY_MID,
                        0,
                        self,
                        _MAX_POWER // 2,  # 半分回復
                    ]
                )
            # 逆走
            else:
                # ラップ更新
                self.event.post(
                    [
                        _EV_REVERSE,
                        EV_PRIORITY_MID,
                        0,
                        self,
                        None,
                    ]
                )

        self.prev_pixel = prev_pixel

    def gravity_effect(self, speed):
        """重力"""
        # 重力源の方向と距離
        d, f = atan(self.vx >> _FIX, self.vz >> _FIX, self.g_src[0], self.g_src[1])

        if d == -1:
            return

        if self.stage.mode & 1 == 0:
            g_limit = _MAX_LIMIT_G_SPEED
        else:
            g_limit = _MAX_LIMIT_G_SPEED_EX

        # ある程度近かったら
        if f < _G_THRESHOLD:
            f = (f - speed) >> 6
            if f < 0:
                f = 0
            self.g_speed += f  # スピードが遅いほど影響受ける
            if self.g_speed > g_limit:
                self.g_speed = g_limit
            cos, sin = cos_sin(d)
            self.vx += cos * (self.g_speed >> _ACC_FIX)
            self.vz += sin * (self.g_speed >> _ACC_FIX)
        else:
            self.g_speed = 0

    def load_course_data(self, num):
        """コースデータ読み込み"""
        data = course_datafile[num]
        self.vx = data[1][0] << _FIX
        self.vz = data[1][1] << _FIX
        self.dir = data[1][2]
        self.g_src = data[2]  # 重力発生源
        self.lap = data[3]  # ゴール範囲

        collect()
        try:
            f = open(data[0], "rb")
        except:
            print(":‑( Load Course Error.")
            self.course_dat = [0] * (_COURSE_DATA_W * _COURSE_DATA_H)
            return

        self.course_dat = f.read()
        f.close()


class Minimap(ThreadSpriteContainer):
    """ミニマップ表示 スプライトを描画しない"""

    def __init__(self):
        super().__init__("map", 4, 7, _BG_Z)

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
        lcd_pixel = lcd.pixel
        for y in range(_y, _h):
            for x in range(_x, _w):
                p = course[i]
                i += 1
                if p == _COL_INDEX_OUT:
                    continue
                col = _COL_MINIMAP
                lcd_pixel(x, y, col)

        self.prev[0] = vx  # 前回の座標
        self.prev[1] = vz

        # マーカー描画
        lcd.rect(self.prev[0] + self.x, self.prev[1] + self.y, 4, 4, _COL_MARKER, True)

    def ev_update_minimap(self, type, sender, data):
        """現在位置を更新"""

        # 前回を復元
        _x = self.prev[0]
        _y = self.prev[1]
        selfx = self.x
        selfy = self.y
        field = data[0]
        lcd_pixel = lcd.pixel
        for y in range(_y, _y + 4):
            for x in range(_x, _x + 4):
                col = 0
                idx = field[x + (y << _COURSE_DATA_COL)]
                if idx != _COL_INDEX_OUT:
                    col = _COL_MINIMAP
                lcd_pixel(x + selfx, y + selfy, col)

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
            lcd.rect(x + self.x, y + self.y, 4, 4, _COL_MARKER, True)


class Power(ThreadSpriteContainer):
    """パワー表示 スプライトを描画しない"""

    def __init__(self):
        super().__init__("power", 0, 0, _BG_Z)

    def enter(self):
        super().enter()

        # イベントリスナー登録
        if self.stage.mode & 2 != 2:  # デバッグモードはノーダメージ
            self.event.add_listener([_EV_UPDATE_POWER, self, True])

        self.power = _MAX_POWER
        self.update_power()

        self.flash = 0  # エネルギーがゼロになったら点滅
        self.flash_interval = 10

    def update_power(self):
        """パワーゲージを描画"""

        w = self.power // _POWER_FIX
        col = _COL_POWER_1
        if w < 60:
            col = _COL_POWER_3
        elif w < 120:
            col = _COL_POWER_2

        if w > 0:
            lcd.rect(0, 0, w - 1, 3, col, True)
        if w < 240:
            lcd.rect(w, 0, 239, 3, _COL_POWER_OFF, True)

        if w <= 0:
            self.flash_interval -= 1
            if self.flash_interval == 0:
                self.flash_interval = 10
                self.flash ^= 1
            if self.flash:
                lcd.rect(w, 0, 239, 3, _COL_POWER_FLASH, True)
        else:
            self.flash = 0

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

        # 爆発
        if self.power <= 0 and self.stage.ship.is_crash == False:
            self.stage.ship.start_crash()  # 爆風
            self.stage.view.crash()  # 速度リセット
        # 爆発終了（復帰）
        elif self.power > 0 and self.stage.ship.is_crash:
            self.stage.ship.end_crash()


class Title(SpriteContainer):
    """タイトル"""

    def __init__(self):
        super().__init__()
        self.init_params(
            "title",
            8,
            10,
            _MES_Z,
        )

    def enter(self):
        super().enter()

        # タイトルは分割
        for i in range(7):
            self.add_child(
                Sprite()
                .init_params(
                    _CHR_TITLE + i, "title", i * _SP_W, 0, _MES_Z, _SP_W, _SP_H
                )
                .enter()
            )

        # サブタイトル
        self.sub = Sprite().init_params(_CHR_SUB, "starcup", 60, 37, _MES_Z, 120, 10)
        self.add_child(self.sub)

        # ゲームモード
        self.ex = Sprite().init_params(_CHR_EX, "ex", 200, 35, _MES_Z, 32, 16)
        self.add_child(self.ex)
        self.ex.enter()
        self.ex.active = False
        # デバッグモード
        self.d = Sprite().init_params(_CHR_DEBUG, "debug", 180, 35, _MES_Z, 16, 16)
        self.add_child(self.d)
        self.d.enter()
        self.d.active = False

        # クレジット
        self.credit = Sprite().init_params(
            _CHR_CREDIT, "choi", 48, 125, _MES_Z, _CREDIT_W, _CREDIT_H
        )
        self.add_child(self.credit)
        self.select_course = SelectCourse()
        self.add_child(self.select_course)

        self.event.add_listener([EV_ANIME_COMPLETE, self, True])

        # アニメ
        self.anime = Animator("title_anime", self.event, linear)
        self.anime.attach()
        self.y = 100
        self.anime.start = self.y
        self.anime.delta = -100
        self.anime.total_frame = 30
        self.anime.play()

    def action(self):
        super().action()

        if self.anime.is_playing:
            self.y = int(self.anime.value)

        if game_status["mode"] & 1 == 1:
            self.ex.active = True
        else:
            self.ex.active = False

    def leave(self):
        super().leave()

        self.anime.stop()
        self.anime.detach()

    def ev_anime_complete(self, type, sender, option):
        """アニメ終了"""
        self.sub.enter()
        self.credit.enter()
        # コース選択
        self.select_course.enter()


class SelectCourse(SpriteContainer):
    """コース選択"""

    def __init__(self):
        super().__init__()
        super().init_params("select", 20, 68, 100)

    def enter(self):
        super().enter()

        # 左右矢印
        sp = Sprite().init_params(_CHR_R_AR, "ar_r", -22, 5, 100, 16, 16)
        self.add_child(sp)
        sp.enter()
        sp = Sprite().init_params(_CHR_L_AR, "ar_l", 74, 5, 100, 16, 16)
        self.add_child(sp)
        sp.enter()
        # planet
        sp = Sprite().init_params(_CHR_PLANET, "planet", 90, -2, 100, 64, 16)
        self.add_child(sp)
        sp.enter()

        self.planet_num = PlanetNum()  # コース
        self.add_child(self.planet_num)
        self.planet_num.enter()
        self.planet_num.update_num()
        self.title_nums = TitleNums()
        self.add_child(self.title_nums)
        self.title_nums.enter()

        self.course_num = game_status["course"]
        self.load_course(self.course_num)

    def load_course(self, num):
        """コースマップ"""
        data = course_datafile[num]

        collect()
        try:
            f = open(data[0], "rb")
        except:
            print(":‑( Error Load Course Data.")
            self.course = [0] * (_COURSE_DATA_W * _COURSE_DATA_H)
            return

        self.course = f.read()
        f.close()

    def show(self, frame_buffer, images, x, y):
        if self.active:

            lcd.line(0, 56, 239, 56, 0xFD00)
            lcd.line(0, 111, 239, 111, 0xFD00)

            if self.course is not None:
                _x = x + self.x
                _y = y + self.y
                lcd.rect(_x - 4, _y - 4, 72, 40, _COL_TITLEMAP1)

                i = 0
                _w = _x + _COURSE_DATA_W
                _h = _y + _COURSE_DATA_H
                course = self.course
                lcd_pixel = lcd.pixel
                for py in range(_y, _h):
                    for px in range(_x, _w):
                        p = course[i]
                        i += 1
                        if p == _COL_INDEX_OUT:
                            continue
                        else:
                            col = _COL_TITLEMAP1
                        lcd_pixel(px, py, col)

            super().show(frame_buffer, images, x, y)

    def action(self):
        super().action()

        if self.active:
            if game_status["mode"] & 1 == 0:
                self.title_nums.update_num(game_status["displap"][self.course_num])
            else:
                self.title_nums.update_num(game_status["displap_ex"][self.course_num])

            key = self.scene.key
            # コース選択
            if key.push & KEY_LEFT:
                self.course_num = (self.course_num - 1) % _MAX_COURSE
                self.load_course(self.course_num)
                game_status["course"] = self.course_num
                save_status(game_status, _FILENAME)
                self.planet_num.update_num()

            elif key.push & KEY_RIGHT:
                self.course_num = (self.course_num + 1) % _MAX_COURSE
                self.load_course(self.course_num)
                game_status["course"] = self.course_num
                save_status(game_status, _FILENAME)
                self.planet_num.update_num()

            # 画面の明るさ
            if key.push & KEY_UP:
                game_status["brightness"] += 1
                if game_status["brightness"] == LCD_BRIGHTNESS_MAX:
                    game_status["brightness"] = LCD_BRIGHTNESS_MAX - 1
                lcd.brightness(game_status["brightness"])
                save_status(game_status, _FILENAME)

            elif key.push & KEY_DOWN:
                game_status["brightness"] -= 1
                if game_status["brightness"] < 0:
                    game_status["brightness"] = 0
                lcd.brightness(game_status["brightness"])
                save_status(game_status, _FILENAME)


class TitleNums(SpriteContainer):
    """タイトル画面 コース選択時のラップ表示"""

    def __init__(self):
        super().__init__()
        super().init_params("title-lap", 100, 20, 100)
        self.nums = []

    def enter(self):
        super().enter()
        x = 0
        for i in range(6):
            s = TitleNum((_CHR_TITLENUM, _REC_NUM_W, _REC_NUM_H), x, 0, 0)
            x += _REC_NUM_W + (i & 1) * 6
            self.add_child(s)
            self.nums.append(s)
            s.enter()

    def update_num(self, num):
        for i in range(5, -1, -1):
            val = num % 10
            num //= 10
            self.nums[i].set_num(val)


class PlanetNum(SpriteContainer):
    """タイトル画面 コース番号表示"""

    def __init__(self):
        super().__init__()
        super().init_params("planet-num", 158, -4, 100)

    def enter(self):
        super().enter()

        self.num = TitleNum((_CHR_TITLENUM, _REC_NUM_W, _REC_NUM_H), 0, 0, 0)
        self.add_child(self.num)
        self.num.enter()

    def update_num(self):
        self.num.set_num(game_status["course"] + 1)


class TitleNum(Sprite):
    """数値スプライト
    Params:
        font(tupple): chr, width, height
        x(int):
        y(int):
        val(int): 初期数値
    """

    def __init__(self, font, x, y, val):
        super().__init__()
        super().init_params(font[0] + val, "num", x, y, _MES_Z, font[1], font[2])
        self.font = font

    def set_num(self, val):
        self.chr_no = self.font[0] + val


class ResultRecords(SpriteContainer):
    """リザルト画面 レコード表示"""

    def __init__(self):
        super().__init__()
        self.init_params(
            "result records",
            72,
            0,
            _MES_Z,
        )

    def enter(self):
        super().enter()

        for i in range(3):
            self.add_child(
                Sprite()
                .init_params(_CHR_RESULTS + i, "results", i * 32, 0, _MES_Z, 32, 32)
                .enter()
            )

        self.add_child(ResultsNums()).enter()

        blank = 0
        for i in range(4):
            if i == 3:
                blank = 2
            self.add_child(
                Sprite()
                .init_params(
                    _CHR_LAP1 + i, "lap", -60, i * 22 + 38 + blank, _MES_Z, 64, 16
                )
                .enter()
            )

        # アニメ
        self.anime = Animator("anime", self.event, inout_elastic)
        self.anime.attach()
        self.y = 140
        self.anime.start = self.y
        self.anime.delta = -134
        self.anime.total_frame = 30
        self.anime.play()

    def action(self):
        super().action()

        if self.anime.is_playing:
            self.y = int(self.anime.value)

    def leave(self):
        super().leave()

        self.anime.stop()
        self.anime.detach()


class ResultsNums(SpriteContainer):
    """ラップレコード表示"""

    def __init__(self):
        super().__init__()
        super().init_params("results-lap", -8, 28, 100)

    def enter(self):
        super().enter()

        # 表示用ラップタイム
        times = self.stage.scene.director.values[0]
        # 失敗
        fail = self.stage.scene.director.values[2] - 1

        y = 10
        blank = 0
        for lap, time in enumerate(times):
            nums = []
            x = 25
            if lap == 3:
                blank = 5
            if lap == fail:
                # failアイコン表示
                self.add_child(
                    Sprite().init_params(_CHR_FAIL, "fail", 140, y, 100, 32, 16)
                ).enter()

            for i in range(6):
                s = TitleNum((_CHR_RESULTNUM, _REC_NUM_W, _REC_NUM_H), x, y + blank, 0)
                x += _REC_NUM_W + (i & 1) * 6
                self.add_child(s)
                nums.append(s)
                s.enter()
            self.update_num(nums, time)
            y += 21

        # ベストレコード
        best = self.stage.scene.director.values[1]
        if best:
            self.add_child(
                Sprite().init_params(_CHR_NEW, "new", 140, 75, 100, 32, 16)
            ).enter()

    def update_num(self, nums, time):
        for i in range(5, -1, -1):
            val = time % 10
            time //= 10
            nums[i].set_num(val)


class Lap(ThreadSpriteContainer):
    """周回数・タイム表示"""

    def __init__(self):
        super().__init__("lap", _LAP_X, _LAP_Y, _MES_Z)

    def enter(self):
        super().enter()

        # スタートタイム
        self.start_time = 0
        # ラップ
        self.lap_count = 0
        self.lap_time = [0] * 3  # 3周
        self.disp_time = [0] * 4  # 3周+トータル
        # 表示用ラップタイムを共有
        self.stage.scene.director.values[0] = self.disp_time  # 表示用ラップタイム
        self.stage.scene.director.values[1] = False  # ベスト更新

        # ラップ表示
        self.lap_nums = Nums(1, (_CHR_LAPNUM, _SP_W, _SP_H), _LAP_NUM_X, _LAP_NUM_Y)
        self.add_child(self.lap_nums)
        self.lap_nums.enter()
        # レコード表示 少し詰める
        self.rec_nums = Nums(
            6, (_CHR_NUM, _REC_NUM_W - 2, _REC_NUM_H), _REC_NUM_X, _REC_NUM_Y
        )
        self.add_child(self.rec_nums)

        self.event.add_listener([_EV_RECORD_LAP, self, True])
        self.event.add_listener([_EV_REVERSE, self, True])

        self.show_once = 1  # １回だけ表示

    def show(self, frame_buffer, images, x, y):
        if self.active:
            ### 描画スレッドに送らない
            if self.show_once > 0:
                x += self.x
                y += self.y

                # "lap"
                frame_buffer.blit(images[_CHR_LAP], x, y, def_alpha_color)
                # "time"
                frame_buffer.blit(
                    images[_CHR_TIME], x + _TIME_X, y + _TIME_Y, def_alpha_color
                )

                # 子スプライト 数字
                for sp in self.sprite_list:
                    sp.show(frame_buffer, images, x, y)

                self.show_once -= 1

    def ev_record_lap(self, type, sender, option):
        """更新: 周回数・タイム"""
        self.show_once = 1  # 1回だけ表示

        if self.lap_count == 0:
            # 計測開始
            self.start_time = ticks_ms()
            self.rec_nums.enter()  # 00 00 00 表示
        else:
            time = ticks_ms()
            self.lap_time[self.lap_count - 1] = time - self.start_time
            self.start_time = time

            # 表示用に加工
            d = self.conv_time(self.lap_time[self.lap_count - 1])
            self.disp_time[self.lap_count - 1] = d
            self.rec_nums.update_num(d)
            self.stage.readygo.countup()  # ラップ更新

        # 終了
        if self.lap_count == 3:
            self.event.post(
                [
                    _EV_FINISH,
                    EV_PRIORITY_MID,
                    30 * 2,
                    self,
                    5,  # 通常
                ]
            )
            # トータルを追加
            total = self.lap_time[0] + self.lap_time[1] + self.lap_time[2]
            self.disp_time[3] = self.conv_time(total)

            # ベストレコード更新
            if self.stage.mode & 2 != 2:
                self.stage.scene.director.values[1] = self.update_best_record(total)
            else:
                self.stage.scene.director.values[1] = False
        else:
            self.lap_count += 1
            self.lap_nums.update_num(self.lap_count)

    def ev_reverse(self, type, sender, option):
        """逆走"""
        if self.lap_count > 0:
            self.lap_count -= 1
            self.stage.readygo.countdown()  # ひとつ戻る

        self.show_once = 1
        self.lap_nums.update_num(self.lap_count)

    def conv_time(self, val):
        """msを 分:秒:ミリ秒表示 に変換"""
        m = val // 1000 // 60
        val -= m * 1000 * 60
        s = val // 1000
        ms = val % 1000 // 10

        return m * 10000 + s * 100 + ms

    def update_best_record(self, current):
        """ベストレコード"""
        course_num = game_status["course"]
        if self.stage.mode & 1 == 0:
            best = game_status["bestlap"][course_num]
        else:
            best = game_status["bestlap_ex"][course_num]

        if current < best:
            if self.stage.mode & 1 == 0:
                game_status["bestlap"][course_num] = current  # ミリ秒
                game_status["displap"][course_num] = self.conv_time(current)  # 表示用
            else:
                game_status["bestlap_ex"][course_num] = current  # ミリ秒
                game_status["displap_ex"][course_num] = self.conv_time(
                    current
                )  # 表示用
            return True

        return False

    def fix_pause_time(self, time):
        """ポーズ中の経過時間を引く"""
        self.lap_time[self.lap_count - 1] -= time


class Nums(ThreadSpriteContainer):
    """数値表示コンテナ
    2桁毎にスペース 00 00 00

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

    def enter(self):
        super().enter()

        # 数字スプライト 2桁毎にスペース
        x = 0
        for i in range(self.digit):
            s = Num(self.font, x, 0, 0)
            x += self.font[1] + (i & 1) * 4
            self.add_child(s)
            self.nums.append(s)
            s.enter()

    def show(self, frame_buffer, images, x, y):
        for sp in self.sprite_list:
            sp.show(frame_buffer, images, x + self.x, y + self.y)

    def update_num(self, num):
        for i in range(self.digit - 1, -1, -1):
            val = num % 10
            num //= 10
            self.nums[i].set_num(val)


class Num(ThreadSprite):
    """数字スプライト

    Params:
        font(tupple): chr, width, height
        x(int):
        y(int):
        val(int): 初期数値
    """

    def __init__(self, font, x, y, val):
        super().__init__(font[0] + val, "num", x, y, _MES_Z, font[1], font[2])
        self.font = font

    def show(self, frame_buffer, images, x, y):
        # 描画スレッドで処理しない
        frame_buffer.blit(images[self.chr_no], x + self.x, y + self.y, def_alpha_color)

    def set_num(self, val):
        self.chr_no = self.font[0] + val


class ReadyGo(ThreadSprite):
    """LAP更新表示"""

    def __init__(self):
        super().__init__(
            _CHR_READY,
            "update lap",
            _READY_X,
            _READY_Y,
            _MES_Z,
            _READY_W,
            _READY_H,
        )

    def enter(self):
        super().enter()
        self.duration = 30 * 3
        self.interval = 5
        self.active = self.visible = True

    def action(self):
        super().action()
        if self.active:
            if self.interval != 0 and self.duration % self.interval == 0:
                self.visible = not self.visible

            # 一定時間で消える
            self.duration -= 1
            if self.duration == 0:
                self.active = self.visible = False

    def show(self, frame_buffer, images, x, y):
        if self.active and self.visible:
            super().show(frame_buffer, images, x, y)

    def countup(self):
        """次の表示"""
        self.duration = 30 * 2
        self.interval = 5
        self.active = self.visible = True
        self.chr_no += 1

    def countdown(self):
        """逆走時巻き戻す"""
        if self.chr_no > _CHR_READY:
            self.chr_no -= 1


class PauseMes(ThreadSprite):
    """ポーズ中のメッセージ"""

    def __init__(self):
        super().__init__(_CHR_PAUSE_MES, "retry", 178, 119, _MES_Z, 80, 16)


### グローバル


# ステータスをロード
game_status = load_status(_FILENAME)

if game_status is None:
    # デフォルト
    game_status = {
        "mode": 0,  # ゲームモード 0 通常  1 EXモード  2 デバッグモード
        "course": 0,  # 現在のコース
        "bestlap": [3599999] * _MAX_COURSE,  # ミリ秒 59:59:99
        "bestlap_ex": [3599999] * _MAX_COURSE,
        "displap": [595999] * _MAX_COURSE,  # 表示用 59:59:99
        "displap_ex": [595999] * _MAX_COURSE,
        "brightness": 2,  # LCDの明るさ
    }
    save_status(game_status, _FILENAME)

# コースデータ
# ファイル名, (スタート座標 方向), (重力源座標), (ゴール方向範囲)
course_datafile = (
    ("course1.dat", (880, 32, 128), (496, 240), (65, 191)),
    ("course2.dat", (32, 128, 64), (784, 240), (1, 127)),
    ("course3.dat", (976, 368, 192), (496, 384), (129, 255)),
    ("course4.dat", (800, 32, 128), (496, 249), (65, 191)),
    ("course5.dat", (32, 224, 64), (784, 240), (1, 127)),
    ("course6.dat", (976, 368, 192), (496, 384), (129, 255)),
)

# LCDの明るさ
lcd.brightness(game_status["brightness"])

key = InputKey()
director = Director(
    (
        ("title", globals()["TitleScene"]),
        ("main", globals()["MainScene"]),
        ("results", globals()["ResultsScene"]),
    ),
    key,
)
director.push("title")
director.play()
