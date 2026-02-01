# pygbag: async
import pygame, math, json, asyncio, sys, os

# 1. BAŞLANGIÇ VE EKRAN AYARI
pygame.init()
pygame.mixer.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()

# Web'de pano ve özel sistem fontları bazen çöker, onları korumaya alalım
IS_WEB = sys.platform == "emscripten"

# 2. SENİN OYUN SINIFLARIN (Dokunmadım, sadece web uyumlu yaptım)
class Player:
    def __init__(self, x, y, size):
        self.x, self.y = x, y
        self.rect = pygame.Rect(0, 0, size, size)
        self.speed = 150
        self.velx, self.vely = 0, 0
    
    def move(self, dt, keys, joy_axis):
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.vely -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.vely += self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.velx += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.velx -= self.speed
        self.x += (self.velx + joy_axis[0]*self.speed) * dt
        self.y += (self.vely + joy_axis[1]*self.speed) * dt
        self.velx *= 0.8; self.vely *= 0.8
        self.x = max(25, min(W - 25, self.x))
        self.y = max(25, min(H - 25, self.y))
        self.rect.center = (self.x, self.y)

class Object:
    def __init__(self, pos, target, easing, col, size, travel_time, blast=None, turn=0):
        self.pos = list(pos)
        self.target, self.easing, self.color = target, easing, col
        self.size, self.travel_time = size, max(travel_time, 0.01)
        self.elapsed, self.start_pos = 0, list(pos)
        self.rect = pygame.Rect(0, 0, size, size)
        self.blast, self.turn = blast, turn
        self.surf = pygame.Surface((size, size), pygame.SRCALPHA).convert_alpha()
        self.surf.fill(self.color)
        self.drawimg = self.surf

    def move(self, dt, objects_list):
        self.elapsed += dt
        t = min(self.elapsed / self.travel_time, 1)
        prog = 1 - (1 - t) ** 3 if self.easing == "ease-out" else t
        if self.turn != 0:
            self.drawimg = pygame.transform.rotate(self.surf, prog * 360 / self.turn)
        self.pos[0] = self.start_pos[0] + (self.target[0] - self.start_pos[0]) * prog
        self.pos[1] = self.start_pos[1] + (self.target[1] - self.start_pos[1]) * prog
        self.rect.center = (self.pos[0], self.pos[1])
        if t >= 1:
            if self.blast:
                for n in range(self.blast):
                    dir = math.radians(360/self.blast*n)
                    tx, ty = self.pos[0]+math.cos(dir)*500, self.pos[1]+math.sin(dir)*500
                    objects_list.append(Object(self.pos, (tx, ty), "ease-out", self.color, 10, 1.0))
            return True # Silinmesi gerekiyor
        return False

# 3. ANA DÖNGÜ (Akif Clicker Mantığıyla)
async def main():
    state = "MENU"
    player = Player(W//2, H//2, 25)
    objects = []
    music_time = 0
    route = []
    spawn_times = []
    route_index = 0
    hp = 5
    dmgcd = 0
    
    # Fontları güvenli yükle
    font = pygame.font.SysFont(None, 35)

    while True:
        dt = clock.tick(60) / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        for e in events:
            if e.type == pygame.QUIT:
                return
            if e.type == pygame.MOUSEBUTTONDOWN or (e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE):
                if state == "MENU":
                    # JSON dosyasını güvenli yükle
                    try:
                        with open("assets/dihblaster.json", "r") as f:
                            route = json.load(f)["route"]
                        spawn_times = []
                        curr = 0
                        for d in route:
                            spawn_times.append(curr)
                            curr += d["duration"]
                        pygame.mixer.music.load("assets/dihblaster.ogg")
                        pygame.mixer.music.play()
                        music_time, route_index, objects, hp = 0, 0, [], 5
                        state = "GAME"
                    except Exception as err:
                        print(f"Yükleme hatası: {err}")

        if state == "GAME":
            # Web'de music.get_pos() bazen -1 döner, o yüzden dt ile manuel takip ekledik
            music_time += dt
            
            # Spawn Mantığı
            while route_index < len(route) and music_time >= spawn_times[route_index]:
                d = route[route_index]
                objects.append(Object(d["pos"], d["target"], d["easing"], d["color"], d["size"], d["time"], d.get("blast"), d.get("turn", 0)))
                route_index += 1

            # Hareket ve Çarpışma
            player.move(dt, keys, [0, 0])
            for obj in objects[:]:
                if obj.move(dt, objects):
                    objects.remove(obj)
                elif player.rect.colliderect(obj.rect) and dmgcd <= 0:
                    hp -= 1
                    dmgcd = 1.0
            
            if dmgcd > 0: dmgcd -= dt

            # Çizim
            screen.fill((0, 0, 0))
            for obj in objects: screen.blit(obj.drawimg, obj.pos)
            pygame.draw.circle(screen, (255, 255, 255), player.rect.center, 12)
            
            hp_txt = font.render(f"HP: {hp}", True, "white")
            screen.blit(hp_txt, (20, 20))
            
            if hp <= 0: state = "MENU"; pygame.mixer.music.stop()

        else:
            screen.fill((10, 10, 10))
            txt = font.render("BLOCKDODGE - CLICK TO START", True, "white")
            screen.blit(txt, (W//2 - txt.get_width()//2, H//2))

        pygame.display.flip()
        await asyncio.sleep(0) # Bu satır Akif Clicker'ı çalıştıran satırdır

asyncio.run(main())