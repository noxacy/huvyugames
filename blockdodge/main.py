import pygame, math, json, asyncio, sys, os

# Web ortamı kontrolü
IS_WEB = sys.platform == "emscripten"

if IS_WEB:
    import platform
    # Pygame-web'de browser yerine genelde js kullanılır
    try:
        from js import window, prompt
    except ImportError:
        # Bazı sürümlerde js doğrudan window olarak gelir
        import js as window

# Mobil kontrolü (Çökmeyi önlemek için güvenli yöntem)
is_mobile = False
if IS_WEB:
    try:
        # userAgentData yerine userAgent kullanmak daha güvenlidir
        from js import window
        user_agent = window.navigator.userAgent
        if any(x in user_agent for x in ["Mobile", "Android", "iPhone", "iPad"]):
            is_mobile = True
    except:
        pass
# Yüksek skorları yükle
high_scores = {}
if os.path.exists("scores.json"):
    with open("scores.json", "r") as f: high_scores = json.load(f)
SKIP_TIME = 0
shake_amount = 0

# Mobil Buton Bölgeleri
pygame.init()
pygame.mixer.init()
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
clock = pygame.time.Clock()
running = True
pressed_keys = []
pygame.display.set_caption("Blockdodge v1.0")
input_active = False
input_text = ""
BTN_CUSTOM = pygame.Rect(W/2 - 150, H/2 + 150, 300, 50)
custom_route = None
# Müzik için mixer.music kullanıyoruz (start_pos desteği için)
pygame.mixer.music.load("assets/dihblaster.ogg")
pygame.mixer.music.set_volume(0.3)
mus = pygame.mixer.Sound("assets/dihblaster.ogg")
hit_sound = pygame.mixer.Sound("assets/hit.ogg")

# Global alanda değişkenleri ayarla
is_1hp = False
is_zen = False
time_scale = 1.0 # 1.0 normal, 1.5 hızlı, 0.7 yavaş

high_scores = {}
try:
    if os.path.exists("scores.json"):
        with open("scores.json", "r") as f: high_scores = json.load(f)
except: pass

# Skor anahtarı için yardımcı fonksiyon (Modları isme ekler)
def get_mode_suffix():
    if is_zen: return "ZEN"
    suffix = "NORMAL"
    if is_1hp: suffix = "1HP"
    if time_scale > 1.0: suffix += "_FAST"
    elif time_scale < 1.0: suffix += "_SLOW"
    return suffix

def save_score(song, percent):
    if is_zen: return # Zen skor kaydetmez
    mode = get_mode_suffix()
    key = f"{song}_{mode}"
    high_scores[key] = max(high_scores.get(key, 0), percent)
    with open("scores.json", "w") as f: json.dump(high_scores, f)

# Mod Ayarları ve Butonlarını Güncelle (global alan):
game_mode = "NORMAL" 
BTN_1HP = pygame.Rect(W/2 - 310, H - 70, 140, 40)
BTN_ZEN = pygame.Rect(W/2 - 160, H - 70, 140, 40)
BTN_FAST = pygame.Rect(W/2 + 10, H - 70, 140, 40)
BTN_SLOW = pygame.Rect(W/2 + 160, H - 70, 140, 40)
TOTAL_TIME = mus.get_length()
hp = 5
dmgcd = 0

JOY_CENTER = (180, H - 180)
JOY_RADIUS = 100
JOY_STICK_RADIUS = 50
joy_pos = list(JOY_CENTER)
is_touching = False
show_joystick = False 
touch_id = None

BTN_START = pygame.Rect(W/2 - 100, H - 150, 200, 60)
BTN_ESC = pygame.Rect(W - 120, 20, 100, 50) # Oyun içi ESC butonu

is_mobile = False
if IS_WEB:
    # Web'de dokunmatik bir cihaz olup olmadığını kontrol et
    try:
        import browser
        if "Mobile" in browser.window.navigator.userAgent:
            is_mobile = True
    except: pass

