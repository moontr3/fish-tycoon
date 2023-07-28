############## INITIALIZATION ##############

import pygame as pg
import os
try:
    import easing_functions as easing
except:
    os.system('pip3 install easing-functions')
    import easing_functions as easing
import draw
import random
from numpy import sin, pi
import json

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
running = True
pg.display.set_caption('caption')
draw.def_surface = screen

halfx = windowx//2
halfy = windowy//2
halfpi = pi/2

# app variables

tutorial = True


# app functions

def lerp(a, b, t):
    return (1-t)*a + t*b

def dlerp(a: tuple, b: tuple, t):
    out = []
    for i in range(min(len(a), len(b))):
        out.append(lerp(a[i], b[i], t))
    return out


def read_json(fp):
    with open(fp, encoding='utf-8') as f:
        return json.load(f)

def write_json(fp, data):
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(data, fp)
    

def set_dragging(state: bool = True):
    global game
    game.dragging = state

def get_dragging():
    return game.dragging

def off_tutorial():
    global tutorial
    tutorial = False

def choose_type(shine=False):
    fishes = []
    for i in fish:
        if (not shine) or (shine and i.stars >= 2):
            for j in range(i.rareness):
                fishes.append(i)
    return random.choice(fishes)


def add_fish_p(fx):
    game.add_fish_p(fx)

def catch(type):
    game.inventory.append(type)
    game.bin_scale = 1.0

def capacity_remaining(count_fp=True):
    return game.capacity - (len(game.inventory)+(len(game.fish_p) if count_fp else 0))


def load_locale(locale):
    global lang
    lang = read_json(f'res/locale/{locale}.json',)

locale = 'ru-ru'
load_locale(locale)


# app classes

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
        if lmb_down and self.hovered:
            self.pressed = True
        if not self.pressed and (not self.hovered or lmb_up):
            self.pressed = False


class FishType:
    def __init__(self, key, size, image, rareness, rareness_increase, boid_size, cost, stars):
        self.key = key
        self.size = size
        self.image = image
        self.rareness = rareness
        self.rareness_decrease = rareness_increase
        self.boid_min = boid_size[0]
        self.boid_max = boid_size[1]
        self.cost = cost
        self.stars = stars


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


class Water:
    def __init__(self, size, still):
        self.still = still
        self.refill(size)

    # regenerates the whole thing
    def refill(self,size):
        if not self.still:
            self.x = size[0]
            self.y = size[1]

            self.big = random.random()*pi
            self.small = random.random()*pi
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

        self.buttons = [
            BtmBrButton('inventory.png', 'inventory',0,self.regen_dict_inv),
            BtmBrButton('shine_ball.png', 'shine',1,self.regen_dict_inv),
            BtmBrButton('settings.png', 'settings',2,self.regen_dict_inv),
        ]
        self.overlay = None
        self.dragging = False

    # adds the effect (particles and all that stuff)
    def add_fish_p(self, fx):
        self.fish_p.append(fx)

    # regenerates the dict_inv
    def regen_dict_inv(self):
        counted = []
        for i in self.inventory:
            if i.key not in counted:
                counted[i.key] = 0
            counted[i.key] += 1

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

    # draws the gui
    def draw_gui(self):
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

    # updates the game
    def update(self):
        old_inv = self.inventory
        # boid spawning
        self.spawn_after -= 1
        if self.spawn_after <= 0:
            self.type = choose_type()
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
        if self.overlay == None:
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

        # updating inventory
        if old_inv != self.inventory:
            self.regen_dict_inv()

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


# preparing

def load_game():
    # fish
    global fish
    data = read_json('res/json/fish.json')
    fish = [FishType(i, **data[i]) for i in data]

load_game()
game = Game()


# main loop

while running:

############## INPUT ##############

    events = pg.event.get()
    mouse_pos = pg.mouse.get_pos()
    mouse_pos = [
        mouse_pos[0]/screenx*windowx,
        mouse_pos[1]/screeny*windowy
    ]
    mouse_press = pg.mouse.get_pressed(5)
    mouse_moved = pg.mouse.get_rel()
    lmb_down = False
    lmb_up = False
    pressed = []



############## PROCESSING EVENTS ##############

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



############## UPDATING SCREEN ##############

    game.update()
    game.draw()

    # resizing the screen surface to match with the window resolution
    surface = pg.transform.smoothscale(screen, (screenx, screeny))
    window.blit(surface, (0,0))
    pg.display.flip()
    clock.tick(fps)