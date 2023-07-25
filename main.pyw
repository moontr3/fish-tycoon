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

def choose_type():
    fishes = []
    for i in fish:
        for j in range(i.rareness):
            fishes.append(i)
    return random.choice(fishes)


def add_fx(fx):
    game.add_fx(fx)


def load_locale(locale):
    global lang
    lang = read_json(f'res/locale/{locale}.json',)

locale = 'ru-ru'
load_locale(locale)


# app classes

class FishType:
    def __init__(self, key, size, image, rareness, rareness_increase, boid_size):
        self.key = key
        self.size = size
        self.image = image
        self.rareness = rareness
        self.rareness_decrease = rareness_increase
        self.boid_min = boid_size[0]
        self.boid_max = boid_size[1]


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
            add_fx(FishParticle((self.x, self.y), self.image, self.size, self.flip))

        # updates the position
        self.sin += self.sin_speed
        self.update_rect()

        # starting dragging
        hovered = self.rect.collidepoint(mouse_pos)
        if hovered and lmb_down and not get_dragging():
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
    def __init__(self, pos, image, size, flip):
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


class Game:
    def __init__(self):
        self.spawn_speed = 300
        self.boid_spawn_speed = 100
        self.boid_size_boost = 1

        self.fish = []
        self.boid_size = 0
        self.spawn_after = self.spawn_speed
        self.fx = []

        self.dragging = False
        self.stopped = False

    def add_fx(self, fx):
        self.fx.append(fx)

    def update(self):
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

        if self.boid_size > 0:
            self.fish_spawn_time -= 1
            if self.fish_spawn_time <= 0:
                self.fish_spawn_time = random.randint(
                    self.boid_spawn_speed-(self.boid_spawn_speed/5),
                    self.boid_spawn_speed+(self.boid_spawn_speed/5)
                )
                self.fish.append(Fish(self.position, self.flip, self.type))
                self.boid_size -= 1

        if not self.stopped:
            out = []
            for i in self.fish:
                i.update()
                if not i.removable:
                    out.append(i)
            self.fish = out

            out = []
            for i in self.fx:
                i.update()
                if not i.removable:
                    out.append(i)
            self.fx = out

    def draw(self):
        for i in self.fish:
            i.draw()
        
        for i in self.fx:
            i.draw()


# preparing

def load_fish():
    global fish
    data = read_json('res/json/fish.json')
    fish = [FishType(i, **data[i]) for i in data]

load_fish()
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

    screen.fill((0,0,0))



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
            if event.key == pg.K_ESCAPE:
                game.stopped = not game.stopped



############## UPDATING SCREEN ##############

    game.update()
    game.draw()

    # resizing the screen surface to match with the window resolution
    surface = pg.transform.smoothscale(screen, (screenx, screeny))
    window.blit(surface, (0,0))
    pg.display.flip()
    clock.tick(fps)