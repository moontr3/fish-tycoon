# LIGRARIES
import glob
import pygame as pg


# INITIALIZING FONTS
pg.font.init()
fonts = {}
images = {}

for i in glob.glob('res/fonts/*.ttf'):
    i = i.replace('\\','/')
    fonts[i] = []
    for j in range(300):
        try:
            fonts[i].append(pg.font.Font(i, j))
        except:
            fonts[i].append(None)


# DEFAULT SURFACE
def_surface = None


# TEXT DRAWING
def text(
        text='',
        pos=(0,0),
        color=(255,255,255), 
        size=18,
        style='regular', 
        h='l', 
        v='t', 
        antialias=True, 
        rotation=0,
        opacity=255,
        surface=None
    ):

    # surface
    if surface == None:
        surface = def_surface

    # getting font
    font = fonts[f'res/fonts/{style}.ttf'][size]
    rtext = font.render(text, antialias, color)

    # rotation
    if rotation != 0:
        rtext = pg.transform.rotate(rtext, rotation)

    # opacity
    if opacity != 255:
        rtext.set_alpha(opacity)

    # aligning
    btext = rtext.get_rect()

    if v == 't':
        if h == 'm':
            btext.midtop = pos[0],pos[1]
        elif h == 'r':
            btext.topright = pos[0],pos[1]
        else:
            btext.topleft = pos[0],pos[1]

    if v == 'm':
        if h == 'm':
            btext.center = pos[0],pos[1]
        elif h == 'r':
            btext.midright = pos[0],pos[1]
        else:
            btext.midleft = pos[0],pos[1]

    if v == 'b':
        if h == 'm':
            btext.midbottom = pos[0],pos[1]
        elif h == 'r':
            btext.bottomright = pos[0],pos[1]
        else:
            btext.bottomleft = pos[0],pos[1]
    
    # drawing
    surface.blit(rtext, btext)
    return font.size(text)


# IMAGE DRAWING
def image(
        image,
        pos=(0,0),
        size=(48,48), 
        h='l', 
        v='t', 
        rotation=0,
        opacity=255,
        flip=False,
        surface=None,
        temp=False,
        smooth=True
    ):

    # surface
    if surface == None:
        surface = def_surface

    # getting font
    if f'res/images/{image}' not in images:
        images[f'res/images/{image}'] = {'base': pg.image.load(f'res/images/{image}')}
    try:
        image = images[f'res/images/{image}'][size[0]][size[1]].copy()
    except:
        if not temp:
            images[f'res/images/{image}'][size[0]] = {}
            if smooth:
                images[f'res/images/{image}'][size[0]][size[1]] = pg.transform.smoothscale(images[f'res/images/{image}']['base'], size)
            else:
                images[f'res/images/{image}'][size[0]][size[1]] = pg.transform.scale(images[f'res/images/{image}']['base'], size)
            image = images[f'res/images/{image}'][size[0]][size[1]].copy()
        else:
            image = pg.transform.smoothscale(images[f'res/images/{image}']['base'], size)

    # flipping
    if flip:
        image = pg.transform.flip(image, True, False)

    # rotation
    if rotation != 0:
        image = pg.transform.rotate(image, rotation)

    # opacity
    if opacity != 255:
        image.set_alpha(opacity)

    # aligning
    rect = image.get_rect()

    if v == 't':
        if h == 'm':
            rect.midtop = pos[0],pos[1]
        elif h == 'r':
            rect.topright = pos[0],pos[1]
        else:
            rect.topleft = pos[0],pos[1]

    if v == 'm':
        if h == 'm':
            rect.center = pos[0],pos[1]
        elif h == 'r':
            rect.midright = pos[0],pos[1]
        else:
            rect.midleft = pos[0],pos[1]

    if v == 'b':
        if h == 'm':
            rect.midbottom = pos[0],pos[1]
        elif h == 'r':
            rect.bottomright = pos[0],pos[1]
        else:
            rect.bottomleft = pos[0],pos[1]
    
    # drawing
    surface.blit(image, rect)


# TEXT SIZE
def get_text_size(text='', size=18, style='regular'):
    font = fonts[f'res/fonts/{style}.ttf'][size]
    return font.size(text)