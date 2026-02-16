import pygame, asyncio, json
pygame.init()
W, H = 1920, 1080
screen = pygame.display.set_mode((W, H))
CLOCK = pygame.time.Clock()
font1 = pygame.font.Font(None, 40)
running = True
mx, my = None, None

assets = []
for a in range(119):
    assets.append(pygame.image.load(f"assets/tile{a}.png"))

class Game:
    def __init__(self):
        self.money = 1000000
        self.gamemodes = ["water", "harvest", "plant"]
        self.mode = "water"
        self.gui = 0
        with open("templates.json", "r")as file:
            f = json.load(file)
            self.plants = f["plants"]
        self.plant = self.plants["turnip"]

game = Game()

class Button:
    def __init__(self, x, y, size, color, command, gui, name):
        self.x = x
        self.y = y
        self.size = size
        self.rect = pygame.Rect(x, y, size[0], size[1])
        self.color = color
        self.command = command
        self.gui = gui
        self.name = name
        self.txt = font1.render(self.name, True, (0,0,0))
        self.txtrect = self.txt.get_rect()
        self.txtrect.center = self.rect.center
    
    def click(self, gui):
        global mode
        if self.command in game.gamemodes:
            game.mode = self.command
        elif game.gui == self.gui:
            self.command()
    
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.txt, self.txtrect)

class Text:
    def __init__(self, x, y, text, color, *, center=False, join=None, show=None):
        self.x = x
        self.y = y
        self.color = color
        self.join = join
        self.center = center
        self.txt = text
        self.text = font1.render(text, True, color)
        self.rect = self.text.get_rect()
        self.mtext = text
        self.show = show
    
    def center_(self):
        self.rect.center = (self.x, self.y)
    
    def set_text(self, txt):
        if self.txt != txt:
            self.txt = txt
            self.text = font1.render(txt, True, self.color)
    
    def draw(self):
        if self.center:
            self.center_()
        if self.join is not None:
            self.txt = self.mtext
            self.set_text(self.txt + self.join())
        if self.show is not None:
            if self.show():
                screen.blit(self.text, self.rect)
        else:
            screen.blit(self.text, self.rect)



class Farm:
    def __init__(self, x, y, size, color):
        self.x = x
        self.y = y
        self.size = size
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (x, y)
        self.color = color
        self.plant = None
        self.lvl = 0
        self.watered = False
        self.watertime = 0
        self.gtime = 0
        self.durs = None
        if self.plant is not None:
            self.durs = self.plant["durations"]
            self.gtime = self.durs[0]
    
    def draw(self):
        color = self.color
        t = 1
        if self.watered:
            t -= 0.5
        if self.plant is not None:
            t -= (self.lvl + 1)*0.1
        r = (color[0]*t)
        g= (color[1]*t)
        b= (color[2]*t)
        color = (r, g, b)
        pygame.draw.rect(screen, color, self.rect)
    
    def click(self, gui):
        if game.gui != 0:
            return
        if not self.watered and game.mode == "water":
            self.watered = True
            self.watertime = 15
        elif self.plant is None and game.mode == "plant":
            if game.plant["cost"] >= game.money:
                self.plant = game.plant
                game.money -= game.plant["price"]
                self.durs = self.plant["durations"]
                self.gtime = self.durs[0]
     
    def update(self, dt):
        multi = 0.5
        if self.watered:
            self.watertime -= dt
            if self.watertime <= 0.017:
                self.watered = False
            multi = 1
        if self.plant is None:
            return
        self.gtime -= multi *dt
        if self.gtime <= 0:
            if self.watered:
                self.lvl += 1
                if self.lvl < len(self.durs):
                    self.gtime = self.durs[self.lvl]
            else:
                self.plant = None

def events(dt):
    global running, mx ,my
    for e in pygame.event.get():
        if e.type == pygame.MOUSEBUTTONDOWN:
            mx, my = e.pos
            click(e.pos[0], e.pos[1], dt)
        elif e.type == pygame.QUIT:
            running = False
            break

def click(mx, my, dt):
    for obj in buttons:
        if obj.rect.collidepoint((mx, my)):
            obj.click(game.gui)
            return
    for obj in farms:   
        if obj.rect.collidepoint((mx, my)):
            obj.click(game.gui)

def draw(dt):
    screen.fill("#ffffff")
    for f in farms:
        f.update(dt)
        f.draw()
    for obj in buttons:
        obj.draw()
        for obj in texts:
            obj.draw()
    pygame.display.flip()
    
farms = [Farm(W/2, H/10 + H/2, W/10, (250, 150, 150))]
buttons = [Button(W/6, H/8,(W/8, W/8),"light blue","water" ,0,"Watering"), Button(W/2.5, H/8,(W/8, W/8),"green","harvest" ,0,"Harvest"), Button(W/1.5, H/8,(W/8, W/8),"brown","plant" ,0, "Plant")]
texts = [Text(65, 15, "Mode: ", (0,0,0),join=lambda: game.mode), Text(45, 45, "Plant: ", (0,0,0),center=True,join=lambda: game.plant["name"], show=lambda: True if game.mode == "plant" else False)]

async def main():
    while running:
        dt = CLOCK.tick(60) / 1000
        events(dt)
        draw(dt)
        await asyncio.sleep(0)
    pygame.quit()
asyncio.run(main())

"""
Each row has 2 crops, first and sixth columns are
portraits.

16x16 spritesheet, no padding, no margin

Crop list (from left to right, top to bottom)
- Turnip
- Rose
- Cucumber
- Tulip
- Tomato
- Melon
- Eggplant
- Lemon
- Pineapple
- Rice
- Wheat
- Grapes
- Straberry
- Cassava
- Potato
- Coffee
- Orange
- Avocado
- Corn
- Sunflower

License (CC0)
http://creativecommons.org/publicdomain/zero/1.0/

Can be used for personal and commercial projects.
Credit to my profile page (https://opengameart.org/users/josehzz) would be appreciated, but this is not requiered.
"""