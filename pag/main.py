import pygame
import asyncio
import sys
import json

# Pygame Başlatma
pygame.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Farm Tycoon: Professional Edition")
CLOCK = pygame.time.Clock()
font_main = pygame.font.Font(None, 40)
font_small = pygame.font.Font(None, 24)

def scale_converter(value):
    return value / 3 * 80

# --- Asset Yükleme (Hata Korumalı) ---
def load_asset(path, size, color=(200, 100, 100)):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        surf = pygame.Surface(size)
        surf.fill(color)
        return surf

# Varlıkları Yükle
assets = []
for a in range(120):
    assets.append(load_asset(f"assets/tile{a}.png", (int(scale_converter(2)), int(scale_converter(2))), (50, 150, 50)))

farm_asset = load_asset("assets/farm.png", (int(scale_converter(4)), int(scale_converter(4))), (101, 67, 33))
farm_water_asset = load_asset("assets/farm_water.png", (int(scale_converter(4)), int(scale_converter(4))), (50, 50, 150))

# --- Oyun Verileri ve JSON Entegrasyonu ---
plant_json_data = {
    "plants": {
        "wheat": {"name": "Wheat", "cost": 15, "sell_c": 25, "id": 10, "phases": {"0": {"grow": 10}, "1": {"grow": 15}, "2": {"grow": 20}, "3": {"grow": 20}, "4": {"grow": 15}}},
        "rice": {"name": "Rice", "cost": 25, "sell_c": 45, "id": 9, "phases": {"0": {"grow": 12}, "1": {"grow": 20}, "2": {"grow": 25}, "3": {"grow": 25}, "4": {"grow": 20}}},
        "turnip": {"name": "Turnip", "cost": 45, "sell_c": 85, "id": 0, "phases": {"0": {"grow": 15}, "1": {"grow": 30}, "2": {"grow": 45}, "3": {"grow": 40}, "4": {"grow": 30}}},
        "potato": {"name": "Potato", "cost": 60, "sell_c": 115, "id": 14, "phases": {"0": {"grow": 20}, "1": {"grow": 40}, "2": {"grow": 50}, "3": {"grow": 50}, "4": {"grow": 40}}},
        "tomato": {"name": "Tomato", "cost": 85, "sell_c": 170, "id": 4, "phases": {"0": {"grow": 30}, "1": {"grow": 50}, "2": {"grow": 60}, "3": {"grow": 60}, "4": {"grow": 50}}},
        "corn": {"name": "Corn", "cost": 110, "sell_c": 230, "id": 18, "phases": {"0": {"grow": 40}, "1": {"grow": 60}, "2": {"grow": 80}, "3": {"grow": 80}, "4": {"grow": 60}}},
        "cassava": {"name": "Cassava", "cost": 140, "sell_c": 300, "id": 13, "phases": {"0": {"grow": 45}, "1": {"grow": 70}, "2": {"grow": 90}, "3": {"grow": 90}, "4": {"grow": 70}}},
        "tulip": {"name": "Tulip", "cost": 170, "sell_c": 380, "id": 3, "phases": {"0": {"grow": 50}, "1": {"grow": 80}, "2": {"grow": 100}, "3": {"grow": 100}, "4": {"grow": 80}}},
        "eggplant": {"name": "Eggplant", "cost": 210, "sell_c": 480, "id": 6, "phases": {"0": {"grow": 55}, "1": {"grow": 90}, "2": {"grow": 115}, "3": {"grow": 110}, "4": {"grow": 90}}},
        "strawberry": {"name": "Strawberry", "cost": 260, "sell_c": 620, "id": 12, "phases": {"0": {"grow": 60}, "1": {"grow": 100}, "2": {"grow": 130}, "3": {"grow": 120}, "4": {"grow": 100}}},
        "sunflower": {"name": "Sunflower", "cost": 320, "sell_c": 780, "id": 19, "phases": {"0": {"grow": 70}, "1": {"grow": 120}, "2": {"grow": 150}, "3": {"grow": 140}, "4": {"grow": 120}}},
        "cucumber": {"name": "Cucumber", "cost": 400, "sell_c": 1000, "id": 2, "phases": {"0": {"grow": 80}, "1": {"grow": 140}, "2": {"grow": 180}, "3": {"grow": 170}, "4": {"grow": 140}}},
        "rose": {"name": "Rose", "cost": 500, "sell_c": 1300, "id": 1, "phases": {"0": {"grow": 100}, "1": {"grow": 180}, "2": {"grow": 220}, "3": {"grow": 200}, "4": {"grow": 180}}},
        "grapes": {"name": "Grapes", "cost": 650, "sell_c": 1750, "id": 11, "phases": {"0": {"grow": 120}, "1": {"grow": 220}, "2": {"grow": 280}, "3": {"grow": 250}, "4": {"grow": 220}}},
        "orange": {"name": "Orange", "cost": 800, "sell_c": 2200, "id": 16, "phases": {"0": {"grow": 150}, "1": {"grow": 280}, "2": {"grow": 350}, "3": {"grow": 320}, "4": {"grow": 280}}},
        "lemon": {"name": "Lemon", "cost": 1000, "sell_c": 2850, "id": 7, "phases": {"0": {"grow": 180}, "1": {"grow": 350}, "2": {"grow": 450}, "3": {"grow": 420}, "4": {"grow": 350}}},
        "melon": {"name": "Melon", "cost": 1300, "sell_c": 3800, "id": 5, "phases": {"0": {"grow": 220}, "1": {"grow": 450}, "2": {"grow": 550}, "3": {"grow": 500}, "4": {"grow": 450}}},
        "coffee": {"name": "Coffee", "cost": 1700, "sell_c": 5200, "id": 15, "phases": {"0": {"grow": 280}, "1": {"grow": 550}, "2": {"grow": 700}, "3": {"grow": 650}, "4": {"grow": 550}}},
        "pineapple": {"name": "Pineapple", "cost": 2200, "sell_c": 7000, "id": 8, "phases": {"0": {"grow": 350}, "1": {"grow": 750}, "2": {"grow": 950}, "3": {"grow": 900}, "4": {"grow": 750}}},
        "avocado": {"name": "Avocado", "cost": 3000, "sell_c": 10000, "id": 17, "phases": {"0": {"grow": 500}, "1": {"grow": 1000}, "2": {"grow": 1300}, "3": {"grow": 1200}, "4": {"grow": 1000}}}
    }
}

