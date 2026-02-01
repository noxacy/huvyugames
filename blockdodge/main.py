import pygame, math, json, asyncio, sys, os

# Web ortamı kontrolü
IS_WEB = sys.platform == "emscripten"

if IS_WEB:
    import platform
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
    try:
        from js import window
        if "Mobile" in window.navigator.userAgent:
            is_mobile = True
    except: 
        pass

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
    def __init__(self, pos, target, easing, col, size, travel_time, spawn_time, *, blast=None, effect=None):
        self.pos = list(pos)
        self.target = target
        self.easing = easing
        self.color = col
        self.size = size
        self.travel_time = max(travel_time, 0.01)
        self.spawn_time = spawn_time # Merminin doğduğu müzik saniyesi
        self.start_pos = list(pos)
        self.rect = pygame.Rect(0, 0, size, size)
        self.blast = blast
        self.effect = effect
        self.mainc = col
        
    def move(self, current_music_time):
        # Merminin ne kadar süredir hayatta olduğunu müzik zamanına göre hesapla
        elapsed = current_music_time - self.spawn_time
        t = min(elapsed / self.travel_time, 1)
        
        # Eğer henüz doğma zamanı gelmediyse (negatifse) hareket etme
        if t < 0: return 

        progression = 1 - (1 - t) ** 3 if self.easing == "ease-out" else t
        
        if progression >= 0.9 and self.effect is not None:
            self.color = self.effect if self.color != self.effect else self.mainc

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
                # Patlamadan çıkan küçük parçaların doğuş zamanı tam şu anki müzik zamanıdır
                objects.append(Object(self.pos, (tx, ty), "ease-out", self.color, 10, 1.0, self.spawn_time + self.travel_time))
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
    # Koordinatları JOY_CENTER'a göre normalize et
    dx = joy_pos[0] - JOY_CENTER[0]
    dy = joy_pos[1] - JOY_CENTER[1]
    dist = math.hypot(dx, dy)
    if dist == 0: return [0, 0]
    
    # Joystick sınırlarını aşmasın
    max_dist = JOY_RADIUS
    clamped_dist = min(dist, max_dist)
    return [dx / max_dist * (clamped_dist / dist), dy / max_dist * (clamped_dist / dist)]

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
    global running, hp, dmgcd, objects, state, current_song_path, route, TOTAL_TIME, is_mobile, game_mode, time_scale, is_1hp, is_zen, input_active, input_text, custom_route, pygame, shake_amount, joy_pos, show_joystick, is_touching
    screen = pygame.display.set_mode((1280, 720))
    player = Player(W//2, H//2, 25)
    route_index, music_time = 0, 0
    damage_flash = 0 
    start_trigger = False 
    touch_id = None

    if not IS_WEB:
        try:
            import pygame.scrap
            pygame.scrap.init()
        except Exception as e:
            print(f"Clipboard init error: {e}")

    while running:
        raw_ms = clock.tick(60) 
        dt = (raw_ms / 1000.0) * time_scale
        
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        
        # 1. OLAYLARI YAKALA
        for e in events:
            if e.type == pygame.QUIT: running = False; break
            
            # Mobil Dokunmatik İşleme
            if e.type in [pygame.FINGERDOWN, pygame.FINGERMOTION, pygame.FINGERUP]:
                is_mobile = True
                fx, fy = e.x * W, e.y * H
                
                if e.type == pygame.FINGERDOWN:
                    if state == "GAME" and BTN_ESC.collidepoint(fx, fy):
                        pygame.mixer.music.stop(); state = "MENU"
                    if math.hypot(fx - JOY_CENTER[0], fy - JOY_CENTER[1]) < JOY_RADIUS * 1.5:
                        is_touching = True
                        touch_id = e.finger_id
                
                if e.type == pygame.FINGERMOTION and is_touching and e.finger_id == touch_id:
                    joy_pos[0], joy_pos[1] = fx, fy
                
                if e.type == pygame.FINGERUP and e.finger_id == touch_id:
                    is_touching = False
                    joy_pos = list(JOY_CENTER)

            # JSON Giriş Modu
            if input_active:
                if e.type == pygame.KEYDOWN:
                    mods = pygame.key.get_mods()
                    # CTRL + V (Windows/Linux) veya CMD + V (Mac)
                    if e.key == pygame.K_v and (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                        if not IS_WEB:
                            try:
                                import pygame.scrap
                                # Kaynağı al ve metne çevir
                                raw_data = pygame.scrap.get(pygame.SCRAP_TEXT)
                                if raw_data:
                                    # Byte verisini temizle ve metne ekle
                                    paste_text = raw_data.decode('utf-8').replace('\x00', '')
                                    input_text += paste_text
                            except Exception as ex:
                                print(f"Paste error: {ex}")
                        continue # Yapıştırma işleminden sonra diğer tuş kontrollerini atla

                    elif e.key == pygame.K_RETURN:
                        input_active = False
                        try:
                            data = json.loads(input_text)
                            custom_route = data["route"] if isinstance(data, dict) and "route" in data else data
                            input_text = "JSON Loaded!"
                        except: 
                            input_text = "Invalid JSON!"; custom_route = None
                    
                    elif e.key == pygame.K_BACKSPACE: 
                        input_text = input_text[:-1]
                    
                    elif e.unicode and not (mods & pygame.KMOD_CTRL or mods & pygame.KMOD_META):
                        input_text += e.unicode
                continue

            # Menü Tıklamaları
            if state == "MENU":
                if e.type in [pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN]:
                    pos = e.pos if e.type == pygame.MOUSEBUTTONDOWN else (e.x * W, e.y * H)
                    if BTN_CUSTOM.collidepoint(pos):
                        if IS_WEB:
                            paste_data = window.prompt("Paste JSON:")
                            if paste_data:
                                try:
                                    data = json.loads(str(paste_data))
                                    custom_route = data["route"]; input_text = "JSON Loaded!"
                                except: input_text = "Invalid!"
                        else: input_active = True; input_text = ""
                    elif BTN_START.collidepoint(pos): start_trigger = True
                    elif BTN_1HP.collidepoint(pos): is_1hp = not is_1hp
                    elif BTN_ZEN.collidepoint(pos): is_zen = not is_zen
                    elif BTN_FAST.collidepoint(pos): time_scale = 1.2 if time_scale != 1.2 else 1.0
                    elif BTN_SLOW.collidepoint(pos): time_scale = 0.75 if time_scale != 0.75 else 1.0
                    for i in range(len(SONGS)):
                        if H/2 + (i * 50) - 25 < pos[1] < H/2 + (i * 50) + 25:
                            current_song_path = list(SONGS.keys())[i]
                if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE: start_trigger = True

            elif state == "GAME":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop(); state = "MENU"

        # 2. BAŞLATMA
        if start_trigger:
            state = "GAME"
            objects = []
            route_index = 0
            # ... (Müzik yükleme kısmı kodunda olduğu gibi kalsın) ...
            if custom_route: route = custom_route; pygame.mixer.music.stop(); TOTAL_TIME = 600
            else:
                route = CACHED_DATA.get(current_song_path, [])
                p = current_song_path
                if time_scale > 1.0: p = SONGS[p].get("fast", p)
                elif time_scale < 1.0: p = SONGS[p].get("slow", p)
                pygame.mixer.music.load(p); pygame.mixer.music.play(start=SKIP_TIME)
                TOTAL_TIME = pygame.mixer.Sound(p).get_length()

            spawn_times = [0]
            curr = 0
            for d in route:
                curr += d["duration"] / time_scale
                spawn_times.append(curr)
            
            music_time = SKIP_TIME
            while route_index < len(spawn_times) and spawn_times[route_index] < SKIP_TIME: route_index += 1
            hp = 1 if is_1hp else 10
            player.x, player.y = W//2, H//2
            start_trigger = False
            continue

        # 3. OYUN MANTIĞI
        if state == "GAME":
            m_pos = pygame.mixer.music.get_pos()
            if not custom_route:
                if m_pos >= 0: music_time = (m_pos / 1000.0) + SKIP_TIME
                else: dt = 0 # Müzik gelene kadar lagı önlemek için dondur
            else:
                music_time += dt

            while route_index < len(route) and music_time >= spawn_times[route_index]:
                d = route[route_index]
                st = spawn_times[route_index] # Tam doğuş anı
                if d.get("type") == "block":
                    objects.append(Block(tuple(d["pos"]), tuple(d["size"]), tuple(d["color"]), st + d["etime"], d["adisplay"]))
                else:
                    # Yeni parametre: st (spawn_time)
                    objects.append(Object(d["pos"], d["target"], d["easing"], d["color"], d["size"], d["time"], st, blast=d.get("blast"), effect=d.get("effect")))
                route_index += 1

            joy_axis = get_joy_axis()
            player.move(dt, keys, joy_axis)
            
            for obj in objects[:]:
                if isinstance(obj, Object):
                    # ARTIK dt DEĞİL music_time GÖNDERİYORUZ
                    obj.move(music_time) 
                    if not is_zen and dmgcd <= 0 and player.rect.colliderect(obj.rect):
                        hp -= 1; dmgcd, shake_amount, damage_flash = 2, 15, 1.0; hit_sound.play()
                elif isinstance(obj, Block):
                    obj.update(music_time) # MÜZİK ZAMANINI GÖNDERİYORUZ
                    if obj.end: objects.remove(obj)
                    elif not is_zen and dmgcd <= 0 and obj.dmg and player.rect.colliderect(obj.rect):
                        hp -= 1; dmgcd, shake_amount, damage_flash = 2, 15, 1.0; hit_sound.play()

            if dmgcd > 0: dmgcd -= dt
            if damage_flash > 0: damage_flash -= dt * 2
            if shake_amount > 0: shake_amount -= 40 * (raw_ms / 1000.0)
            draw(objects, player, hp, show_joystick, joy_pos, music_time, shake_amount, damage_flash)

            if hp <= 0:
                pygame.mixer.music.stop(); draw_overlay("GAME OVER", "RESTARTING...", "#ff0000")
                pygame.display.flip(); await asyncio.sleep(0.5); start_trigger = True; continue
            if music_time >= TOTAL_TIME - 0.5: state = "WIN"

        elif state == "MENU":
            draw_menu(); pygame.display.flip()
        elif state == "WIN":
            draw_overlay("LEVEL CLEARED!", "Space to Menu", "#00ff00"); pygame.display.flip()
            if any(e.type == pygame.KEYDOWN or e.type == pygame.FINGERDOWN for e in events): state = "MENU"
        await asyncio.sleep(0)
    pygame.quit()
asyncio.run(main())