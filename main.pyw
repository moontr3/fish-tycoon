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

try:
    import cryptocode
except:
    os.system('pip3 install cryptocode')
    import cryptocode

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
rod_pos = [0,0]
dfps = 0.0
show_fps = False
still_water = False
smoothscale = True


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

# read encrypted json
def read(fp):
    with open(fp, encoding='utf-8') as f:
        data = f.read()
        ddata = cryptocode.decrypt(data[8:], data[0:8])
        return json.loads(ddata)
    
# write encrypted json and return the key
def write(fp, data): 
    with open(fp, 'w', encoding='utf-8') as f:
        key = ''.join(random.choices('1234567890qwertyuiopasdfghjklzxcvbnm', k=8))
        data = key+cryptocode.encrypt(json.dumps(data), key)
        f.write(data)
        return key


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

# sells all fish in inventory
def sell_all():
    global game
    for i in game.dict_inv:
        amount = game.dict_inv[i]
        fish_type = dict_fish[i]
        game.balance += fish_type.cost*amount
    game.inventory = []
    game.regen_dict_inv()

# sells one fish or the whole batch
def sell(key, is_batch=False):
    global game
    fish_type = dict_fish[key]
    # batch selling
    if is_batch:
        game.balance += fish_type.cost*game.dict_inv[key]
        new = []
        for i in game.inventory:
            if i.key != key:
                new.append(i)
        game.inventory = new
    # one selling
    else:
        for i in game.inventory:
            if i.key == key:
                game.balance += fish_type.cost
                game.inventory.reverse()
                game.inventory.remove(i)
                game.inventory.reverse()
                break
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
def load_locale(code):
    global lang, locale
    locale = code
    lang = read_json(f'res/locale/{code}.json',)

# loads a language and applies it
def change_water(value):
    global game, still_water
    still_water = value
    game.water = Water((windowx,windowy), value)

# changes resize method
def change_resize_method(is_smooth):
    global smoothscale, resize_method
    smoothscale = is_smooth
    if smoothscale:
        resize_method = pg.transform.smoothscale
    else:
        resize_method = pg.transform.scale

# returns current bin upgrade cost
def get_bin_cost():
    return game.capacity_cost

# returns current balance
def get_balance():
    return game.balance

# adds/substracts to game balance
def modify_bal(amount):
    global game
    game.balance += amount


# upgrade inventory capacity
def upgrade_bin():
    global game
    game.update_capacity(game.capacity+1)

# upgrade boid size
def upgrade_boid_boost():
    global game
    game.update_boid_boost(round(game.boid_size_boost+0.1, 1))

# get boid boost limit for upgrading
def boid_boost_limit():
    return (round(game.boid_size_boost*10)-10, 15)

# get boid boost cost
def boid_boost_cost():
    return game.boid_boost_cost

# upgrade boid size
def upgrade_fish_speed():
    global game
    game.update_spawn_time(game.spawn_speed-10)

# get boid boost limit for upgrading
def fish_speed_limit():
    return (round((300-game.spawn_speed)/10), 25)

# get boid boost cost
def fish_speed_cost():
    return game.spawn_speed_cost

# upgrade cursor smoothness
def upgrade_cur_smoothness():
    global game
    game.update_cur_smoothness(game.cur_smoothness+0.05)

# get cursor smoothness limit for upgrading
def cur_smoothness_limit():
    return (round(((game.cur_smoothness*2)-0.2)*10), 10)

# get cursor smoothness cost
def cur_smoothness_cost():
    return game.cur_smooth_cost


# save the game to the file
def save():
    data = {
        'inv': [i.key for i in game.inventory],
        'bal': game.balance,
        'xp': game.level.xp,
        'still_water': still_water,
        'smoothscale': smoothscale,
        'lang': locale,
        'capacity': game.capacity,
        'boid_boost': game.boid_size_boost,
        'spawn_speed': game.spawn_speed,
        'cur_smoothness': game.cur_smoothness
    }
    write('save', data)

# loads the locale from the file
def fetch_locale():
    try:
        data = read('save')
        load_locale(data['lang'])
    except Exception as e:
        load_locale('ru-ru')

# loads the resize mehtod from the file
def fetch_resize_method():
    try:
        data = read('save')
        change_resize_method(data['smoothscale'])
    except:
        change_resize_method(True)