# Verileri önbelleğe al (Lagı önlemek için)

SONGS = {
    "assets/slash_inferno.ogg": {
        "name": "Slash Inferno - Noxacy Remix (EASY)",
        "data": "assets/slash_inferno.json",
        "slow": "assets/slash_inferno_slow.ogg", # Yavaşlatılmış versiyon
        "fast": "assets/slash_inferno_fast.ogg"  # Hızlandırılmış versiyon
    },
    "assets/dihblaster.ogg": {
        "name": "Sonic Blaster - Noxacy Remix (HARD)",
        "data": "assets/dihblaster.json",
        "slow": "assets/dihblaster_slow.ogg", # Yavaşlatılmış versiyon
        "fast": "assets/dihblaster_fast.ogg"  # Hızlandırılmış versiyon
    }
}
current_song_path = list(SONGS.keys())[0]
state = "MENU"

# Tüm şarkı verilerini oyun açılırken bir kez yükle
CACHED_DATA = {}
for path, info in SONGS.items():
    try:
        with open(info["data"], "r") as f:
            CACHED_DATA[path] = json.load(f)["route"]
    except Exception as e:
        print(f"Yükleme hatası ({info['name']}): {e}")
        CACHED_DATA[path] = []

def draw_overlay(title, subtitle, color="#ffffff"):
    # Arka planı hafif karart
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    cached_draw(title, color, (W/2, H/2 - 50), True)
    cached_draw(subtitle, "#aaaaaa", (W/2, H/2 + 20), True)

def draw_menu():
    screen.fill("#050505")
    cached_draw("BLOCKDODGE v1.0", "#ffffff", (W/2, H/2 - 180), True)

    current_suffix = get_mode_suffix() # Aktif mod kombinasyonunu al
    
    for i, (path, info) in enumerate(SONGS.items()):
        is_selected = (path == current_song_path)
        color = "#00ff00" if is_selected else "#ffffff"
        
        # Skorları dinamik suffix ile çek
        display_score = high_scores.get(f"{info['name']}_{current_suffix}", 0)
        cached_draw(f"{'> ' if is_selected else ''}{info['name']} (Best {current_suffix}: %{display_score})", color, (W/2, H/2 + (i * 50)), True)

    # Butonları Çiz (is_1hp, is_zen ve time_scale'e göre renk değişimi)
    modes = [
        ("1HP", BTN_1HP, "#ff4444" if is_1hp else "#ffffff"),
        ("ZEN", BTN_ZEN, "#00ffff" if is_zen else "#ffffff"),
        ("FASTER", BTN_FAST, "#ffaa00" if time_scale > 1.0 else "#ffffff"),
        ("SLOWER", BTN_SLOW, "#aaaaff" if time_scale < 1.0 else "#ffffff")
    ]
    for m_name, rect, m_color in modes:
        pygame.draw.rect(screen, m_color, rect, 2, border_radius=5)
        cached_draw(m_name, m_color, rect.center, True)
    
    # ... start butonu kısmı aynı ...

    pygame.draw.rect(screen, "#00ff00" if input_active else "#ffffff", BTN_CUSTOM, 2, border_radius=5)  
    
    if input_active:
        # Metnin son kısmını göster (Sığması için)
        display_txt = (input_text[-25:] if len(input_text) > 25 else input_text) + "|"
    elif custom_route:
        msg = "Custom JSON Loaded!"
    else:
        msg = "Click & CTRL+V to Paste JSON"

    # Start Butonu Çizimi
    pygame.draw.rect(screen, "#00ff00", BTN_START, 0, border_radius=10)
    cached_draw("START", "#000000", BTN_START.center, True)
    
    # Mobildeysek ESC/Menü butonu da menüde yardımcı olabilir (İsteğe bağlı)
        
    cached_draw(display_txt if input_active else msg, "#00ff00" if input_active else "#ffffff", BTN_CUSTOM.center, True)

