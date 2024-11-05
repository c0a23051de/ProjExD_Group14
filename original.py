import os
import pygame as pg
import random
import sys
import time
import math

WIDTH, HEIGHT = 1100, 650
DELTA = {pg.K_w:   ( 0,-5),
         pg.K_s: ( 0,+5),
         pg.K_a: (-5, 0),
         pg.K_d:(+5, 0),
         }

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Ball:
    def __init__(self, pos: tuple[int, int], target_pos: tuple[int, int]):
        self.image = pg.transform.rotozoom(pg.image.load("fig/ball.png"), 0, 0.1)
        self.rect = self.image.get_rect(center=pos)

        # こうかとんに向かって進むようにするための速度を計算
        dx, dy = target_pos[0] - pos[0], target_pos[1] - pos[1]
        distance = math.hypot(dx, dy)
        self.speed = (dx / distance * 5, dy / distance * 5)  # 速度の正規化

    def update(self, screen: pg.Surface):
        """
        ボールを画面内で移動させる
        """
        self.rect.move_ip(self.speed)
        screen.blit(self.image, self.rect)

        # 画面外に出たボールを削除
        if self.rect.left > WIDTH or self.rect.right < 0 or self.rect.top > HEIGHT or self.rect.bottom < 0:
            return False  # 削除フラグ
        return True
    
# ボールとこうかとんの円形当たり判定を実装
def is_colliding(circle1, circle2):
    # 2つの円の中心間の距離を計算
    distance = math.hypot(circle1.centerx - circle2.centerx, circle1.centery - circle2.centery)
    # 2つの円の半径の合計が距離以下であれば衝突
    return distance <= (circle1.width / 2 + circle2.width / 2) * 0.8

def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    yoko, tate = True, True
    # 左側の移動制限
    # オブジェクトの左端が画面幅の2/5よりも左に出ている場合、または
    # オブジェクトの右端が画面幅の3/5よりも右に出ている場合は
    # 横方向の移動を制限する
    if obj_rct.left < WIDTH * 1 / 5 or WIDTH * 3 / 5 < obj_rct.right:
        yoko = False

    # 縦方向の移動制限
    # オブジェクトの上端が画面の上（0）よりも上に出ている場合、または
    # オブジェクトの下端が画面の高さを超えている場合は
    # 縦方向の移動を制限する
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    
    # 横方向と縦方向の移動制限の結果を返す
    return yoko, tate

class Bird:
    delta = {  
        pg.K_w: (0, -5),
        pg.K_s: (0, +5),
        pg.K_a: (-5, 0),
        pg.K_d: (+5, 0),
        
    }
    img0 = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    img = pg.transform.flip(img0, True, False)  
    imgs = {  
        (+5, 0): img,  
        (+5, -5): pg.transform.rotozoom(img, 45, 0.9),  
        (0, -5): pg.transform.rotozoom(img, 90, 0.9),  
        (-5, -5): pg.transform.rotozoom(img0, -45, 0.9),  
        (-5, 0): img0,  
        (-5, +5): pg.transform.rotozoom(img0, 45, 0.9),  
        (0, +5): pg.transform.rotozoom(img, -90, 0.9),  
        (+5, +5): pg.transform.rotozoom(img, -45, 0.9),  
    }

    def __init__(self, xy: tuple[int, int]):
        self.img = __class__.imgs[(+5, 0)]
        self.rct: pg.Rect = self.img.get_rect()
        self.rct.center = xy

    def change_img(self, num: int, screen: pg.Surface):
        self.img = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = __class__.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)

def gameover(screen):
    black = pg.Surface((WIDTH, HEIGHT))
    pg.draw.rect(black, (0, 0, 0), (0, 0, WIDTH, HEIGHT))
    black.set_alpha(100)
    screen.blit(black, (0, 0))
    cry_img = pg.transform.rotozoom(pg.image.load("fig/8.png"), 0, 1.2)
    cry_rct = cry_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
    screen.blit(cry_img, cry_rct)
    fonto = pg.font.Font(None, 80)
    txt = fonto.render("GameOver", True, (0, 150, 255))
    txt_rct = txt.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(txt, txt_rct)
    pg.display.update()
    time.sleep(2)
    pg.quit()  # Pygameを終了
    sys.exit()  # プログラムを終了