# load the game from the file
def load():
    try:
        data = read('save')
        global tutorial
        tutorial = False
        load_locale(data['lang'])
        change_water(data['still_water'])
        game.level.add(data['xp'])
        game.level.update_level()
        game.level.vis_percentage = game.level.percentage
        game.level.old_level = game.level.level
        game.inventory = [dict_fish[i] for i in data['inv']]
        game.regen_dict_inv()
        game.balance = data['bal']
        game.update_capacity(data['capacity'])
        game.update_boid_boost(data['boid_boost'])
        game.update_spawn_time(data['spawn_speed'])
        game.update_cur_smoothness(data['cur_smoothness'])
        change_resize_method(data['smoothscale'])

    except Exception as e:
        load_locale('ru-ru')
        write('save', {
            'inv': [],
            'bal': 0,
            'xp': 0,
            'still_water': False,
            'lang': 'ru-ru',
            'capacity': 5,
            'boid_boost': 1.0,
            'spawn_speed': 300,
            'cur_smoothness': 0.1
        })

fetch_locale()
fetch_resize_method()


# app classes

# upgrade element
class UpgradeElement:
    def __init__(self, image, name, cost_callback, upgrade_callback, limit_callback=None):
        self.image = image
        self.text = lang[name]
        self.desc = lang[f'{name}-desc']
        self.cost_callback = cost_callback
        self.upgrade_callback = upgrade_callback
        self.cost = cost_callback()
        self.size = 160+draw.get_text_size(self.text, 36)[0]+10
        self.limit_callback = limit_callback

    def draw(self, pos):
        rect = pg.Rect((pos[0], pos[1]+40), (self.size-10, 150))
        bal = get_balance()

        # bg
        if self.limit_callback != None:
            check = self.limit_callback()
            check = check[0] < check[1]
        else:
            check = True

        if bal < self.cost or not check:
            pg.draw.rect(screen, (220,210,180),rect, 0, 7)
        else:
            pg.draw.rect(screen, (240,230,200) if not (rect.collidepoint(mouse_pos) and mouse_press[0]) else (200,190,160),rect, 0, 7)
        pg.draw.rect(screen, (150,130,90),rect, 2, 7)

        # data
        draw.image(self.image, (rect.left+70, rect.centery), (90,90), 'm', 'm')
        draw.text(self.text, (rect.left+140, rect.top+20), (0,0,0), size=36, opacity=230)
        draw.text(self.desc, (rect.left+140, rect.top+60), (0,0,0), size=18, opacity=128)
        
        # cost
        if bal < self.cost:
            draw.image('coin.png', (rect.left+140, rect.bottom-54), (24,24))
            draw.text(f'{bal} / {self.cost}', (rect.left+170, rect.bottom-56), (255,50,50), size=24, opacity=170)
        elif not check:
            draw.text(lang['max-lvl'], (rect.left+140, rect.bottom-56), (0,0,0), size=24, opacity=150)
        else:
            draw.image('coin.png', (rect.left+140, rect.bottom-54), (24,24))
            draw.text(str(self.cost), (rect.left+170, rect.bottom-56), (0,0,0), size=24, opacity=170)

        # limit
        if self.limit_callback != None:
            data = self.limit_callback()
            draw.text(f'{data[0]} / {data[1]}', (rect.right-25, rect.bottom-50), (0,0,0), size=20, h='r', opacity=200)

    def update(self, pos):
        # updating elements
        rect = pg.Rect((pos[0], pos[1]+40), (self.size-10, 150))
        self.cost = self.cost_callback()

        if rect.collidepoint(mouse_pos) and lmb_up:
            bal = get_balance()
            if bal < self.cost:
                pass
            else:
                if self.limit_callback != None:
                    data = self.limit_callback()
                    data = data[0] < data[1]
                else:
                    data = True
                if data:
                    modify_bal(-self.cost)
                    self.upgrade_callback()