def draw_game_ui(hp, current_time, shake_amount):
    if is_mobile:
        pygame.draw.rect(screen, (100, 100, 100), BTN_ESC, 0, border_radius=5)
        cached_draw("MENU", "#ffffff", BTN_ESC.center, True)
class Player:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(0, 0, size, size)
        self.speed = 150
        self.velx = 0
        self.vely = 0
    
    def move(self, dt, keys, joy_axis):
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.vely -= self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.vely += self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.velx += self.speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.velx -= self.speed
        
        self.velx += joy_axis[0] * self.speed
        self.vely += joy_axis[1] * self.speed
        self.x += self.velx * dt
        self.y += self.vely * dt
        self.velx *= 0.8
        self.vely *= 0.8
        
        self.x = max(25, min(W - 25, self.x))
        self.y = max(25, min(H - 25, self.y))
        self.rect.center = (self.x, self.y)

class Object:
    def __init__(self, pos, target, easing, col, size, travel_time, *, blast=None, effect=None):
        self.pos = list(pos)
        self.target = target
        self.easing = easing
        self.color = col
        self.size = size
        self.travel_time = max(travel_time, 0.01)
        self.elapsed = 0
        self.start_pos = list(pos)
        self.rect = pygame.Rect(0, 0, size, size)
        self.blast = blast
        self.effect  = effect
        self.mainc = col
        
    def move(self, dt):
        self.elapsed += dt
        t = min(self.elapsed / self.travel_time, 1)
        progression = 1 - (1 - t) ** 3 if self.easing == "ease-out" else t
        if progression >= 0.9:
            if self.effect is not None:
                if self.color != self.effect:
                    self.color = self.effect
                else:
                    self.color = self.mainc
        self.pos[0] = self.start_pos[0] + (self.target[0] - self.start_pos[0]) * progression
        self.pos[1] = self.start_pos[1] + (self.target[1] - self.start_pos[1]) * progression
        self.rect.center = (self.pos[0], self.pos[1])
        if t >= 1: self.remove()

    def remove(self):
        global objects
        if self.blast is not None:
            for n in range(self.blast):
                dir = math.radians(360/self.blast*n)
                tx = self.pos[0] + math.cos(dir) * 500
                ty = self.pos[1] + math.sin(dir) * 500
                objects.append(Object(self.pos, (tx, ty), "ease-out", self.color, 10, 1.0))
        if self in objects: objects.remove(self)

class Block:
    def __init__(self, center: tuple, size: tuple, color: tuple, etime: float | int, adisplay: float | int):
        self.x = center[0]
        self.y = center[1]
        self.sizex = size[0]
        self.sizey = size[1]
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.rect.center = (self.x, self.y)
        self.color = color
        self.maincolor = color
        self.etime = etime
        self.dmg = False
        self.starttime = etime
        self.adisplay = adisplay
        self.a = 0.5
        self.set_col()
        self.end = False

    def set_col(self):
        r, g, b = self.maincolor
        r = int(r * (1 - self.a))
        g = int(g * (1 - self.a))
        b = int(b * (1 - self.a))
        self.color = (r, g, b)
    
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)

    def update(self, dt): # dt parametresini ekledik
        global shake_amount
        self.etime -= dt
        if self.etime <= 0:
            self.end = True
        if self.starttime - self.etime >= self.adisplay:
            if not self.dmg: # Sadece patladığı an sarsıntı yap
                self.dmg = True
                self.a = 0
                self.set_col()
                shake_amount = 5

def get_joy_axis():
    if not is_touching: return [0, 0]
    dx = joy_pos[0] - JOY_CENTER[0]
    dy = joy_pos[1] - JOY_CENTER[1]
    return [dx/JOY_RADIUS, dy/JOY_RADIUS]
    try:
        finger = pygame._sdl2.touch.get_finger(pygame._sdl2.touch.get_device(0), touch_id)
        if not finger: return [0, 0]
        fx, fy = finger['x'] * W, finger['y'] * H
        dist = math.hypot(dx, dy)
        if dist > JOY_RADIUS: dx, dy = dx/dist * JOY_RADIUS, dy/dist * JOY_RADIUS
        joy_pos = [JOY_CENTER[0] + dx, JOY_CENTER[1] + dy]
        return [dx/JOY_RADIUS, dy/JOY_RADIUS]
    except: return [0,0]

