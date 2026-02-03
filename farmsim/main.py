import pygame

pygame.init()
W, H = 1920, 1080
screen = pygame.display.set_mode((W, H))
CLOCK = pygame.time.Clock()
font1 = pygame.font.Font(None, 40)
running = True
mode = "water"
gamemodes = ["water", "harvest", "plant"]
gui = 0

class Button:
    # Çift alt çizgiye dikkat: __init__
    def __init__(self, x, y, size, color, command, gui, name):
        self.rect = pygame.Rect(x, y, size[0], size[1])
        self.color = color
        self.command = command
        self.gui = gui
        self.name = name
        self.txt = font1.render(self.name, True, (0,0,0))
        self.txtrect = self.txt.get_rect()
        self.txtrect.center = self.rect.center
    
    def click(self, current_gui):
        global mode
        if self.command in gamemodes:
            mode = self.command
            print(f"Mod Değişti: {mode}")
        elif current_gui == self.gui:
            self.command()
    
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.txt, self.txtrect)

class Farm:
    # Çift alt çizgiye dikkat: __init__
    def __init__(self, x, y, size, color):
        self.rect = pygame.Rect(0, 0, size, size)
        self.rect.center = (x, y)
        self.color = color
        self.watered = False
    
    def draw(self):
        color = self.color
        if self.watered:
            # Renk değerlerini tam sayıya yuvarlamak gerekir
            color = (int(self.color[0]*0.5), int(self.color[1]*0.5), int(self.color[2]*0.5))
        pygame.draw.rect(screen, color, self.rect)
    
    def click(self, current_gui):
        if current_gui != 0:
            return
        if mode == "water":
            self.watered = True

def events():
    global running
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
        if e.type == pygame.MOUSEBUTTONDOWN:
            click(e.pos[0], e.pos[1])

def click(mx, my):
    for obj in buttons:
        if obj.rect.collidepoint((mx, my)):
            obj.click(gui)
            return
    for obj in farms:
        if obj.rect.collidepoint((mx, my)):
            obj.click(gui)

def draw():
    screen.fill("#ffffff")
    for f in farms:
        f.draw()
    for obj in buttons:
        obj.draw()
    pygame.display.flip()

# Nesneleri oluşturma
farms = []
buttons = [
    Button(W/6, H/8, (W/8, 100), "light blue", "water", 0, "Watering"),
    Button(W/2.5, H/8, (W/8, 100), "green", "harvest", 0, "Harvest"),
    Button(W/1.5, H/8, (W/8, 100), "brown", "plant", 0, "Plant")
]

for row in range(1, 5):
    for col in range(1, 5):
        farms.append(Farm(row*W/5, col*H/10 + H/2, W/12, (250, 150, 150)))

# Ana Döngü
while running:
    dt = CLOCK.tick(60) / 1000
    events()
    draw()

pygame.quit()