# upgrade menu
class UpgradeMenu:
    def __init__(self):
        self.elements = [
            UpgradeElement('bin.png', 'bin-upgrade', get_bin_cost, upgrade_bin),
            UpgradeElement('fish.png', 'fish-boost', boid_boost_cost, upgrade_boid_boost, boid_boost_limit),
            UpgradeElement('poof.png', 'spawn-speed', fish_speed_cost, upgrade_fish_speed, fish_speed_limit),
            UpgradeElement('mouse.png', 'cur-smoothness', cur_smoothness_cost, upgrade_cur_smoothness, cur_smoothness_limit),
        ]
        self.scroll_offset = 0
        self.scroll_vel = 0
        self.size = max(0, sum([i.size for i in self.elements])+10-windowx)

    def draw(self, y):
        # drawing title
        size = draw.text(lang['upgrade'], (10,y+5), size=24)[0]+20

        # drawing elements
        ongoing = 10-self.scroll_offset
        for i in self.elements:
            i.draw((ongoing, y))
            ongoing += i.size

    def update(self, y):
        # scrolling
        if mouse_scroll != 0.0:
            self.scroll_vel -= mouse_scroll*15

        if self.scroll_offset < 0:
            self.scroll_offset = 0
        if self.scroll_offset > self.size:
            self.scroll_offset = self.size

        self.scroll_offset += self.scroll_vel
        self.scroll_vel /= 1.2

        # updating elements
        ongoing = 10-self.scroll_offset
        for i in self.elements:
            i.update((ongoing, y))
            ongoing += i.size


# inventory
class Inventory:
    def __init__(self):
        self.scroll_offset = 0
        self.scroll_vel = 0
        self.inv = {}
        self.prev_len = 0
        self.size = 0
        self.btn_hovered = False
        self.update_btn_rect(windowy)

    def update_btn_rect(self, y):
        self.btn_rect = pg.Rect(windowx-150, y+10, 140, 20)

    def draw(self, y):
        # drawing title
        size = draw.text(lang['inventory'], (10,y+5), size=24)[0]+20
        cur_capacity = capacity()
        draw.text(f'{cur_capacity-capacity_remaining(False)}/{cur_capacity}', (size, y+9), (180,180,180))

        # drawing items
        ongoing = 10-self.scroll_offset
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

        if len(self.inv) > 0:
            # drawing button
            pg.draw.rect(screen, (240,230,200) if not (self.btn_hovered and mouse_press[0]) else (200,190,160),self.btn_rect, 0, 14)
            pg.draw.rect(screen, (150,130,90),self.btn_rect, 2, 14)
            draw.text(lang['sell-all'], (self.btn_rect.centerx, self.btn_rect.centery-1), (0,0,0), size=14, h='m', v='m')
            draw.text(lang['sell-one' if not keys[pg.K_LSHIFT] else 'sell-batch'], (windowx-165, self.btn_rect.centery-1), (200,200,200), size=16, h='r', v='m')
        else:
            # drawing empty inventory label
            draw.text(lang['empty-inventory'], (halfx, y+110), (50,50,50), size=26, h='m', v='m')

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

        # selling one or batch
        ongoing = 10-self.scroll_offset
        for i in self.inv:
            rect = pg.Rect(ongoing, y+40, 100, 150)
            if rect.collidepoint(mouse_pos) and lmb_up:
                sell(i, keys[pg.K_LSHIFT])
                break
            ongoing += 110

        # selling all
        if len(self.inv) > 0:
            self.btn_hovered = self.btn_rect.collidepoint(mouse_pos)
            if self.btn_hovered and lmb_up:
                sell_all()
        elif self.btn_hovered != False:
            self.btn_hovered = False

# switch element
class SwitchElement:
    def __init__(self, data, image, text):
        self.data = data
        self.image = image
        self.text = text

# switch
class SettingsSwitch:
    def __init__(self, elements, text, callback, default_state_var):
        self.elements = elements
        self.text = text
        self.callback = callback
        cur_index = [i.data for i in self.elements].index(globals()[default_state_var])
        self.current_element = self.elements[cur_index]
        self.size = 110

    def next(self):
        cur_index = [i.data for i in self.elements].index(self.current_element.data)
        cur_index += 1
        if cur_index >= len(self.elements):
            cur_index = 0
        globals()[self.current_element.data] = self.elements[cur_index].data
        self.current_element = self.elements[cur_index]
        self.callback(self.current_element.data)

    def draw(self, pos):
        rect = pg.Rect(pos, (100,150))

        # bg
        pg.draw.rect(screen, (240,230,200) if not (rect.collidepoint(mouse_pos) and mouse_press[0]) else (200,190,160),rect, 0, 7)
        pg.draw.rect(screen, (150,130,90),rect, 2, 7)

        # info
        draw.text(lang[self.text], (rect.centerx, rect.top+10), (0,0,0), 16, h='m')
        draw.image(self.current_element.image, rect.center, (80,80), 'm', 'm')
        draw.text(lang[self.current_element.text], (rect.centerx, rect.bottom-30), (0,0,0), 14, h='m', opacity=170)

    def update(self, pos):
        rect = pg.Rect(pos, (100,150))
        hovered = rect.collidepoint(mouse_pos)

        if hovered and lmb_up:
            self.next()