class Enemy:
    def __init__(self, screen):
        self.screen = screen
        self.countdown = 5  # 5秒のカウントダウン
        self.is_shooting = False  # レーザー発射中かどうか
        self.laser_image = pg.transform.rotozoom(pg.image.load("fig/laser.png"), 0, 1)  # 0.5に変更してサイズを半分に
        self.laser_rect = self.laser_image.get_rect(center=(WIDTH - 150, HEIGHT // 2))  # レーザーの位置

    def update(self):
        if self.is_shooting:
            self.screen.blit(self.laser_image, self.laser_rect)  # レーザーを描画

        if self.countdown > 0:
            self.countdown -= 1 / 50  # カウントダウンを1/50秒毎に減らす
        else:
            self.is_shooting = True  # レーザーを発射
            self.countdown = 5  # カウントダウンをリセット

    def draw_countdown(self):
        font = pg.font.Font(None, 60)
        countdown_text = font.render(f"{int(self.countdown)}", True, (255, 0, 0))
        text_rect = countdown_text.get_rect(center=(WIDTH - 150, HEIGHT // 2 - 50))
        self.screen.blit(countdown_text, text_rect)


def enemy(num, screen, enemy_instance, bird: Bird):
    if num == 1:
        en_img1 = pg.transform.rotozoom(pg.image.load("fig/DQMJ2.webp"), 0, 0.6)
        en_rct1 = en_img1.get_rect()
        en_rct1.centerx = 150
        en_rct1.centery = HEIGHT / 2
        screen.blit(en_img1, en_rct1)
        stage1()

    elif num == 2:
        en_img2 = pg.transform.rotozoom(pg.image.load("fig/en1.png"), 0, 0.4)
        en_rct2 = en_img2.get_rect()
        en_rct2.centerx = WIDTH - 150
        en_rct2.centery = HEIGHT / 2
        screen.blit(en_img2, en_rct2)
        enemy_instance.update()  # 敵の更新
        enemy_instance.draw_countdown()  # カウントダウンを描画

        # レーザーをボールのように動かす処理を追加
        if enemy_instance.is_shooting:
            enemy_instance.laser_rect.move_ip(-20, 0)  # 左に移動
            if enemy_instance.laser_rect.left < 0:  # 画面外に出たらリセット
                enemy_instance.is_shooting = False
                enemy_instance.laser_rect.center = (WIDTH - 150, HEIGHT // 2)

            # レーザーとこうかとんの衝突判定
            if is_colliding(enemy_instance.laser_rect, bird.rct)* 0.1:
                gameover(screen)

    elif num == 3:
        en_img3 = pg.transform.rotozoom(pg.image.load("fig/en5.png"), 0, 1)
        en_img4 = pg.transform.rotozoom(pg.image.load("fig/en6.png"), 0, 1)
        en_rct3 = en_img3.get_rect()
        en_rct3.centerx = 150
        en_rct3.centery = HEIGHT / 2
        en_rct4 = en_img4.get_rect()
        en_rct4.centerx = WIDTH - 150
        en_rct4.centery = HEIGHT / 2
        screen.blit(en_img3, en_rct3)
        screen.blit(en_img4, en_rct4)
        stage3()

    elif num == 4:
        en_img5 = pg.transform.rotozoom(pg.image.load("fig/en7.png"), 0, 0.6)
        en_rct5 = en_img5.get_rect()
        en_rct5.centerx = 150
        en_rct5.centery = HEIGHT / 2
        screen.blit(en_img5, en_rct5)
        stageEX()


def stage1():
    return 0

def stage2(screen: pg.Surface, bird: Bird, balls: list):###################################st2
    # 8%の確率で新しいボールを生成する
    if random.random() < 0.1:
        # ボールの発射位置を画面右端の上下50ピクセル以内でランダムに設定
        launch_y = HEIGHT // 2 + random.randint(-50, 50)
        # 新しいボールを生成し、こうかとんの中心をターゲットに設定
        ball = Ball((WIDTH - 100, launch_y), bird.rct.center)
        # ボールリストに生成したボールを追加
        balls.append(ball)
    for ball in balls[:]:
        if not ball.update(screen):
            balls.remove(ball)
        if is_colliding(ball.rect, bird.rct):
            gameover(screen)
            return

def stage3():
    return 0

def stageEX():
    return 0

def timescore():
    return 0

def skill():
    return 0

def main():
    pg.init()  # Pygameの初期化
    pg.display.set_caption("避けろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.transform.rotozoom(pg.image.load("fig/bg.png"), 0, 1.9)
    bird = Bird([WIDTH / 2, HEIGHT / 2])
    stage = 2

    enemy_instance = Enemy(screen)  # 敵のインスタンスを生成

    clock = pg.time.Clock()
    tmr = 0
    balls = []  # ボールのリスト

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
        screen.blit(bg_img, [0, 0]) 

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        enemy(stage, screen, enemy_instance, bird)  # 敵にインスタンスとこうかとんを渡す
        
        if stage == 2:
            stage2(screen, bird, balls)  # stage2にscreen, bird, ballsを渡す

        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    main()