text_cache = {}
def cached_draw(text, color, position, center=False):
    font = pygame.font.SysFont(None, 35)
    key = (str(text), color)
    if key not in text_cache: text_cache[key] = font.render(str(text), True, color).convert_alpha()
    surf = text_cache[key]
    rect = surf.get_rect(center=position if center else (position[0], position[1]))
    screen.blit(surf, rect)

def draw(objects, player, hp, show_joystick, joy_pos, current_time, shake=0, damage_flash=0):
    import random
    ox = random.randint(-int(shake), int(shake)) if shake > 0 else 0
    oy = random.randint(-int(shake), int(shake)) if shake > 0 else 0

    screen.fill("#000000")

    # Hasar yiyince ekran kenarlarını kırmızı parlat
    if damage_flash > 0:
        overlay = pygame.Surface((W, H))
        overlay.set_alpha(int(damage_flash * 150)) # Parlama şiddeti
        overlay.fill((200, 0, 0))
        screen.blit(overlay, (0, 0))
    
    # Progress Bar (Sarsıntıdan etkilenir)
    bar_width = (current_time / max(1, TOTAL_TIME)) * W
    pygame.draw.rect(screen, (50, 50, 50), (ox, oy, W, 8))
    pygame.draw.rect(screen, (255, 255, 255), (ox, oy, bar_width, 8))

    for obj in objects:
        if isinstance(obj, Block):
            obj.draw()

    for obj in objects:
        if isinstance(obj, Object):
            sr = obj.rect.copy()
            sr.x += ox; sr.y += oy
            pygame.draw.rect(screen, obj.color, obj.rect)
            if obj.blast: cached_draw(obj.blast, "#000000", sr.center, True)
    
    if is_mobile:
        pygame.draw.rect(screen, (100, 100, 100), BTN_ESC, 0, border_radius=5)
        cached_draw("MENU", "#ffffff", BTN_ESC.center, True)

    # Joystick Çizimi
    if is_mobile: # show_joystick yerine is_mobile kullanmak daha garantidir
        pygame.draw.circle(screen, (255, 255, 255), JOY_CENTER, JOY_RADIUS, 2)
        pygame.draw.circle(screen, (150, 150, 150), joy_pos, JOY_STICK_RADIUS)
    
    # Oyuncuyu çiz (Dmgcd varken yanıp söner)
    if dmgcd <= 0 or int(pygame.time.get_ticks() / 50) % 2 == 0:
        pygame.draw.circle(screen, "#ffffff", (player.rect.centerx + ox, player.rect.centery + oy), 12.5)
    
    # --- UI BİLGİLERİ (Geri Eklenen Kısımlar) ---
    # Can Göstergesi
    cached_draw(f"HP: {hp}", "#ffffff", (65 + ox, 35 + oy))
    
    # Süre (00:00 / 00:00 formatı)
    m, s = divmod(int(current_time), 60)
    sm, ss = divmod(int(TOTAL_TIME), 60)
    cached_draw(f"{m:02d}:{s:02d} / {sm:02d}:{ss:02d}", "#ffffff", (W/2 + ox, 35 + oy), True)
    
    # Yüzde Göstergesi
    progress_percent = round((current_time / max(1, TOTAL_TIME)) * 100, 1)
    progress_percent = min(100.0, progress_percent)
    cached_draw(f"%{progress_percent}", "#ffffff", (W/2 + ox, 70 + oy), True)

    if show_joystick and is_mobile:
        pygame.draw.circle(screen, (40, 40, 40), JOY_CENTER, JOY_RADIUS, 2)
        pygame.draw.circle(screen, (80, 80, 80), joy_pos, JOY_STICK_RADIUS)
    
    
    pygame.display.flip()

