############## INITIALIZATION ##############

import pygame as pg
import os
import draw
import random
import json

try:
    import easing_functions as easing
except:
    os.system('pip3 install easing-functions')
    import easing_functions as easing

try:
    from numpy import sin, pi
except:
    os.system('pip3 install numpy')
    from numpy import sin, pi

pg.init()

# game size
windowx = 1280
windowy = 720
# window size, changes on resize
screenx = 1280
screeny = 720

clock = pg.time.Clock()
fps = 60

window = pg.display.set_mode((screenx,screeny), pg.RESIZABLE)
screen = pg.Surface((windowx, windowy))
pg.mouse.set_visible(False)
running = True
pg.display.set_caption('caption')
draw.def_surface = screen

halfx = windowx//2
halfy = windowy//2
halfpi = pi/2

# app variables

tutorial = True
rod_pos = [0,0]
dfps = 0.0
show_fps = False


# app functions

# linear interpolation between two one-d points
def lerp(a, b, t):
    return (1-t)*a + t*b

# linear interpolation between two coordinates in any dimension
def dlerp(a: tuple, b: tuple, t):
    out = []
    for i in range(min(len(a), len(b))):
        out.append(lerp(a[i], b[i], t))
    return out


# read unencrypted json
def read_json(fp):
    with open(fp, encoding='utf-8') as f:
        return json.load(f)

# write unencrypted json
def write_json(fp, data):
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(data, fp)


# game functions

# enable or disable dragging, used for correct handling of the fish dragging
def set_dragging(state: bool = True):
    global game
    game.dragging = state

# returns whether the player is currently dragging a fish
def get_dragging():
    return game.dragging

# returns inventory dictionary
def get_inv():
    return game.dict_inv

# disables the tutorial
def off_tutorial():
    global tutorial
    tutorial = False


# returns a random FishType according to the level (the higher the level, the rarer the fish)
def choose_type(level=1, shine=False):
    fishes = []
    level -= 1
    for i in fish:
        if (not shine) or (shine and i.stars >= 2):
            for j in range(i.rareness+(i.rareness_increase*(level-1))):
                fishes.append(i)
    return random.choice(fishes)

# adds this flying fish thingie (FishParticle)
def add_fish_p(fx):
    game.add_fish_p(fx)

# catches a fish and adds it to the inventory
def catch(type):
    game.inventory.append(type)
    game.bin_scale = 1.0
    game.level.add(random.randint([5,50,150][type.stars-1], [10,80,200][type.stars-1]))
    game.regen_dict_inv()

# opens a menu 
def set_menu(menu):
    global game
    game.overlay = menu()

# returns how much space is left in inventory
# count_fp == True then FishParticle will also be counted as an item in inventory
def capacity_remaining(count_fp=True):
    return game.capacity - (len(game.inventory)+(len(game.fish_p) if count_fp else 0))

# returns inventory capacity
def capacity():
    return game.capacity

# returns whether the menu is opened or not
def menu_opened():
    return game.overlay != None

# loads a language and applies it
def load_locale(locale):
    global lang
    lang = read_json(f'res/locale/{locale}.json',)

locale = 'ru-ru'
load_locale(locale)


# app classes