class Game:
    def __init__(self):
        self.money = 50
        self.mode = "water"
        self.gui = 0  # 0: Game, 1: Shop
        self.plants = {}
        
        # Tüm bitkileri döngüyle ekle
        for key, data in plant_json_data["plants"].items():
            p = data.copy()
            p["assets"] = [assets[(data["id"] * 6) + i] for i in range(6)]
            self.plants[key] = p

game = Game()

class Stock:
    def __init__(self):
        self.seeds = []
        self.harvested = []
        self.selected_seed_idx = 0

    def add_seed(self, key):
        for item in self.seeds:
            if item[0]["name"] == game.plants[key]["name"]:
                item[1] += 1
                return
        self.seeds.append([game.plants[key], 1])

    def add_harvested(self, plant_obj):
        for item in self.harvested:
            if item[0]["name"] == plant_obj["name"]:
                item[1] += 1
                return
        self.harvested.append([plant_obj, 1])

    def sell_all_harvested(self):
        total_gain = 0
        for item in self.harvested:
            total_gain += item[0]["sell_c"] * item[1]
        game.money += total_gain
        self.harvested = []

    def sell_one_harvested(self, index):
        if index < len(self.harvested):
            item = self.harvested[index]
            game.money += item[0]["sell_c"]
            item[1] -= 1
            if item[1] <= 0: self.harvested.pop(index)

stock = Stock()