async def main():
    global running, hp, dmgcd, objects, state, current_song_path, route, TOTAL_TIME, is_mobile, game_mode, time_scale, is_1hp, is_zen, input_active, input_text, custom_route, pygame, shake_amount, joy_pos, show_joystick
    screen = pygame.display.set_mode((1280, 720))
    player = Player(W//2, H//2, 25)
    route_index, music_time = 0, 0
    damage_flash = 0 
    
    # Başlangıç tetiğini döngünün içinde yöneteceğiz
    start_trigger = False 

    if IS_WEB:
        pygame.display.flip()
        await asyncio.sleep(0.1)
    else:
        try:
            import pygame.scrap
            pygame.scrap.init()
        except: pass

    while running:
        raw_ms = clock.tick(60) 
        dt = (raw_ms / 1000.0) * time_scale
        
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        joy_axis = get_joy_axis()
        
        # 1. OLAYLARI YAKALA
        for e in events:
            if e.type == pygame.QUIT: running = False; break
            
            # --- JSON GİRİŞ MODU ---
            if input_active:
                if e.type == pygame.KEYDOWN:
                    # CTRL + V Kontrolü
                    if e.key == pygame.K_v and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        if not IS_WEB: # Masaüstü için
                            try:
                                import pygame.scrap
                                raw_data = pygame.scrap.get(pygame.SCRAP_TEXT)
                                if raw_data: 
                                    text = raw_data.decode('utf-8').replace('\x00', '')
                                    input_text += text
                            except: pass
                    
                    elif e.key == pygame.K_RETURN:
                        input_active = False
                        try:
                            data = json.loads(input_text)
                            custom_route = data["route"] if isinstance(data, dict) and "route" in data else data
                            input_text = "JSON Loaded!"
                        except: 
                            input_text = "Invalid JSON!"
                            custom_route = None
                    elif e.key == pygame.K_BACKSPACE: 
                        input_text = input_text[:-1]
                    elif e.unicode and not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        input_text += e.unicode
                continue

            # --- MENÜ TIKLAMALARI ---
            if state == "MENU":
                if e.type in [pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN]:
                    if e.type == pygame.MOUSEBUTTONDOWN: pos = e.pos
                    else: pos = (e.x * W, e.y * H)
                    
                    if BTN_CUSTOM.collidepoint(pos):
                        if IS_WEB:
                            try:
                                # js modülünden gelen window.prompt kullanımı
                                paste_data = window.prompt("Paste your JSON route here:")
                                if paste_data:
                                    input_text = str(paste_data)
                                    data = json.loads(input_text)
                                    custom_route = data["route"] if isinstance(data, dict) and "route" in data else data
                                    input_text = "JSON Loaded!"
                            except Exception as e:
                                input_text = "Invalid JSON!"
                                print(f"JSON Error: {e}")
                        else:
                            input_active = True
                            input_text = ""
                    
                    # Başlat Butonu
                    elif BTN_START.collidepoint(pos): 
                        start_trigger = True
                    
                    # Mod Butonları
                    elif BTN_1HP.collidepoint(pos): is_1hp = not is_1hp
                    elif BTN_ZEN.collidepoint(pos): is_zen = not is_zen
                    elif BTN_FAST.collidepoint(pos): time_scale = 1.2 if time_scale != 1.2 else 1.0
                    elif BTN_SLOW.collidepoint(pos): time_scale = 0.75 if time_scale != 0.75 else 1.0
                    
                    # Şarkı Seçimi
                    for i in range(len(SONGS)):
                        if H/2 + (i * 50) - 25 < pos[1] < H/2 + (i * 50) + 25:
                            current_song_path = list(SONGS.keys())[i]

                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                    start_trigger = True

            # --- OYUN İÇİ KONTROLLER ---
            elif state == "GAME":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop(); state = "MENU"
        # 2. BAŞLATMA MANTIĞI (Tetiklendiyse çalışır)
        if start_trigger:
            state = "GAME"
            objects = []
            route_index = 0
            if custom_route:
                route = custom_route
                pygame.mixer.music.stop()
                TOTAL_TIME = 600
            else:
                route = CACHED_DATA.get(current_song_path, [])
                p = current_song_path
                if time_scale > 1.0: p = SONGS[p].get("fast", p)
                elif time_scale < 1.0: p = SONGS[p].get("slow", p)
                pygame.mixer.music.load(p)
                pygame.mixer.music.play(start=SKIP_TIME)
                TOTAL_TIME = pygame.mixer.Sound(p).get_length()

            spawn_times = []
            current_sum = 0
            for d in route:
                spawn_times.append(current_sum)
                current_sum += d["duration"] / time_scale
            
            music_time = SKIP_TIME
            while route_index < len(spawn_times) and spawn_times[route_index] < SKIP_TIME:
                route_index += 1
            
            shake_amount, damage_flash = 0, 0
            hp = 1 if is_1hp else 10
            player.x, player.y = W//2, H//2
            player.velx, player.vely = 0, 0
            start_trigger = False # TETİĞİ SIFIRLA
            continue # Oyuna hemen başla

        # 3. OYUN DÖNGÜSÜ
        if state == "GAME":
            # Müzik/Süre senkronizasyonu
            if not custom_route:
                m_pos = pygame.mixer.music.get_pos()
                if m_pos >= 0: music_time = (m_pos / 1000.0) + SKIP_TIME
                else: music_time += dt
            else:
                music_time += dt

            # Sarsıntı azaltma
            if shake_amount > 0: shake_amount -= 40 * (raw_ms / 1000.0)

            # Nesne oluşturma
            while route_index < len(route) and music_time >= spawn_times[route_index]:
                d = route[route_index]
                cur = d.get("type", "object")
                if cur == "object":
                    objects.append(Object(d["pos"], d["target"], d["easing"], d["color"], d["size"], d["time"], blast=d.get("blast"), effect=d.get("effect")))
                elif cur == "block":
                    objects.append(Block(tuple(d["pos"]), tuple(d["size"]), tuple(d["color"]), d["etime"], d["adisplay"]))
                route_index += 1

            player.move(dt, keys, joy_axis)
            
            for obj in objects[:]:
                if isinstance(obj, Object):
                    obj.move(dt)
                    if not is_zen and dmgcd <= 0 and obj.blast is None and player.rect.colliderect(obj.rect):
                        hp -= 1
                        dmgcd, shake_amount, damage_flash = 1.0, 15, 1.0
                        hit_sound.play()
                        obj.remove()
                elif isinstance(obj, Block):
                    obj.update(dt)
                    if obj.end:
                        if obj in objects: objects.remove(obj)
                        continue
                    if not is_zen and dmgcd <= 0 and obj.dmg and player.rect.colliderect(obj.rect):
                        hp -= 1
                        dmgcd, shake_amount, damage_flash = 1.0, 15, 1.0
                        hit_sound.play()

            if dmgcd > 0: dmgcd -= dt
            if damage_flash > 0: damage_flash -= dt * 2

            draw(objects, player, hp, show_joystick, joy_pos, music_time, shake_amount, damage_flash)

            if hp <= 0:
                pygame.mixer.music.stop()
                draw_overlay("GAME OVER", "RESTARTING...", "#ff0000")
                pygame.display.flip()
                await asyncio.sleep(0.5) 
                pygame.event.clear()
                start_trigger = True # ÖLÜNCE OTOMATİK RESTART
                continue

            if music_time >= TOTAL_TIME - 0.5:
                state = "WIN"

        elif state == "MENU":
            draw_menu()
            pygame.display.flip()

        elif state == "WIN":
            draw_overlay("LEVEL CLEARED!", "Tap/Space for Menu", "#00ff00")
            pygame.display.flip()
            if any((e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE) or e.type == pygame.FINGERDOWN for e in events):
                state = "MENU"

        await asyncio.sleep(0)
    pygame.quit()
asyncio.run(main())