# settings menu
class Settings:
    def __init__(self):
        self.scroll_offset = 0
        self.scroll_vel = 0
        self.items = [
            SettingsSwitch([
                SwitchElement('ru-ru', 'ru-ru.png', 'russian'),
                SwitchElement('en-us', 'en-us.png', 'english'),
            ], 'language', load_locale, 'locale'),
            SettingsSwitch([
                SwitchElement(True, 'still_water.png', 'still-water'),
                SwitchElement(False, 'wavy_water.png', 'wavy-water'),
            ], 'water-flow', change_water, 'still_water'),
            SettingsSwitch([
                SwitchElement(True, 'smooth.png', 'smooth'),
                SwitchElement(False, 'rough.png', 'rough'),
            ], 'smoothscale', change_resize_method, 'smoothscale')
        ]
        self.size = max(0, sum([i.size for i in self.items])+10-windowx)

    def draw(self, y):
        # drawing title
        size = draw.text(lang['settings'], (10,y+5), size=24)[0]+20
        
        # drawing elements
        ongoing = 10-self.scroll_offset
        for i in self.items:
            i.draw((ongoing, y+40))
            ongoing += i.size

    def update(self, y):
        # scrolling
        if mouse_scroll != 0.0:
            self.scroll_vel -= mouse_scroll*15

        if self.scroll_offset < 0:
            self.scroll_offset = 0
        if self.scroll_offset > self.size:
            self.scroll_offset = self.size

        self.scroll_offset += self.scroll_vel
        self.scroll_vel /= 1.2
        
        # drawing elements
        ongoing = 10-self.scroll_offset
        for i in self.items:
            i.update((ongoing, y+40))
            ongoing += i.size


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
        while self.level_xp >= self.total_level_xp:
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
        pg.mouse.set_visible(False) 

        self.update_spawn_time(300)
        self.boid_spawn_speed = 100
        self.update_boid_boost(1)

        self.fish = []
        self.water = Water((windowx, windowy), False)
        self.boid_size = 0
        self.spawn_after = self.spawn_speed
        self.fish_p = []

        self.balance = 0
        self.bin_scale = 0.0
        self.full_inv_appearance = 0.0
        self.inventory = []
        self.dict_inv = {}
        self.update_capacity(5)
        self.level = LevelManager()

        self.buttons = [
            BtmBrButton('inventory.png', 'inventory',0,Inventory),
            BtmBrButton('shine_ball.png', 'shine',1,Inventory),
            BtmBrButton('up.png', 'upgrade',2,UpgradeMenu),
            BtmBrButton('settings.png', 'settings',3,Settings),
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
        self.update_cur_smoothness(0.1)

        self.play_bg_music()

    # starts playing background music
    def play_bg_music(self):
        pg.mixer.music.stop()
        pg.mixer.music.load('res/sounds/background.mp3')
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

    # updates bin capacity
    def update_capacity(self, amount):
        self.capacity = amount
        self.capacity_cost = 50+(amount-5)*30

    # updates boid size boost
    def update_boid_boost(self, amount):
        self.boid_size_boost = amount
        self.boid_boost_cost = 100+(round(amount*10)-10)*75

    # updates fish spawn time
    def update_spawn_time(self, amount):
        self.spawn_speed = amount
        self.spawn_speed_cost = 100+round((300-amount)/10)*50

    # updates cursor smoothness
    def update_cur_smoothness(self, amount):
        self.cur_smoothness = amount
        self.cur_smooth_cost = 100+round(((amount*2)-0.2)*10)*100

    # updates the gui
    def update_gui(self):
        # bin animation
        if self.bin_scale > 0.0:
            self.bin_scale -= 0.04

        # full inventory notification
        if capacity_remaining() <= 0:
            if self.full_inv_appearance < 1.0:
                self.full_inv_appearance += 0.02
        elif self.full_inv_appearance > 0.0:
            self.full_inv_appearance -= 0.02

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
        if self.full_inv_appearance > 0.0:
            ease = easing.ExponentialEaseOut(0,50,1).ease(self.full_inv_appearance)
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
        self.rod_pos = dlerp(self.rod_pos, init_pos, self.cur_smoothness)
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


# dust particle or whatever this thing is on the loading screen
class LSParticle:
    def __init__(self):
        self.x = random.randint(halfx-200,halfx+200)
        self.y = windowy+10
        self.removable = False
        self.speed = random.random()/2+0.75

        # size properties
        self.size = random.randint(8,15)
        self.size_key = random.random()*pi
        self.size_speed = random.random()/20+0.02 # how fast the size changes
        self.size_strength = random.randint(1,4) # how strong is the size change

        # opacity properties
        self.alpha = random.randint(110,180)
        self.alpha_key = 0
        self.alpha_speed = random.random()/30+0.02 # how fast the opacity changes
        self.alpha_strength = random.randint(15,69) # how strong is the opacity change

        # offset (wobbling) properties
        self.offset_key = random.random()*pi
        self.offset_speed = random.random()/20+0.01 # how fast the offset changes
        self.offset_strength = random.randint(4,15) # how strong is the offset

    def update(self):
        self.y -= self.speed
        if self.y <= -20:
            self.removable = True

        self.size_key += self.size_speed
        self.alpha_key += self.alpha_speed
        self.offset_key += self.offset_speed

    def draw(self):
        size = self.size+sin(self.size_key)*self.size_strength
        ease = easing.ExponentialEaseOut(0,1,1).ease(self.y/windowy)
        opacity = (self.alpha + sin(self.alpha_key)*self.alpha_strength) * ease
        draw.image(
            'ambient_particle.png', 
            (self.x+sin(self.offset_key)*self.offset_strength, self.y), 
            (size, size), 'm','m', opacity=opacity
        )


# loading screen, doesn't actually load anything but there's a cool animation
class LoadingScreen:
    def __init__(self):
        self.frame = 0
        self.key = 0
        self.alpha = 0
        self.surface = pg.Surface((windowx,windowy))
        self.switch_key = 0.0
        self.switching = False
        self.particles = []
        self.particle_spawn_timeout = 0

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
            load()

        # particles
        if self.frame == 1:
            # spawning
            self.particle_spawn_timeout -= 1
            if self.particle_spawn_timeout <= 0:
                self.particles.append(LSParticle())
                self.particle_spawn_timeout = random.randint(10,40)

            # updating
            new = []
            for i in self.particles:
                i.update()
                if not i.removable:
                    new.append(i)
            self.particles = new

        # other things
        self.update_alpha()

    def draw(self):
        screen.fill((0,0,0))

        # 1st frame
        if self.frame == 0:
            draw.text(lang['attention'], (halfx,halfy-80), (255,60,60), size=40, h='m', v='m')
            draw.text(lang['att-desc-1'], (halfx,halfy-25), (255,255,255), size=24, h='m', v='m')
            draw.text(lang['att-desc-2'], (halfx,halfy+10), (255,255,255), size=24, h='m', v='m')
            draw.text(lang['att-desc-3'], (halfx,halfy+45), (255,255,255), size=24, h='m', v='m')
            draw.text(lang['att-desc-4'], (halfx,halfy+80), (255,255,255), size=24, h='m', v='m')

        # 2nd frame
        elif self.frame == 1:
            # bg
            draw.image('ambient_glow.png', (halfx,windowy), (700,200), 'm', 'b')

            # particles
            for i in self.particles:
                i.draw()

            # text
            draw.text(lang['click_to_start'], (halfx,windowy-50), size=20, h='m', v='m')

        # dimming screen
        if self.alpha < 255 and self.switch_key <= 0.0:
            a = 255-self.alpha
            self.surface.set_alpha(a)
            screen.blit(self.surface, (0,0))

        if self.switch_key > 0.0:
            ease = easing.ExponentialEaseIn(0,1,1).ease(self.switch_key)
            size = (50+ease*500+self.switch_key*500,50+ease*500+self.switch_key*500)
            draw.image('glow.png', (halfx,halfy), size, 'm', 'm', opacity=ease*255, temp=True)
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
    keys = pg.key.get_pressed()
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
            save()

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
        draw.text(f'FPS: {dfps}', (5,3), (0,0,0)) # shadow
        draw.text(f'FPS: {dfps}', (5,2))

    # resizing the screen surface to match with the window resolution
    surface = resize_method(screen, (screenx, screeny))
    window.blit(surface, (0,0))
    pg.display.flip()
    clock.tick(fps)
    dfps = round(clock.get_fps(), 1)