# --- Paneller ---
mode_surf = pygame.Surface((scale_converter(16), scale_converter(11)))
mode_rect = mode_surf.get_rect(topleft=(0, 0))
farm_surf = pygame.Surface((scale_converter(32), scale_converter(27)))
farm_rect = farm_surf.get_rect(topleft=(scale_converter(16), 0))
stock_surf = pygame.Surface((scale_converter(16), scale_converter(16)))
stock_rect = stock_surf.get_rect(topleft=(0, scale_converter(11)))
shop_surf = pygame.Surface((scale_converter(32), scale_converter(20)))
shop_rect = shop_surf.get_rect(center=(W//2, H//2))

class FarmTile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(0, 0, scale_converter(4), scale_converter(4))
        self.rect.center = (x, y)
        self.plant = None
        self.lvl = 0
        self.watered = False
        self.watertime = 0
        self.gtime = 0

    def click(self):
        if game.mode == "water" and not self.watered:
            self.watered = True
            self.watertime = 15
        elif game.mode == "plant" and self.plant is None:
            if stock.selected_seed_idx < len(stock.seeds):
                sel = stock.seeds[stock.selected_seed_idx]
                self.plant = sel[0]
                self.lvl = 0
                self.gtime = self.plant["phases"]["0"]["grow"]
                sel[1] -= 1
                if sel[1] <= 0:
                    stock.seeds.pop(stock.selected_seed_idx)
                    stock.selected_seed_idx = 0
        elif game.mode == "harvest" and self.plant and self.lvl == 4:
            stock.add_harvested(self.plant)
            self.plant = None

    def update(self, dt):
        if self.watered:
            self.watertime -= dt
            if self.watertime <= 0: self.watered = False
        if self.plant and self.lvl < 4:
            speed = 3.0 if self.watered else 0.4
            self.gtime -= speed * dt
            if self.gtime <= 0:
                self.lvl += 1
                if self.lvl < 4: self.gtime = self.plant["phases"][str(self.lvl)]["grow"]

    def draw(self, surf):
        img = farm_water_asset if self.watered else farm_asset
        surf.blit(img, self.rect.topleft)
        if self.plant:
            # Bitki büyüme görselleri (5-lvl mantığı korunuyor)
            p_img = self.plant["assets"][5-self.lvl]
            surf.blit(p_img, p_img.get_rect(center=self.rect.center))

farms = [FarmTile(col*scale_converter(5)+scale_converter(3.5), row*scale_converter(5)+scale_converter(3.5)) 
         for row in range(5) for col in range(6)]

# --- Arayüz Çizimleri ---
def draw_ui():
    # MOD PANELI
    mode_surf.fill((45, 45, 45))
    money_txt = font_main.render(f"Balance: ${game.money}", True, (255, 215, 0))
    mode_surf.blit(money_txt, (20, 20))
    
    btns = [("WATERING", (80, 180, 255), "water", 100),
            ("HARVEST", (80, 255, 80), "harvest", 165),
            ("PLANT", (200, 140, 40), "plant", 230)]
    
    for name, col, mode, y in btns:
        rect = pygame.Rect(15, y, 220, 55)
        draw_col = col if game.mode == mode else [c//2 for c in col]
        pygame.draw.rect(mode_surf, draw_col, rect, border_radius=10)
        if game.mode == mode: pygame.draw.rect(mode_surf, (255,255,255), rect, 3, border_radius=10)
        txt = font_small.render(name, True, (0,0,0))
        mode_surf.blit(txt, txt.get_rect(center=rect.center))

    # STOK PANELI
    stock_surf.fill((35, 35, 35))
    # Market Butonu
    shop_btn = pygame.Rect(15, 10, 220, 50)
    pygame.draw.rect(stock_surf, (220, 40, 40), shop_btn, border_radius=8)
    stock_surf.blit(font_main.render("MARKET (S)", True, (255,255,255)), (45, 22))

    # Tohum Envanteri (Kullanıcı İsteği: Index 5 kullan)
    stock_surf.blit(font_small.render("SEEDS", True, (200,200,200)), (15, 75))
    for i, item in enumerate(stock.seeds):
        r, c = divmod(i, 3)
        slot = pygame.Rect(20+c*75, 100+r*75, 65, 65)
        bg = (120, 120, 60) if stock.selected_seed_idx == i else (60, 60, 60)
        pygame.draw.rect(stock_surf, bg, slot, border_radius=5)
        img = item[0]["assets"][5] # Tohum listesinde index 5
        stock_surf.blit(img, img.get_rect(center=slot.center))
        stock_surf.blit(font_small.render(str(item[1]), True, (255,255,255)), (slot.x+5, slot.y+5))

    # Hasat Envanteri (Kullanıcı İsteği: Index 0 kullan)
    stock_surf.blit(font_small.render("HARVESTED", True, (200,200,200)), (15, 260))
    for i, item in enumerate(stock.harvested):
        r, c = divmod(i, 3)
        slot = pygame.Rect(20+c*75, 290+r*75, 65, 65)
        pygame.draw.rect(stock_surf, (40, 90, 40), slot, border_radius=5)
        img = item[0]["assets"][0] # Hasat listesinde index 0
        stock_surf.blit(img, img.get_rect(center=slot.center))
        stock_surf.blit(font_small.render(str(item[1]), True, (255,255,255)), (slot.x+5, slot.y+5))

def draw_shop():
    shop_surf.fill((25, 25, 25))
    pygame.draw.rect(shop_surf, (255, 215, 0), shop_surf.get_rect(), 3)
    
    shop_surf.blit(font_main.render(f"MARKET - Wallet: ${game.money}", True, (255, 255, 255)), (25, 20))
    shop_surf.blit(font_small.render("Press ESC to Exit | Press E to Sell All", True, (180,180,180)), (25, 55))
    
    # Satın Al (Sol)
    y_off = 90
    for i, (key, p) in enumerate(list(game.plants.items())[:8]): # İlk 8 bitki
        rect = pygame.Rect(20, y_off, 380, 40)
        pygame.draw.rect(shop_surf, (45, 45, 45), rect, border_radius=5)
        shop_surf.blit(p["assets"][5], (25, y_off+2))
        shop_surf.blit(font_small.render(f"{p['name']} Seed: ${p['cost']}", True, (255,255,255)), (80, y_off+10))
        # Buy Buton
        b_rect = pygame.Rect(320, y_off+5, 70, 30)
        pygame.draw.rect(shop_surf, (0, 130, 0), b_rect, border_radius=5)
        shop_surf.blit(font_small.render("BUY", True, (255,255,255)), (335, y_off+10))
        y_off += 45

    # Satış (Sağ)
    y_off = 90
    for i, item in enumerate(stock.harvested[:8]):
        rect = pygame.Rect(420, y_off, 380, 40)
        pygame.draw.rect(shop_surf, (35, 55, 35), rect, border_radius=5)
        shop_surf.blit(item[0]["assets"][0], (425, y_off+2))
        shop_surf.blit(font_small.render(f"{item[0]['name']} (x{item[1]}): ${item[0]['sell_c']} ea", True, (200,255,200)), (480, y_off+10))
        # Sell Buton
        s_rect = pygame.Rect(720, y_off+5, 70, 30)
        pygame.draw.rect(shop_surf, (180, 0, 0), s_rect, border_radius=5)
        shop_surf.blit(font_small.render("SELL", True, (255,255,255)), (735, y_off+10))
        y_off += 45

async def main():
    while True:
        dt = CLOCK.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            # Klavye Kısayolları
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s: game.gui = 1
                if event.key == pygame.K_ESCAPE: game.gui = 0
                if event.key == pygame.K_e: stock.sell_all_harvested()
                if event.key == pygame.K_1: game.mode = "water"
                if event.key == pygame.K_2: game.mode = "harvest"
                if event.key == pygame.K_3: game.mode = "plant"

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if game.gui == 0:
                    if mode_rect.collidepoint(pos):
                        ry = pos[1] - mode_rect.y
                        if 100 <= ry <= 155: game.mode = "water"
                        elif 165 <= ry <= 220: game.mode = "harvest"
                        elif 230 <= ry <= 285: game.mode = "plant"
                    
                    if stock_rect.collidepoint(pos):
                        rel = (pos[0]-stock_rect.x, pos[1]-stock_rect.y)
                        if 10 <= rel[1] <= 60: game.gui = 1 # Market
                        for i in range(len(stock.seeds)):
                            r, c = divmod(i, 3)
                            if pygame.Rect(20+c*75, 100+r*75, 65, 65).collidepoint(rel):
                                stock.selected_seed_idx = i

                    if farm_rect.collidepoint(pos):
                        rel = (pos[0]-farm_rect.x, pos[1]-farm_rect.y)
                        for f in farms:
                            if f.rect.collidepoint(rel): f.click()

                elif game.gui == 1:
                    if not shop_rect.collidepoint(pos): game.gui = 0
                    else:
                        rel = (pos[0]-shop_rect.x, pos[1]-shop_rect.y)
                        # Alış Logic
                        y_off = 90
                        for i, (key, p) in enumerate(list(game.plants.items())[:8]):
                            if pygame.Rect(320, y_off+5, 70, 30).collidepoint(rel):
                                if game.money >= p["cost"]:
                                    game.money -= p["cost"]
                                    stock.add_seed(key)
                            y_off += 45
                        # Satış Logic
                        y_off = 90
                        for i in range(len(stock.harvested[:8])):
                            if pygame.Rect(720, y_off+5, 70, 30).collidepoint(rel):
                                stock.sell_one_harvested(i)
                                break
                            y_off += 45

        if game.gui == 0:
            for f in farms: f.update(dt)

        screen.fill((10, 10, 10))
        if game.gui == 0:
            draw_ui()
            screen.blit(mode_surf, mode_rect)
            farm_surf.fill((50, 35, 25))
            for f in farms: f.draw(farm_surf)
            screen.blit(farm_surf, farm_rect)
            screen.blit(stock_surf, stock_rect)
        elif game.gui == 1:
            draw_shop()
            screen.blit(shop_surf, shop_rect)

        pygame.display.flip()
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())