# inventory
class Inventory:
    def __init__(self):
        self.scroll_offset = 0
        self.scroll_vel = 0
        self.inv = {}
        self.prev_len = 0
        self.size = 0
        self.update_btn_rect(windowy)

    def update_btn_rect(self, y):
        self.btn_rect = pg.Rect(windowx-150, y+10, 140, 20)

    def draw(self, y):
        # drawing title
        size = draw.text(lang['inventory'], (10,y+5), size=24)[0]+20
        cur_capacity = capacity()
        draw.text(f'{cur_capacity-capacity_remaining(False)}/{cur_capacity}', (size, y+9), (180,180,180))

        # drawing items
        ongoing = self.scroll_offset+10
        for i in self.inv:
            rect = pg.Rect(ongoing, y+40, 100, 150)
            amount = self.inv[i]
            fish_type = dict_fish[i]
            
            # bg
            pg.draw.rect(screen, (240,230,200) if not (rect.collidepoint(mouse_pos) and mouse_press[0]) else (200,190,160),rect, 0, 7)
            pg.draw.rect(screen, (150,130,90),rect, 2, 7)

            # info
            draw.image(fish_type.image, (rect.centerx,rect.top+50), (80,80), 'm', 'm')
            draw.text(lang[f'fish-{i}'], (rect.centerx,rect.bottom-60), (0,0,0), 12, h='m')

            # cost
            size = draw.get_text_size(str(fish_type.cost),14)[0]+20
            draw.image('coin.png', (rect.centerx-size//2,rect.bottom-42), (14,14))
            draw.text(str(fish_type.cost), (rect.centerx+size//2,rect.bottom-43), (0,0,0), 14, h='r', opacity=200)
            
            # stars
            ongoing_stars = rect.left+8
            for i in range(fish_type.stars):
                draw.image('star.png', (ongoing_stars, rect.bottom-8), (15,15), v='b')
                ongoing_stars += 17

            # amount
            size = draw.get_text_size(f'x{amount}', 14)[0]+10
            size_rect = pg.Rect(rect.right-size, rect.bottom-20, size, 20)
            pg.draw.rect(screen, (150,130,90),size_rect,border_top_left_radius=4, border_bottom_right_radius=4)
            draw.text(f'x{amount}', (size_rect.centerx, size_rect.centery-1),(0,0,0), 14, h='m', v='m')

            ongoing += 110

        # drawing button
        pg.draw.rect(screen, (240,230,200) if not (self.btn_hovered and mouse_press[0]) else (200,190,160),self.btn_rect, 0, 14)
        pg.draw.rect(screen, (150,130,90),self.btn_rect, 2, 14)
        draw.text(lang['sell-all'], (self.btn_rect.centerx, self.btn_rect.centery-1), (0,0,0), size=14, h='m', v='m')
        draw.text(lang['sell-one'], (windowx-165, self.btn_rect.centery-1), (200,200,200), size=16, h='r', v='m')

    def update(self, y):
        # updating size
        self.inv = get_inv()
        if len(self.inv) != self.prev_len:
            self.prev_len = len(self.inv)
            self.size = max(0, len(self.inv)*110+10-windowx)
        if self.btn_rect.top-10 != y:
            self.update_btn_rect(y)

        # scrolling
        if mouse_scroll != 0.0:
            self.scroll_vel -= mouse_scroll*15

        if self.scroll_offset < 0:
            self.scroll_offset = 0
        if self.scroll_offset > self.size:
            self.scroll_offset = self.size

        self.scroll_offset += self.scroll_vel
        self.scroll_vel /= 1.2

        # selling one
        ongoing = self.scroll_offset+10
        for i in self.inv:
            rect = pg.Rect(ongoing, y+40, 100, 150)
            
        # selling all
        self.btn_hovered = self.btn_rect.collidepoint(mouse_pos)


# experience manager (displays and handles the xp)
class LevelManager:
    def __init__(self):
        self.xp = 0
        self.vis_percentage = 0.0
        self.level = 1
        self.update_level()
        self.level_up = False
        self.level_up_key = 0.0
        self.old_level = 1
        self.level_up_end_key = 0.0

    # used to update the variables relating to self.xp
    # to add xp use self.add(amount)
    def update_level(self):
        # percentage and all that stuff
        old_lvl = self.level
        self.level = 1
        self.total_level_xp = 50
        self.level_xp = self.xp
        while self.level_xp > self.total_level_xp:
            self.level += 1
            self.level_xp -= self.total_level_xp
            self.total_level_xp += 30
        self.percentage = self.level_xp/self.total_level_xp
        
        # level up
        if self.level > old_lvl:
            self.level_up = True
            self.old_level = old_lvl

    # add xp
    def add(self, xp):
        self.xp += xp
        self.update_level()
    
    def draw(self):
        # shaking
        if self.level_up_key > 0.0:
            xoffset = random.randint(-int(self.level_up_key*6), int(self.level_up_key*6))
            yoffset = random.randint(-int(self.level_up_key*3), int(self.level_up_key*3))
        elif self.level_up_end_key > 0.0:
            xoffset = random.randint(-1,1)
            if random.random() > self.level_up_end_key:
                xoffset = 0
            yoffset = 0
        else:
            xoffset = 0
            yoffset = 0

        # bar
        bar_rect = pg.Rect(halfx-200+xoffset, 25+yoffset, 400, 8)
        cur_rect = pg.Rect(halfx-200+xoffset, 25+yoffset, self.vis_percentage*392+8, 8)
        pg.draw.rect(screen, (50,100,130), ((bar_rect.x, bar_rect.y+1), bar_rect.size), 0, 4)
        pg.draw.rect(screen, (80,160,210), bar_rect, 0, 4)
        pg.draw.rect(screen, (255,230,70), cur_rect, 0, 4)

        # text
        offset = halfx-(
            draw.get_text_size(f'{lang["level"]} {self.old_level}', 18)[0]+\
            draw.get_text_size(f'{int(self.vis_percentage*100)}%', 16)[0]
        )/2-5
        offset += draw.text(f'{lang["level"]} {self.old_level}', (offset, 40), size=18)[0]+10
        draw.text(f'{int(self.vis_percentage*100)}%', (offset, 41), size=16, opacity=200)

        # level up glow
        if self.level_up_key > 0:
            ease = easing.QuinticEaseIn(0,255,1).ease(self.level_up_key)
            draw.image('glow.png', bar_rect.center, (500,40), h='m', v='m', opacity=self.level_up_key*255)
            draw.image('glow.png', bar_rect.center, (600,80), h='m', v='m', opacity=ease)
        if self.level_up_end_key > 0:
            ease = easing.ExponentialEaseIn(0,255,1).ease(self.level_up_end_key)
            draw.image('glow.png', bar_rect.center, (500,40), h='m', v='m', opacity=ease)
            draw.image('glow.png', bar_rect.center, (600,80), h='m', v='m', opacity=ease)
        
            # level up text
            text_in_ease = easing.ExponentialEaseIn(1,0,1).ease(self.level_up_end_key)
            text_out_ease = easing.ExponentialEaseOut(0,1,1).ease(self.level_up_end_key)
            draw.text(str(self.level), (halfx, 50+text_in_ease*30), size=18+int(text_in_ease*48), opacity=text_out_ease*255, h='m')
            draw.text(lang['level_up'], (halfx, 70+text_in_ease*80), size=6+int(text_in_ease*16), opacity=text_out_ease*255, h='m')

    def update(self):
        # animation
        if self.level == self.old_level:
            self.vis_percentage += (self.percentage-self.vis_percentage)/7
        else:
            self.vis_percentage += (1.0-self.vis_percentage)/7
        
        # level up animation
        if self.level != self.old_level:
            if self.level_up_key < 1.0:
                self.level_up_key += 0.02
            else:
                self.level_up = False
                self.level_up_key = 0.0
                self.level_up_end_key = 1.0
                self.old_level = self.level
                self.vis_percentage = 0.0

        if self.level_up_end_key > 0.0:
            self.level_up_end_key -= 0.01


# button on the bottom of the screen
class BtmBrButton:
    def __init__(self, image, name, index, callback):
        self.image = image
        self.name = name
        self.callback = callback
        self.pressed = False
        self.rect = self.get_rect(index)
        self.hovered = False
        self.index = index
        self.key = 0.0
        self.pressed = False

    def get_rect(self, index):
        rect = pg.Rect(0,0, 48,48)
        rect.center = (40+index*65, windowy-40)
        return rect

    def draw(self):
        # text
        if self.key > 0.0:
            opacity_ease = easing.QuadEaseOut(0,255,1).ease(self.key)
            offset_ease = easing.QuadEaseOut(0,20,1).ease(self.key)
            draw.text(
                lang[self.name], (self.rect.center[0] if self.index != 0 else 15, self.rect.top-offset_ease),
                size=19, h='m' if self.index != 0 else 'l', v='b', opacity=int(opacity_ease)
            )
        else:
            offset_ease = 0
        # image
        draw.image(self.image, (self.rect.centerx, self.rect.centery-offset_ease/3), h='m', v='m')

    def update(self):
        # hovering
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered:
            if self.key < 1.0:
                self.key += 0.1
        elif self.key > 0.0:
            self.key -= 0.1

        # pressing
        if self.hovered and lmb_up:
            self.callback()

        if lmb_down and self.hovered:
            self.pressed = True
        if self.pressed and (not self.hovered or lmb_up):
            self.pressed = False

        if self.hovered and lmb_up and not menu_opened():
            set_menu(self.callback)


# fish that gets stored in inventory, gets choosed in a rng and all this
class FishType:
    def __init__(self, key, size, image, rareness, rareness_increase, boid_size, cost, stars):
        self.key = key
        self.size = size
        self.image = image
        self.rareness = rareness
        self.rareness_increase = rareness_increase
        self.boid_min = boid_size[0]
        self.boid_max = boid_size[1]
        self.cost = cost
        self.stars = stars


# fish that gets displayed on the screen
class Fish:
    def __init__(self, pos, flip: bool, fish_type):
        self.flip = flip
        self.type = fish_type
        self.size = self.type.size
        self.image = self.type.image
        self.hsize = self.size//2 # hsize stands for half size
        if self.flip:
            self.x = windowx+self.hsize
        else:
            self.x = -self.hsize
        self.y = pos*(windowy-350)+150
        self.y += random.randint(-20,20)
        self.sin = random.random()*3.14
        self.sin_strength = random.randint(5,15)
        self.sin_speed = random.random()/100+0.05
        self.removable = False
        self.dragging = False

        self.tutorial = tutorial
        if self.tutorial:
            off_tutorial()
            self.circle_size = 0.0
            self.step = 1
            self.text_opacity = 0.0

        self.update_rect()

    # updates the rect of the current fish
    def update_rect(self):
        self.rect = pg.Rect(0,0,self.size,self.size)
        sinval = sin(self.sin)*self.sin_strength if not self.dragging else 0
        self.rect.center = (self.x, self.y+sinval)
            
    # updates the fish
    def update(self):
        # if the fish is facing left and coming from the right
        if self.flip:
            # changing position and deleting if out of bounds
            self.x -= 1
            if (self.x < -self.hsize or self.y < 100)\
                and not self.dragging:
                    self.removable = True

            # showing tutorial
            if self.x < windowx-100 and self.tutorial:
                if self.circle_size < 1.0:
                    self.circle_size += 0.01
                if self.text_opacity < 1.0:
                    self.text_opacity += 0.04
        # if the fish is facing right and coming from the left
        else:
            # changing position and deleting if out of bounds
            self.x += 1
            if (self.x > windowx+self.hsize or self.y < 100)\
                and not self.dragging:
                    self.removable = True

            # showing tutorial
            if self.x > 100 and self.tutorial:
                if self.circle_size < 1.0:
                    self.circle_size += 0.01
                if self.text_opacity < 1.0:
                    self.text_opacity += 0.04

        # checking if we catched the fish
        if self.removable and self.y < 100:
            add_fish_p(FishParticle(self.type, (self.x, self.y), self.image, self.size, self.flip))

        # updates the position
        self.sin += self.sin_speed
        self.update_rect()

        # starting dragging
        hovered = self.rect.collidepoint(mouse_pos)
        if hovered and lmb_down and not get_dragging()\
            and capacity_remaining() > 0:
                self.dragging = True
                self.sin = 0
                set_dragging()
                if self.tutorial and self.step == 1:
                    self.step = 2
                    self.text_opacity = 0.0

        # dragging the fish
        if self.dragging:
            self.x = mouse_pos[0]
            self.y = mouse_pos[1]
            self.update_rect()
        
        # releasing the fish
        if lmb_up:
            if self.dragging:
                self.dragging = False
                self.sin = 0
                set_dragging(False)
            
    # draws the fish
    def draw(self):
        # image
        draw.image(self.image, self.rect.center, (self.size, self.size), h='m', v='m',
            flip=not self.flip, rotation=sin(self.sin*10)*10 if self.dragging\
            else sin(self.sin+1.3)*self.sin_strength * (-1 if not self.flip else 1)
        )

        # tutorial
        if self.tutorial:
            # circle
            if self.circle_size > 0:
                circle_ease = easing.ExponentialEaseOut(0,75,1).ease(self.circle_size)
                thickness_ease = easing.CubicEaseOut(1,7,1).ease(self.circle_size)
                pg.draw.circle(screen, (255,255,255), (self.x, self.y), 150-circle_ease, int(thickness_ease))
            # text
            if self.text_opacity > 0:
                opacity_ease = easing.SineEaseOut(0,255,1).ease(self.text_opacity)
                offset_ease = easing.QuadEaseOut(0,30,1).ease(self.text_opacity)
                draw.text(lang[f'tutorial-{self.step}'],
                    (self.x-70-offset_ease if self.flip else self.x+70+offset_ease, self.y),
                v='m', h='r' if self.flip else 'l', opacity=int(opacity_ease))


# y know when the fish is flying towards the bin? yep this is it
class FishParticle:
    def __init__(self, type, pos, image, size, flip):
        self.type = type
        self.flip = flip
        self.size = size
        self.image = image
        self.hsize = self.size//2 # hsize stands for half size
        self.x = pos[0]
        self.y = pos[1]
        self.start_pos = pos
        self.end_pos = (windowx-50, 50)
        self.key = 0
        self.vel = 25/abs(self.end_pos[0]-self.start_pos[0])+0.01
        self.removable = False
        self.sin = 0.0
            
    # updates the fish
    def update(self):
        self.key += self.vel
        if self.key >= 1.0:
            self.removable = True
            catch(self.type)

        # position and sinewave and all that stuff
        self.sin = sin(self.key*pi)
        pos = dlerp(self.start_pos, self.end_pos, self.key)
        self.x = pos[0]
        self.y = pos[1]
            
    # draws the fish
    def draw(self):
        draw.image(
            self.image, (self.x+self.sin*(abs(self.end_pos[0]-self.start_pos[0])/10), self.y-self.sin*50),
            (self.size, self.size), h='m', v='m', flip=not self.flip, opacity=min(1.0, (1-self.key)*5)*255
        )


# game background
class Water:
    def __init__(self, size, still):
        self.still = still
        self.refill(size)

    # regenerates the whole thing
    def refill(self,size):
        if not self.still:
            self.x = size[0]
            self.y = size[1]

            self.big = pi
            self.small = 0
            self.big_array = []
            self.small_array = []
            self.big_speed = random.random()*2+10
            self.small_speed = random.random()+5

            for i in range(self.x):
                self.big_array.append(sin(self.big/96)*3)
                self.big += self.big_speed
                self.small_array.append(sin(self.small/69)*2)
                self.small += self.small_speed

    def update(self):
        if not self.still:
            # big waves
            self.big_array.pop(0)
            self.big_array.append(sin(self.big/96)*3)
            self.big += self.big_speed

            # small faster waves
            for i in range(2):
                self.small_array.pop(0)
                self.small_array.append(sin(self.small/69)*2)
                self.small += self.small_speed

    def draw(self):
        screen.fill((0,100,150))

        if not self.still:
            # calculating points
            points = [self.small_array[i]+self.big_array[i] for i in range(self.x)]
            draw_points = [(index, i+85) for index, i in enumerate(points)]
            poly_points = draw_points+[(windowx, 0), (0,0)]
            
            # drawing
            pg.draw.polygon(screen, (90,180,240), poly_points)
            pg.draw.aalines(screen, (255,255,255), False, draw_points)
        else:
            # still water
            pg.draw.rect(screen, (90,180,240), pg.Rect(0,0,windowx, 80))
            pg.draw.line(screen, (255,255,255), (0,80), (windowx,80))


# main game with all buttonss, fish and all this
class Game:
    def __init__(self):
        self.spawn_speed = 300
        self.boid_spawn_speed = 100
        self.boid_size_boost = 1

        self.fish = []
        self.water = Water((windowx, windowy), False)
        self.boid_size = 0
        self.spawn_after = self.spawn_speed
        self.fish_p = []

        self.balance = 0
        self.bin_scale = 0.0
        self.full_inv_appeaeance = 0.0
        self.inventory = []
        self.dict_inv = {}
        self.capacity = 5
        self.level = LevelManager()

        self.buttons = [
            BtmBrButton('inventory.png', 'inventory',0,Inventory),
            BtmBrButton('shine_ball.png', 'shine',1,Inventory),
            BtmBrButton('up.png', 'upgrade',2,Inventory),
            BtmBrButton('settings.png', 'settings',3,Inventory),
        ]
        self.overlay = None
        self.dragging = False
        self.rod_pos = pg.mouse.get_pos()
        self.rod_offset = self.rod_pos[0]

        self.start_dim = 1.0
        self.dim_surface = pg.Surface((windowx,windowy))
        self.menu_key = 0.0
        self.menu_closing = False
        self.menu_ease = windowy

        self.play_bg_music()

    # starts playing background music
    def play_bg_music(self):
        pg.mixer.music.stop()
        pg.mixer.music.load('res/sounds/background.wav')
        pg.mixer.music.set_volume(0.4)
        pg.mixer.music.play(-1)

    # adds the effect (particles and all that stuff)
    def add_fish_p(self, fx):
        self.fish_p.append(fx)

    # regenerates the dict_inv
    def regen_dict_inv(self):
        self.dict_inv = {}
        for i in self.inventory:
            if i.key not in self.dict_inv:
                self.dict_inv[i.key] = 0
            self.dict_inv[i.key] += 1

    # updates the gui
    def update_gui(self):
        # bin animation
        if self.bin_scale > 0.0:
            self.bin_scale -= 0.04

        # full inventory notification
        if capacity_remaining() <= 0:
            if self.full_inv_appeaeance < 1.0:
                self.full_inv_appeaeance += 0.02
        elif self.full_inv_appeaeance > 0.0:
            self.full_inv_appeaeance -= 0.02

        # buttons
        for i in self.buttons:
            i.update()

        # xp bar
        self.level.update()

        # menu
        if self.overlay != None:
            # open animation
            if self.menu_key < 1.0 and not self.menu_closing:
                self.menu_key += 0.04
                self.menu_key = round(self.menu_key, 2)
            # close animation
            if self.menu_closing:
                self.menu_key -= 0.04
                if self.menu_key <= 0.0:
                    self.overlay = None
                    self.menu_closing = False
            # animating
            self.menu_ease = easing.QuarticEaseOut(0,1,1).ease(self.menu_key)
            self.menu_ease = windowy-self.menu_ease*200
            # closing menu
            if lmb_up and mouse_pos[1] < windowy-200:
                self.menu_closing = True
            # updating
            if self.overlay != None:
                self.overlay.update(self.menu_ease)
            

    # draws the gui
    def draw_gui(self):
        # full inventory notification
        if self.full_inv_appeaeance > 0.0:
            ease = easing.ExponentialEaseOut(0,50,1).ease(self.full_inv_appeaeance)
            size = draw.get_text_size(lang['full-bin'])[0]
            rect = pg.Rect(halfx-size/2-15,windowy-ease,size+30,40)
            pg.draw.rect(screen, (200,50,50), rect, 0, 7)
            draw.text(lang['full-bin'], rect.center, h='m', v='m')

        # buttons
        for i in self.buttons:
            i.draw()

        # menu
        if self.overlay != None:
            pg.draw.rect(screen, (30,30,30), pg.Rect(0,self.menu_ease, windowx,200))
            draw.image('shadow.png', (0,self.menu_ease-100), (windowx,100), opacity=self.menu_key*255)
            self.overlay.draw(self.menu_ease)

        # money counter
        draw.image('coin.png', (40,40), (32,32), h='m', v='m')
        draw.text(str(self.balance), (70,40), size=26, v='m')

        # bin
        if self.bin_scale > 0.0:
            size = 32+sin(self.bin_scale*pi)*10
        else:
            size = 32
        draw.image('bin.png', (windowx-40,40), (size,size), h='m', v='m')
        size = windowx-70
        size -= draw.text(str(self.capacity), (size,40), size=18, h='r', v='m')[0]
        size -= draw.text(f'/', (size,40), size=22, h='r', v='m')[0]+1
        draw.text(str(len(self.inventory)), (size,40), size=26, h='r', v='m')

        # xp level
        self.level.draw()

        # fishing rod
        draw.image('hook.png', self.rod_pos, (20,35), 'r','m')
        pg.draw.aaline(screen, (0,0,0), (self.rod_pos[0]-11, self.rod_pos[1]-17), (self.rod_offset-11, -1))

    # updates the game
    def update(self):
        old_inv = self.inventory
        if self.overlay == None:
            # boid spawning
            self.spawn_after -= 1
            if self.spawn_after <= 0:
                self.type = choose_type(level=self.level.level)
                self.boid_size = random.randint(
                    int(self.type.boid_min*self.boid_size_boost),
                    int(self.type.boid_max*self.boid_size_boost),
                )
                self.fish_spawn_time = random.randint(self.boid_spawn_speed-10, self.boid_spawn_speed+10)
                self.spawn_after = self.spawn_speed + self.boid_size*self.boid_spawn_speed
                self.position = random.random()
                self.flip = bool(random.randint(0,1))

            # individual fish from the boid spawning
            if self.boid_size > 0:
                self.fish_spawn_time -= 1
                if self.fish_spawn_time <= 0:
                    self.fish_spawn_time = random.randint(
                        self.boid_spawn_speed-(self.boid_spawn_speed/5),
                        self.boid_spawn_speed+(self.boid_spawn_speed/5)
                    )
                    self.fish.append(Fish(self.position, self.flip, self.type))
                    self.boid_size -= 1

            # updating game
            self.water.update()

            # updating fish
            out = []
            for i in self.fish:
                i.update()
                if not i.removable:
                    out.append(i)
            self.fish = out

            # updating effects
            out = []
            for i in self.fish_p:
                i.update()
                if not i.removable:
                    out.append(i)
            self.fish_p = out

        self.update_gui()

        # updaing fishing rod
        self.rod_pos = dlerp(self.rod_pos, init_pos, 0.15)
        self.rod_offset = lerp(self.rod_offset, self.rod_pos[0], 0.4)

        # updating inventory
        if old_inv != self.inventory:
            self.regen_dict_inv()

        # dimming screen when started
        if self.start_dim > 0.0:
            self.start_dim -= 0.01

    # draws the game
    def draw(self):
        self.water.draw()
        # fish
        for i in self.fish:
            i.draw()
        # effects
        for i in self.fish_p:
            i.draw()
        self.draw_gui()

        # dimming
        if self.start_dim > 0.0:
            self.dim_surface.fill((255,255,255))
            self.dim_surface.set_alpha(self.start_dim*255)
            screen.blit(self.dim_surface, (0,0))


# loading screen, doesn't actually load anything but there's a cool animation
class LoadingScreen:
    def __init__(self):
        self.frame = 0
        self.key = 0
        self.alpha = 0
        self.surface = pg.Surface((windowx,windowy))
        self.switch_key = 0.0
        self.switching = False

    def update_alpha(self):
        self.alpha = self.key*5 if self.key < 51 else min(255, (300-self.key)*5)

    def update(self):
        # updating frames
        if (self.frame != 1) or (self.frame == 1 and self.key < 51):
            self.key += 1
        if self.key > 300 or lmb_up: # pressed
            if self.frame >= 1:
                self.switching = True
            else:
                self.key = 0
                self.frame += 1

        # switching to the game
        if self.switching:
            self.switch_key += 0.02
        if self.switch_key >= 1.0:
            global game
            game = Game()

        # other things
        self.update_alpha()

    def draw(self):
        screen.fill((0,0,0))

        # 1st frame
        if self.frame == 0:
            draw.text('', (halfx,halfy-30), (255,60,60), size=40, h='m', v='m')
            draw.text('Loading screen!!!!', (halfx,halfy+30), (255,255,255), size=24, h='m', v='m')

        # 2nd frame
        elif self.frame == 1:
            draw.text(lang['click_to_start'], (halfx,windowy-50), size=20, h='m', v='m')

        # dimming screen
        if self.alpha < 255 and self.switch_key <= 0.0:
            a = 255-self.alpha
            self.surface.set_alpha(a)
            screen.blit(self.surface, (0,0))

        if self.switch_key > 0.0:
            ease = easing.ExponentialEaseIn(0,1,1).ease(self.switch_key)
            size = (50+ease*500+self.switch_key*500,50+ease*500+self.switch_key*500)
            draw.image('sparkle.png', (halfx,halfy), size, 'm', 'm', ease*100, ease*255, temp=True)
            self.surface.fill((255,255,255))
            self.surface.set_alpha(ease*255)
            screen.blit(self.surface, (0,0))


# preparing

def load_game():
    # fish
    global fish, dict_fish
    data = read_json('res/json/fish.json')
    fish = [FishType(i, **data[i]) for i in data]
    dict_fish = {i: FishType(i, **data[i]) for i in data}

load_game()
game = LoadingScreen()


# main loop

while running:

############## INPUT ##############

    events = pg.event.get()
    init_pos = pg.mouse.get_pos()
    init_pos = [
        init_pos[0]/screenx*windowx,
        init_pos[1]/screeny*windowy
    ]
    mouse_press = pg.mouse.get_pressed(5)
    mouse_moved = pg.mouse.get_rel()
    mouse_scroll = 0.0
    if type(game) == Game:
        mouse_pos = game.rod_pos
    else:
        mouse_pos = init_pos
    lmb_down = False
    lmb_up = False
    pressed = []

    # processing events
    for event in events:
        if event.type == pg.QUIT:
            running = False 

        if event.type == pg.VIDEORESIZE:
            # resizing the window (not the screen)
            screenx = event.w
            screeny = event.h
            if screenx <= 640:
                screenx = 640
            if screeny <= 480:
                screeny = 480
            window = pg.display.set_mode((screenx,screeny), pg.RESIZABLE)

        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                lmb_down = True

        if event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                lmb_up = True

        if event.type == pg.KEYDOWN:
            pressed.append(event.key)
            if event.key == pg.K_F3:
                show_fps = not show_fps

        if event.type == pg.MOUSEWHEEL:
            mouse_scroll = event.y

    # updating screen
    game.update()
    game.draw()

    # showing fps
    if show_fps:
        draw.text(f'FPS: {dfps}', (5,3), (0,0,0))
        draw.text(f'FPS: {dfps}', (5,2))

    # resizing the screen surface to match with the window resolution
    surface = pg.transform.smoothscale(screen, (screenx, screeny))
    window.blit(surface, (0,0))
    pg.display.flip()
    clock.tick(fps)
    dfps = round(clock.get_fps(), 1)