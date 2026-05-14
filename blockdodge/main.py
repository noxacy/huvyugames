import pygame, math, json, asyncio, sys, os, random

vfx_start_time = 0
vfx_total_duration = 1.0
vfx_target_bg = [0, 0, 0]
vfx_target_p = [255, 255, 255]
is_vfx_smooth = False # Başlangıçta geçiş hesaplamasın

# Global veya reset anında tanımla
start_timer = 1.0  # 1 saniye geri sayım
restart_timer = 0  # Fail sonrası için


if sys.platform == "emscripten":
    try:
        pygame.mixer.SoundPatch()
        print("Pygbag SoundPatch active")
    except:
        pass

bg_color_1 = [0, 0, 0]
bg_color_2 = [0, 0, 0]
is_gradient_active = False
bg_angle = 0
player_color = [255, 255, 255]

# Web ortamı kontrolüa
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
        window.eval("if (window.audioContext) { window.audioContext.resume(); }")
        user_agent = window.navigator.userAgent
        if any(x in user_agent for x in ["Mobile", "Android", "iPhone", "iPad"]):
            is_mobile = True
    except:
        pass
# Yüksek skorları yükle
high_scores = {}
if os.path.exists("scores.json"):
    with open("scores.json", "r") as f: high_scores = json.load(f)
OG_SKIP_TIME = 0
SKIP_TIME = 0
shake_amount = 0
# Mobil Buton Bölgeleri
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.mixer.init()
pygame.init()
pygame.font.init()

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
mus = pygame.mixer.Sound("assets/dihblaster.ogg")
hit_sound = pygame.mixer.Sound("assets/hit.wav")

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
def save_score(song_path, percent):
    if is_zen: return # Zen modunda skor kaydedilmez

    # Şarkı ismini SONGS sözlüğünden çek
    song_info = SONGS.get(song_path)
    if not song_info: return

    song_name = song_info["name"]
    mode = get_mode_suffix()
    key = f"{song_name}_{mode}"

    # Mevcut skoru kontrol et ve en yükseğini al
    current_best = high_scores.get(key, 0)
    if percent > current_best:
        high_scores[key] = percent
        try:
            with open("scores.json", "w") as f:
                json.dump(high_scores, f, indent=4)
            print(f"Skor Kaydedildi: {key} - %{percent}")
        except Exception as e:
            print(f"Skor yazma hatası: {e}")

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
    },
    "assets/ordih.ogg": {
        "name": "Animation Warrior Theme - Noxacy Remix (INSANITY)",
        "data": "assets/ordih.json",
        "slow": "assets/ordih_slow.ogg", # Yavaşlatılmış versiyon
        "fast": "assets/ordih_fast.ogg"  # Hızlandırılmış versiyon
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

overlay_surface = pygame.Surface((W, H), pygame.SRCALPHA)

def draw_overlay(title, subtitle, color="#ffffff"):
    # Arka planı hafif karart
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    cached_draw(title, color, (W/2, H/2 - 50), True)
    cached_draw(subtitle, "#aaaaaa", (W/2, H/2 + 20), True)

def draw_menu():
    screen.fill("#050505")
    cached_draw("BLOCKDODGE v1.5", "#ffffff", (W/2, H/2 - 180), True)

    current_suffix = get_mode_suffix() 

    for i, (path, info) in enumerate(SONGS.items()):
        is_selected = (path == current_song_path)
        
        # SADECE SEÇİLİ OLAN YEŞİL (#00ff00), DİĞERLERİ BEYAZ (#ffffff)
        level_color = "#00ff00" if is_selected else "#ffffff"
        
        score_key = f"{info['name']}_{current_suffix}"
        display_score = high_scores.get(score_key, 0)

        # Rengi level_color olarak kullanıyoruz
        cached_draw(f"{'> ' if is_selected else ''}{info['name']} (Best: %{display_score})", level_color, (W/2, H/2 + (i * 50)), True)

    # Mod Butonları (Renkleri kendi mantığında kalıyor)
    modes = [
        ("1HP", BTN_1HP, "#ff4444" if is_1hp else "#ffffff"),
        ("ZEN", BTN_ZEN, "#00ffff" if is_zen else "#ffffff"),
        ("FASTER", BTN_FAST, "#ffaa00" if time_scale > 1.0 else "#ffffff"),
        ("SLOWER", BTN_SLOW, "#aaaaff" if time_scale < 1.0 else "#ffffff")
    ]
    for m_name, rect, m_color in modes:
        pygame.draw.rect(screen, m_color, rect, 2, border_radius=5)
        cached_draw(m_name, m_color, rect.center, True)

    # Custom JSON Alanı
    pygame.draw.rect(screen, "#00ff00" if input_active else "#ffffff", BTN_CUSTOM, 2, border_radius=5)
    
    if input_active:
        display_txt = (input_text[-25:] if len(input_text) > 25 else input_text) + "|"
        msg = display_txt
    elif custom_route:
        msg = "Custom JSON Loaded!"
    else:
        msg = "Click & CTRL+V to Paste JSON"
        
    cached_draw(msg, "#00ff00" if input_active else "#ffffff", BTN_CUSTOM.center, True)

    # Start Butonu
    pygame.draw.rect(screen, "#00ff00", BTN_START, 0, border_radius=10)
    cached_draw("START", "#000000", BTN_START.center, True)

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
        self.trail = []
        self.max_trail = 8
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
        self.spawn_time = spawn_time
        self.start_pos = list(pos)
        self.rect = pygame.Rect(0, 0, size, size)
        self.blast = blast
        self.effect = effect
        self.mainc = col
        self.trail = []  # İzleri tutacak liste
        self.max_trail = 5

    def move(self, current_music_time):
        elapsed = current_music_time - self.spawn_time
        t = min(elapsed / self.travel_time, 1)
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
                objects.append(Object(self.pos, (tx, ty), "ease-out", self.color, 10, 1.0, self.spawn_time + self.travel_time))
        if self in objects: objects.remove(self)

    def draw(self, surface, ox=0, oy=0):
        self.trail.insert(0, (self.pos[0] + ox, self.pos[1] + oy))
        if len(self.trail) > self.max_trail:
            self.trail.pop()

        # İzleri çiz (Gittikçe küçülen kareler)
        for i, p in enumerate(self.trail):
            trail_size = self.size * (1 - (i / self.max_trail))
            if trail_size > 1:
                # RENK KONTROLÜ: Eğer renk liste değilse (hex string ise) direkt onu kullan
                if isinstance(self.color, (list, tuple)):
                    t_col = [max(0, c - 50) for c in self.color]
                else:
                    t_col = self.color # String ise olduğu gibi bırak (şeffaflık zor olur)
                
                t_rect = pygame.Rect(0, 0, trail_size, trail_size)
                t_rect.center = p
                # 'screen' yerine 'surface' kullanıyoruz
                pygame.draw.rect(surface, t_col, t_rect)

        # Ana mermiyi çiz
        sr = self.rect.copy()
        sr.x += ox; sr.y += oy
        pygame.draw.rect(surface, self.color, sr)

        if self.blast:
            # self.blast'ı stringe çevirerek hata almayı engelliyoruz
            cached_draw(str(self.blast), "#000000", sr.center, True)

BLOCK_FONTS = {}

particles = [] # [ [x, y, vx, vy, color, life], ... ]


class Block:
    def __init__(self, center: tuple, size: tuple, color: tuple, spawn_time: float, etime: float, adisplay: float):
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.rect.center = center
        self.maincolor = color
        self.color = color
        self.spawn_time = spawn_time
        self.etime = etime
        self.adisplay = adisplay
        self.dmg = False
        self.end = False
        self.a = 0.5
        self.current_life = 0
        self.size = size
        self.mode = "OBJECT" # "OBJECT" veya "BLOCK"

        # FORMÜL DÜZELTME:
        # Bloğun hem genişliğini hem yüksekliğini baz al,
        # ama genişliğin (3 karakter: "0.0") sığması için genişliği 3'e böl.
        f_size = int(min(size[0] / 2.2, size[1] / 1.2))

        if f_size < 12: f_size = 12 # Minimum okunabilirlik
        if f_size > 50: f_size = 50 # Maksimum devasa blok sınırı

        if f_size not in BLOCK_FONTS:
            BLOCK_FONTS[f_size] = pygame.font.SysFont("Arial", f_size, bold=True)
        self.font = BLOCK_FONTS[f_size]
        self.set_col()


    def draw(self, surface, ox=0, oy=0):
        sr = self.rect.copy()
        sr.x += ox
        sr.y += oy
        
        # --- RENK KORUMA KALKANI ---
        try:
            # Renk değerlerini güvenli bir şekilde sayıya çevir ve 0-255 arasına sıkıştır
            r = max(0, min(255, int(self.maincolor[0])))
            g = max(0, min(255, int(self.maincolor[1])))
            b = max(0, min(255, int(self.maincolor[2])))
        except (TypeError, IndexError, ValueError):
            # Eğer renk verisi bozuksa varsayılan olarak gri yap (Hata vermesini engeller)
            r, g, b = 150, 150, 150
        
        safe_rgb = (r, g, b)

        if not self.dmg:
            # Hazırlık aşaması (Şeffaf blok)
            s = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            s.fill((*safe_rgb, 100)) # (*tuple, alpha) kullanımı en sağlamıdır
            surface.blit(s, sr)
            
            rem = self.adisplay - self.current_life
            if rem > 0:
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                txt_col = (0, 0, 0) if luminance > 0.5 else (255, 255, 255)
                txt = self.font.render(f"{rem:.1f}", True, txt_col)
                surface.blit(txt, txt.get_rect(center=sr.center))
        else:
            # Aktif hasar aşaması
            pygame.draw.rect(surface, safe_rgb, sr)
    def set_col(self):
        r, g, b = self.maincolor
        self.color = (int(r * (1 - self.a)), int(g * (1 - self.a)), int(b * (1 - self.a)))

    def update(self, current_music_time):
        global shake_amount, time_scale
        self.current_life = current_music_time - self.spawn_time

        s_etime = self.etime / time_scale
        s_adisplay = self.adisplay / time_scale

        if self.current_life >= s_etime:
            self.end = True
            return

        if self.current_life >= s_adisplay and not self.dmg:
            self.dmg = True
            self.a = 0
            self.set_col()
            shake_amount = 5
            # Blok silinirken burayı çalıştır:
            p_color = list(self.color) if isinstance(self.color, (list, tuple)) else self.color
        
            for _ in range(18): # Sayıyı 15'e çıkardık
                particles.append([
                    self.rect.centerx, self.rect.centery, 
                    random.uniform(-12, 12), # X hızı çok daha yüksek
                    random.uniform(-12, 12), # Y hızı çok daha yüksek
                    p_color, 
                    1.0 # Life (Ömür)
                ])
# --- EDİTÖR YARDIMCI SABİTLERİ ---
SIDEBAR_W = 300
PROP_KEYS = {
    "object": ["x", "y", "tx", "ty", "time", "size", "blast", "r", "g", "b"],
    "block": ["x", "y", "size_w", "size_h", "time", "etime", "adisplay", "r", "g", "b"],
    # vfx kısmını bu şekilde güncelle:
    "vfx": ["time", "time_duration", "bg_r", "bg_g", "bg_b", "p_r", "p_g", "p_b", "smooth"]
}
target_bg = [0, 0, 0]
target_player = [255, 255, 255]

class LevelEditor:
    def __init__(self):
        self.route = []
        self.current_time = 0.0
        self.playing = False
        self.zoom = 100 
        self.timeline_h = 150
        self.mode = "OBJECT"
        self.selected_idx = -1
        self.prop_idx = 0 # Hangi özelliği düzenliyoruz? (size, time vb.)

    def add_element(self, pos, obj_type=None):
        if obj_type is None:
            obj_type = self.mode.lower()

        # --- 1. DOĞUŞ ZAMANI (TIMELINE YERİ) HESABI ---
        # Şu ana kadarki objelerin bekleme sürelerini (duration) topla
        total_duration_so_far = sum(o.get("duration", 0) for o in self.route)
        # Yeni objenin duration'ı = (Editörün şu anki saniyesi) - (Önceki toplam)
        # Böylece mermi tam olarak o anki kırmızı çizginin olduğu yerde doğar.
        spawn_delay = max(0, self.current_time - total_duration_so_far)

        # Temel veriler
        new_obj = {
            "type": obj_type,
            "pos": [int(pos[0]), int(pos[1])],
            "duration": round(spawn_delay, 3) # BURASI DOĞUŞ ZAMANINI BELİRLER
        }

        # Seçili objeden kopya çekme (Önceki objenin özelliklerini almak için)
        source = None
        if 0 <= self.selected_idx < len(self.route):
            temp_source = self.route[self.selected_idx]
            if temp_source.get("type", "").lower() == obj_type:
                source = temp_source

        # --- 2. TİPE ÖZEL VERİLER (TIME = UÇUŞ SÜRESİ) ---
        if obj_type == "object":
            # BURADAKİ 'time' ARTIK SENİN JSON'DAKİ 0.45 GİBİ OLAN UÇUŞ SÜRESİDİR
            new_obj["time"] = source.get("time", 0.45) if source else 0.45
            new_obj["size"] = source.get("size", 33) if source else 33
            new_obj["color"] = list(source.get("color", [255, 255, 255])) if source else [255, 255, 255]
            new_obj["target"] = [int(pos[0] + 100), int(pos[1])]
            new_obj["blast"] = source.get("blast", 12) if source else 12
            new_obj["easing"] = "ease-out"

        elif obj_type == "block":
            new_obj["size"] = list(source.get("size", [100, 100])) if source else [100, 100]
            new_obj["color"] = list(source.get("color", [255, 255, 255])) if source else [255, 255, 255]
            new_obj["etime"] = source.get("etime", 2.0) if source else 2.0
            new_obj["adisplay"] = source.get("adisplay", 1.0) if source else 1.0

        elif obj_type == "vfx":
            new_obj.update({
                "time_duration": 1.0, # Bu VFX'in kendi iç süresi
                "bg_color": [0, 0, 0],
                "p_color": [0, 255, 255],
                "smooth": True
            })

        self.route.append(new_obj)
        self.selected_idx = len(self.route) - 1

    def set_target_at(self, mouse_pos):
        if 0 <= self.selected_idx < len(self.route):
            obj = self.route[self.selected_idx]
            if obj.get("type", "object").lower() == "object":
                obj["target"] = list(mouse_pos)

    def select_at(self, mouse_pos):
            # Listeyi tersten kontrol et (en üstteki objeyi seçmek için)
            for i in range(len(self.route) - 1, -1, -1):
                obj = self.route[i]
                o_type = obj.get("type", "object").lower()
                o_start = obj.get("time", 0)

                if o_type == "vfx":
                    v_dur = obj.get("time_duration", 1.0)
                    # VFX karesi sadece ekranda görünürken seçilebilir olsun (veya hep seçilsin istersen if'i kaldır)
                    if (o_start <= self.current_time <= o_start + v_dur) or (self.selected_idx == i):
                        px, py = obj.get("pos", [W//2, H//2])
                        r = pygame.Rect(px - 20, py - 20, 40, 40)
                        if r.collidepoint(mouse_pos):
                            self.selected_idx = i
                            return True
                    continue

                if o_type == "block":
                    r = pygame.Rect(0, 0, obj["size"][0], obj["size"][1])
                    r.center = obj["pos"]
                    if r.collidepoint(mouse_pos):
                        self.selected_idx = i
                        return True
                else:
                    # Normal obje (mermi) kontrolü
                    dist = math.hypot(mouse_pos[0] - obj["pos"][0], mouse_pos[1] - obj["pos"][1])
                    if dist <= obj.get("size", 15):
                        self.selected_idx = i
                        return True
            return False

    def toggle_play(self, current_song_path):
        self.playing = not self.playing
        if self.playing:
            # Müziği kaldığı yerden başlat
            pygame.mixer.music.load(current_song_path)
            pygame.mixer.music.play(start=self.current_time)
        else:
            pygame.mixer.music.stop()

    def toggle_preview(self, music_path):
        self.playing = not self.playing
        if self.playing:
            try:
                pygame.mixer.music.load(music_path)
                # Müziği current_time saniyesinden başlat
                pygame.mixer.music.play(start=self.current_time)
            except Exception as e:
                print("Music not found.")
        else:
            pygame.mixer.music.stop()

    def update(self, dt):
        if self.playing:
            # Müziğin pozisyonunu al (ms to s)
            # music.get_pos() bazen sapıtabilir, dt ile toplamak daha stabildir
            self.current_time += dt
    def draw(self, screen):
        # 1. Başlangıç renkleri
        res_bg = [15, 15, 15]
        res_p = [0, 255, 255]

        # VFX'leri zamana göre sırala
        vfx_list = [o for o in self.route if o.get("type") == "vfx"]
        vfx_list.sort(key=lambda x: x.get("time", 0))

        for i, v in enumerate(vfx_list):
            v_start = v.get("time", 0)
            v_dur = v.get("time_duration", 1.0)
            
            if self.current_time >= v_start:
                target_bg = v.get("bg_color", [0, 0, 0])
                target_p = v.get("p_color", [0, 255, 255])
                
                if v.get("smooth", True) and v_dur > 0:
                    # Geçiş ne kadar tamamlandı? (0.0 - 1.0)
                    progress = min(1.0, (self.current_time - v_start) / v_dur)
                    # Bir önceki rengi baz alarak lerp yap
                    for c in range(3):
                        res_bg[c] += (target_bg[c] - res_bg[c]) * progress
                        res_p[c] += (target_p[c] - res_p[c]) * progress
                else:
                    res_bg, res_p = list(target_bg), list(target_p)
        
        screen.fill(res_bg)
        pygame.draw.circle(screen, res_p, (W//2, H//2), 12, 2)
        
        # ... Geri kalan mermi/blok çizim kodların ...
        
        # O anki zamana kadar olan en son VFX'i bul
        active_vfx = None
        for o in self.route:
            if o.get("type") == "vfx" and o.get("time", 0) <= self.current_time:
                active_vfx = o
        
    
        # --- 2. OBJELERİ ÇİZDİR --
        current_sum_time = 0
        for i, obj in enumerate(self.route):
            o_type = obj.get("type", "object").lower()
            start_t = obj.get("time", 0)
            current_sum_time += obj.get("duration", 0)
            spawn_t = current_sum_time
            
            # VFX Karesi Çizimi
            if o_type == "vfx":
                v_dur = obj.get("time_duration", 1.0)
                # Sadece kendi süresi içindeyse VEYA seçiliyse ekranda gözüksün
                if (spawn_t <= self.current_time <= spawn_t + v_dur) or (self.selected_idx == i):
                    px, py = obj.get("pos", [W//2, H//2])
                    vfx_rect = pygame.Rect(px - 20, py - 20, 40, 40)
                    v_col = (255, 255, 0) if self.selected_idx == i else (100, 100, 0)
                    pygame.draw.rect(screen, v_col, vfx_rect, 2)
                    cached_draw("VFX", (255, 255, 255), vfx_rect.center, True)
                continue # VFX'in başka çizimi yok
            
            
            elif o_type == "object":
                flight_duration = obj.get("time", 0.45)
                blast_count = obj.get("blast", 0)
                
                # Mermi sadece doğduğu an ile uçuşunun bittiği an arasında çizilir
                if spawn_t <= self.current_time <= spawn_t + flight_duration:
                    progress = (self.current_time - spawn_t) / flight_duration
                    prog_eased = 1 - (1 - progress) ** 3 # ease-out
                    
                    cur_x = obj["pos"][0] + (obj["target"][0] - obj["pos"][0]) * prog_eased
                    cur_y = obj["pos"][1] + (obj["target"][1] - obj["pos"][1]) * prog_eased
                    
                    pygame.draw.rect(screen, obj.get("color", (255,255,255)), 
                                   (int(cur_x)-obj["size"]//2, int(cur_y)-obj["size"]//2, obj["size"], obj["size"]))

                    if blast_count > 0:
                            cached_draw(str(blast_count), (0,0,0), (int(cur_x), int(cur_y)), True, pygame.font.SysFont("Arial", 14, bold=True))
                
                elif blast_count > 0 and spawn_t + flight_duration < self.current_time <= spawn_t + flight_duration + 1.0:
                    blast_progress = (self.current_time - (spawn_t + flight_duration)) / 1.0 # Parçalar 1 sn uçar
                    blast_eased = 1 - (1 - blast_progress) ** 3
                    
                    for n in range(blast_count):
                        angle = math.radians(360 / blast_count * n)
                        dist = 500 * blast_eased
                        px = obj["target"][0] + math.cos(angle) * dist
                        py = obj["target"][1] + math.sin(angle) * dist
                        # Parçalar daha küçük kareler (size=10)
                        pygame.draw.rect(screen, obj["color"], (int(px)-5, int(py)-5, 10, 10))

            else: # BLOCK ÇİZİMİ
                etime = obj.get("etime", 2.0)
                adisplay = obj.get("adisplay", 1.0)
                
                # start_t yerine spawn_t kullandık (Timeline'a uyması için)
                if spawn_t <= self.current_time <= spawn_t + etime:
                    elapsed = self.current_time - spawn_t
                    rect = pygame.Rect(0, 0, obj["size"][0], obj["size"][1])
                    rect.center = obj["pos"]
                    
                    if elapsed < adisplay:
                        # Hazırlık aşaması: Karartılmış renk ve kalan süre
                        alpha = 0.3
                        r_col = [int(c * alpha) for c in obj["color"]]
                        pygame.draw.rect(screen, r_col, rect)
                        # Aktifleşmeye kalan süre (Geri sayım)
                        rem_active = adisplay - elapsed
                        cached_draw(f"{rem_active:.1f}", (255,255,255), rect.center, True, pygame.font.SysFont("Arial", 20, bold=True))
                    else:
                        # Aktif aşama: Tam renk ve Sarsıntı (isteğe bağlı)
                        pygame.draw.rect(screen, obj["color"], rect)

        if 0 <= self.selected_idx < len(self.route):
            sel_obj = self.route[self.selected_idx]
            if sel_obj.get("type", "object").lower() == "object":
                pygame.draw.line(screen, (255, 255, 0), sel_obj["pos"], sel_obj["target"], 1)
                pygame.draw.circle(screen, (255, 0, 0), sel_obj["target"], 5, 1)

        # 2. Properties Paneli (Sağ Panel)
        prop_rect = pygame.Rect(W - SIDEBAR_W, 0, SIDEBAR_W, H)
        pygame.draw.rect(screen, (25, 25, 25), prop_rect)
        pygame.draw.line(screen, (80, 80, 80), (W - SIDEBAR_W, 0), (W - SIDEBAR_W, H), 2)
        
        cached_draw("PROPERTIES", (255, 215, 0), (W - SIDEBAR_W + 20, 20))
        
        if 0 <= self.selected_idx < len(self.route):
            obj = self.route[self.selected_idx]
            obj_type = obj.get("type", "object").lower()
            keys = PROP_KEYS.get(obj_type, [])
            
            # --- DÜZELTİLMİŞ DÖNGÜ VE DEĞER OKUMA ---
            for i, key in enumerate(keys):
                is_active = (i == self.prop_idx)
                c = (255, 255, 255) if is_active else (150, 150, 150)
                prefix = "> " if is_active else "  "
                
                # Değer belirleme
                if obj_type == "vfx":
                    if key == "bg_r": val = obj["bg_color"][0]
                    elif key == "bg_g": val = obj["bg_color"][1]
                    elif key == "bg_b": val = obj["bg_color"][2]
                    elif key == "p_r": val = obj["p_color"][0]
                    elif key == "p_g": val = obj["p_color"][1]
                    elif key == "p_b": val = obj["p_color"][2]
                    else: val = obj.get(key, "N/A")
                
                # --- STANDART OBJE/BLOCK DEĞER OKUMA ---
                else:
                    if key == "x": val = int(obj["pos"][0])
                    elif key == "y": val = int(obj["pos"][1])
                    elif key == "tx": val = int(obj["target"][0]) if "target" in obj else "N/A"
                    elif key == "ty": val = int(obj["target"][1]) if "target" in obj else "N/A"
                    elif key == "size_w": val = obj["size"][0] if isinstance(obj["size"], list) else "N/A"
                    elif key == "size_h": val = obj["size"][1] if isinstance(obj["size"], list) else "N/A"
                    elif key == "r": val = obj["color"][0]
                    elif key == "g": val = obj["color"][1]
                    elif key == "b": val = obj["color"][2]
                    else: val = obj.get(key, "N/A")

                # Her bir özelliği tek tek ekrana yazdır (Döngünün İÇİNDE)
                cached_draw(f"{prefix}{key}: {val}", c, (W - SIDEBAR_W + 30, 70 + i * 35))
            
            # Alt Bilgi (Döngü bittikten sonra bir kez)
            msg = "[TAB] Select, [+/-] Change, [DEL] Delete"
            cached_draw(msg, (100, 255, 100), (W - SIDEBAR_W + 20, H - 50), False, pygame.font.SysFont(None, 24))
        else:
            cached_draw("Select an object (A->Add", (100, 100, 100), (W - SIDEBAR_W + 20, 100))

        # 3. Timeline (Alt Panel)
        tl_y = H - self.timeline_h
        pygame.draw.rect(screen, (35, 35, 35), (0, tl_y, W - SIDEBAR_W, self.timeline_h))
        start_x = ((W - SIDEBAR_W) // 2) - (self.current_time * self.zoom)
        
        for s in range(600):
            x = start_x + (s * self.zoom)
            if 0 < x < W - SIDEBAR_W:
                pygame.draw.line(screen, (60, 60, 60), (x, tl_y + 40), (x, H))
                cached_draw(f"{s}s", (80, 80, 80), (x, tl_y + 20), True)

        tmp_t = 0
        for i, o in enumerate(self.route):
            tmp_t += o["duration"]
            ox = start_x + (tmp_t * self.zoom)
            if 0 < ox < W - SIDEBAR_W:
                color = (0, 255, 0) if o.get("type") == "object" else (255, 165, 0)
                if i == self.selected_idx: color = (255, 255, 255)
                pygame.draw.rect(screen, color, (ox - 4, tl_y + 60, 8, 40))

        # Playhead
        pygame.draw.line(screen, (255, 0, 0), ((W - SIDEBAR_W) // 2, tl_y), ((W - SIDEBAR_W) // 2, H), 3)


    
def editor_save(route_data):
    json_str = json.dumps({"route": route_data}, indent=4)
    if IS_WEB:
        # Web'de konsola yazdır veya window.prompt ile veriyi kullanıcıya göster
        print("--- COPY JSON BELOW ---")
        print(json_str)
        window.prompt("Copy this JSON:", json_str)
    else:
        with open("assets/custom_level.json", "w") as f:
            f.write(json_str)
        print("Saved to assets/custom_level.json")

def editor_load():
    if IS_WEB:
        data = window.prompt("Paste JSON string here:")
        return json.loads(data)["route"] if data else []
    else:
        if os.path.exists("assets/custom_level.json"):
            with open("assets/custom_level.json", "r") as f:
                return json.load(f)["route"]
    return []

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
GAME_FONT = pygame.font.SysFont(None, 35)
def cached_draw(text, color, position, center=False, font=GAME_FONT):
    key = (str(text), color)
    if key not in text_cache: text_cache[key] = font.render(str(text), True, color).convert_alpha()
    surf = text_cache[key]
    rect = surf.get_rect(center=position if center else (position[0], position[1]))
    screen.blit(surf, rect)

def draw_gradient_bg(surface, c1, c2, is_vertical):
    w, h = surface.get_size()
    # Çok küçük bir yüzey oluşturup sonra ekrana yayıyoruz (Performans için en iyisi)
    if is_vertical:
        base = pygame.Surface((1, 2))
        pygame.draw.line(base, c1, (0, 0), (0, 0))
        pygame.draw.line(base, c2, (0, 1), (0, 1))
    else:
        base = pygame.Surface((2, 1))
        pygame.draw.line(base, c1, (0, 0), (0, 0))
        pygame.draw.line(base, c2, (1, 0), (1, 0))
    
    # Ekrana pürüzsüzce yay
    pygame.transform.smoothscale(base, (w, h), surface)

def draw(objects, player, hp, show_joystick, joy_pos, current_time, bg1, bg2, is_grad, angle, p_col, shake=0, damage_flash=0):
    # 1. Sarsıntı (Shake) hesapla
    ox = random.randint(-int(shake), int(shake)) if shake > 0 else 0
    oy = random.randint(-int(shake), int(shake)) if shake > 0 else 0
    
    # 2. Arkaplan
    if is_grad:
        draw_gradient_bg(screen, bg1, bg2, angle == 1)
    else:
        screen.fill(bg1)

    
    # 3. Hasar Flaş Efekti
    if damage_flash > 0:
        flash_surf = pygame.Surface((W, H))
        flash_surf.fill((255, 0, 0))
        flash_surf.set_alpha(int(damage_flash * 120))
        screen.blit(flash_surf, (0, 0))

    # 4. Objeleri ve Blokları Çiz
    for obj in objects:
        obj.draw(screen, ox, oy)

    # main döngüsü içinde çizim sırasının en sonunda olsun (Oyuncudan hemen önce)
    for p in particles[:]:
        # Konumu güncelle
        p[0] += p[2] 
        p[1] += p[3]
        
        # Hava sürtünmesi (Hız yavaş yavaş azalsın ama başta çok hızlı olsunlar)
        p[2] *= 0.96
        p[3] *= 0.96
        
        # Ömür tüketimi (Biraz daha yavaş ölsünler ki görünsünler)
        p[5] -= 0.025 
        
        if p[5] <= 0:
            particles.remove(p)
        else:
            # Boyut Ayarı: Başlangıçta 15 pikselden başlasın (Blok parçası gibi)
            # s = int(15 * p[5]) yerine sabit bir değer + ömür çarpanı:
            s = max(4, int(12 * p[5])) 
            
            # Renk: Karartmayı kaldırdık, bloğun orijinal rengi neyse o!
            draw_col = p[4] 
            
            # Çizim (Kamera ox, oy değerlerini eklemeyi unutma)
            pygame.draw.rect(screen, draw_col, (int(p[0] + ox), int(p[1] + oy), s, s))

    # 5. Oyuncuyu Çiz (Daire şeklinde)
    player_pos = (int(player.x + ox), int(player.y + oy))
    player.trail.insert(0, player_pos)
    if len(player.trail) > player.max_trail:
        player.trail.pop()

    for i, p in enumerate(player.trail):
        # Gittikçe küçülen ve solan daireler
        t_radius = (player.rect.width // 2) * (1 - (i / player.max_trail))
        if t_radius > 1:
            # Oyuncu rengini hafif koyulaştırarak iz yap
            if isinstance(p_col, (list, tuple)):
                t_col = [max(0, c - 30) for c in p_col]
            else:
                t_col = p_col
            pygame.draw.circle(screen, t_col, p, int(t_radius))
    pygame.draw.circle(screen, p_col, (int(player.x + ox), int(player.y + oy)), player.rect.width // 2)

    # 6. Kullanıcı Arayüzü (UI)
    
    # --- HP Yazısı ---
    hp_color = (0, 255, 0) if hp > 2 else (255, 0, 0)
    cached_draw(f"HP: {int(hp)}", hp_color, (65 + ox, 35 + oy))

    # --- Zaman ve Yüzde Bilgisi ---
    m, s = divmod(int(current_time), 60)
    sm, ss = divmod(int(TOTAL_TIME), 60)
    # Ortadaki zaman yazısı
    cached_draw(f"{m:02d}:{s:02d} / {sm:02d}:{ss:02d}", "#ffffff", (W/2 + ox, 35 + oy), True)
    
    # Ortadaki yüzde yazısı
    progress_ratio = min(1.0, current_time / max(1, TOTAL_TIME))
    progress_percent = round(progress_ratio * 100, 1)
    cached_draw(f"%{progress_percent}", "#ffffff", (W/2 + ox, 70 + oy), True)

    # --- PROGRESS BAR (İlerleme Çubuğu) ---
    bar_w, bar_h = 400, 10
    bar_x = (W - bar_w) // 2 + ox
    bar_y = 95 + oy
    # Arkaplan (Boş çubuk)
    # Dolu çubuk
    if progress_ratio > 0:
        pygame.draw.rect(screen, (255, 255, 255), (0, 0, int(W * progress_ratio), 6))

    # --- Mobil Kontroller ---
    if show_joystick:
        pygame.draw.circle(screen, (150, 150, 150), JOY_CENTER, JOY_RADIUS, 2)
        pygame.draw.circle(screen, (255, 255, 255), joy_pos, JOY_STICK_RADIUS)

    if is_mobile:
        pygame.draw.rect(screen, (80, 80, 80), BTN_ESC, 0, border_radius=5)
        cached_draw("MENU", (255, 255, 255), BTN_ESC.center, True)

    if state == "FAIL_SCREEN":
        # Ekranı karart ve yazıyı yaz
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        cached_draw(f"You died at {progress_percent}%", "#ff4444", (W/2, H/2), True)
        cached_draw("Restarting...", "#ffffff", (W/2, H/2 + 50), True)

    if state == "WIN_SCREEN":
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        overlay.fill((0, 255, 0, 100))
        screen.blit(overlay, (0, 0))
        cached_draw("You won!", "#ffffff", (W/2, H/2), True)
        cached_draw("ESC For menu", "#eeeeee", (W/2, H/2 + 50), True)

    pygame.display.flip()

start_ticks = pygame.time.get_ticks()

async def main():
    global running, hp, dmgcd, objects, state, current_song_path, route, TOTAL_TIME, is_mobile, game_mode, time_scale, is_1hp, is_zen, input_active, input_text, custom_route, pygame, shake_amount, joy_pos, show_joystick, is_touching, bg_color_1, player_color,start_timer ,target_bg,target_player,restart_timer,is_vfx_smooth, vfx_start_time, vfx_total_duration
    
    screen = pygame.display.set_mode((1280, 720))
    player = Player(W//2, H//2, 25)
    route_index, music_time = 0, 0
    damage_flash = 0
    start_trigger = False
    touch_id = None
    editor = None

    if not IS_WEB:
        try:
            import pygame.scrap
            pygame.scrap.init()
        except: pass

    while running:
        raw_ms = clock.tick(60)
        dt = (raw_ms / 1000.0) * time_scale
        events = pygame.event.get()
        keys = pygame.key.get_pressed()

        # --- 1. OLAY (EVENT) DÖNGÜSÜ ---
        # Tüm tuş ve fare kontrolleri bu döngünün İÇİNDE olmalı
# --- 1. OLAY (EVENT) DÖNGÜSÜ ---
        for e in events:
            if e.type == pygame.FINGERDOWN or e.type == pygame.FINGERMOTION:
                is_touching = True
                show_joystick = True
                # Parmak koordinatlarını ekran boyutuna (W, H) çevir
                tx, ty = e.x * W, e.y * H
                
                # Sadece ekranın sol tarafı joystick'i kontrol etsin (opsiyonel)
                if tx < W / 2:
                    # Joystick'in merkezinden uzaklığı hesapla
                    dx = tx - JOY_CENTER[0]
                    dy = ty - JOY_CENTER[1]
                    dist = math.hypot(dx, dy)
                    
                    if dist <= JOY_RADIUS:
                        joy_pos = [tx, ty]
                    else:
                        # Joystick sınırında tut (Clamping)
                        angle = math.atan2(dy, dx)
                        joy_pos = [
                            JOY_CENTER[0] + math.cos(angle) * JOY_RADIUS,
                            JOY_CENTER[1] + math.sin(angle) * JOY_RADIUS
                        ]

            if e.type == pygame.FINGERUP:
                is_touching = False
                joy_pos = list(JOY_CENTER) # Bırakınca merkeze dönsün
            if e.type == pygame.QUIT:
                running = False
                break

            # --- EDITOR DURUMU OLAYLARI ---
            if state == "EDITOR" and editor:
                if e.type == pygame.KEYDOWN:
                    # Temel Navigasyon
                    if e.key == pygame.K_ESCAPE: state = "MENU"
                    if e.key == pygame.K_1: editor.mode = "OBJECT"
                    if e.key == pygame.K_2: editor.mode = "block"
                    if e.key == pygame.K_3: editor.mode = "VFX"
                    if e.key == pygame.K_RIGHT: editor.current_time += 0.5
                    if e.key == pygame.K_LEFT: editor.current_time = max(0, editor.current_time - 0.5)
                # Kopyalama (C tuşu)
                    if e.key == pygame.K_c:
                        if editor.selected_idx != -1:
                            m_pos = pygame.mouse.get_pos()
                            editor.add_element(m_pos)
                    
                    # Müzik Kontrolü (SPACE)
                    if e.key == pygame.K_SPACE:
                        editor.playing = not editor.playing
                        if editor.playing:
                            try:
                                pygame.mixer.music.load(current_song_path)
                                pygame.mixer.music.play(start=editor.current_time)
                            except: print("Müzik dosyası yüklenemedi!")
                        else:
                            pygame.mixer.music.stop()

                    # Tekli Obje Ekleme (A)
                    if e.key == pygame.K_a:
                        m_pos = pygame.mouse.get_pos()
                        if m_pos[0] < W - SIDEBAR_W:
                            editor.add_element(m_pos)

                    # Kayıt ve Yükleme
                    if e.key == pygame.K_s: editor_save(editor.route)
                    if e.key == pygame.K_l: editor.route = editor_load()

                    # Seçili Obje Parametrelerini Düzenleme
                    if 0 <= editor.selected_idx < len(editor.route):
                        obj = editor.route[editor.selected_idx]
                        o_type = obj.get("type", "object").lower()
                        p_keys = PROP_KEYS.get(o_type, [])
                        key = p_keys[editor.prop_idx]

                        # Özellik Seçme (TAB)
                        if e.key == pygame.K_TAB and p_keys:
                            editor.prop_idx = (editor.prop_idx + 1) % len(p_keys)

                        # Değer Artırma/Azaltma (+ / -)
                        change = 0
                        if e.key in [pygame.K_KP_PLUS, pygame.K_EQUALS]: change = 1
                        if e.key in [pygame.K_KP_MINUS, pygame.K_MINUS]: change = -1

                        if change != 0 and p_keys:
# ... mevcut kod ...
                            if o_type == "vfx":
                                if key == "bg_r": obj["bg_color"][0] = max(0, min(255, obj["bg_color"][0] + change * 15))
                                elif key == "bg_g": obj["bg_color"][1] = max(0, min(255, obj["bg_color"][1] + change * 15))
                                elif key == "bg_b": obj["bg_color"][2] = max(0, min(255, obj["bg_color"][2] + change * 15))
                                elif key == "p_r": obj["p_color"][0] = max(0, min(255, obj["p_color"][0] + change * 15))
                                elif key == "p_g": obj["p_color"][1] = max(0, min(255, obj["p_color"][1] + change * 15))
                                elif key == "p_b": obj["p_color"][2] = max(0, min(255, obj["p_color"][2] + change * 15))
                                # BURASI ÖNEMLİ: time_duration'ı 'time' anahtarıyla eşle
                                elif key == "time_duration" or key == "time": 
                                    obj["time_duration"] = round(max(0.1, obj.get("time_duration", 1.0) + change * 0.1), 1)
                                elif key == "smooth":
                                    obj["smooth"] = (change > 0)
                            else:
                                key = p_keys[editor.prop_idx]
                                if key == "x": obj["pos"][0] += change * 10
                                elif key == "y": obj["pos"][1] += change * 10
                                elif key == "tx": obj["target"][0] += change * 10
                                elif key == "ty": obj["target"][1] += change * 10
                                elif key == "size": obj["size"] += change * 5
                                elif key == "size_w": obj["size"][0] = max(10, obj["size"][0] + change * 10)
                                elif key == "size_h": obj["size"][1] = max(10, obj["size"][1] + change * 10)
                                elif key == "r": obj["color"][0] = max(0, min(255, obj["color"][0] + change * 15))
                                elif key == "g": obj["color"][1] = max(0, min(255, obj["color"][1] + change * 15))
                                elif key == "b": obj["color"][2] = max(0, min(255, obj["color"][2] + change * 15))
                                elif key in ["time", "etime", "adisplay"]:
                                    obj[key] = round(max(0.1, obj[key] + change * 0.1), 1)
                                elif key == "blast":
                                    obj[key] = max(0, obj[key] + change)

                        # Silme (Delete/Backspace)
                        if e.key in [pygame.K_DELETE, pygame.K_BACKSPACE]:
                            editor.route.pop(editor.selected_idx)
                            editor.selected_idx = -1

                elif e.type == pygame.MOUSEBUTTONDOWN:
                    keys = pygame.key.get_pressed()
                    step = 0.1 if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else 1.0
                    
                    if e.button == 1: # Sol Tık
                        if e.pos[0] < W - SIDEBAR_W:
                            # 1. Önce tıklanan yerde bir obje var mı diye bak (Seçim yap)
                            found = editor.select_at(e.pos)
                    
                                
                    elif e.button == 3: # Sağ Tık: Hedef Belirleme
                        editor.set_target_at(e.pos)
                    
                    # ... (tekerlek kontrolleri aynı kalıyor)

                    elif e.button == 4: # Tekerlek yukarı (Geri git)
                        editor.current_time = max(0, editor.current_time - step)
                        # Eğer müzik çalıyorsa müziği de senkronize et (İsteğe bağlı ama önerilir)
                        if editor.playing:
                            pygame.mixer.music.play(start=editor.current_time)
                            
                    elif e.button == 5: # Tekerlek aşağı (İleri git)
                        editor.current_time += step
                        if editor.playing:
                            pygame.mixer.music.play(start=editor.current_time)
                
            # --- MENÜ DURUMU OLAYLARI ---
            # --- MENÜ DURUMU OLAYLARI ---
            elif state == "MENU":
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_e:
                        editor = LevelEditor()
                        state = "EDITOR"
                    if e.key == pygame.K_SPACE: start_trigger = True
                
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    m_pos = e.pos # Tıklanan yer
                    
                    # --- Seviye Seçimi ---
                    song_list = list(SONGS.keys())
                    for i, song_path in enumerate(song_list):
                        rect = pygame.Rect(0, 0, 400, 40)
                        rect.center = (W//2, H//2 + (i * 50))
                        if rect.collidepoint(m_pos):
                            current_song_path = song_path

                    # --- Modifier Butonları ---
                    if BTN_1HP.collidepoint(m_pos): is_1hp = not is_1hp
                    if BTN_ZEN.collidepoint(m_pos): is_zen = not is_zen
                    
                    if BTN_FAST.collidepoint(m_pos):
                        time_scale = 1.25 if time_scale == 1.0 else 1.0
                    if BTN_SLOW.collidepoint(m_pos):
                        time_scale = 0.75 if time_scale == 1.0 else 1.0
                    
                    # Custom JSON Alanı
                    if BTN_CUSTOM.collidepoint(m_pos): input_active = True
                    else: input_active = False

                    # Başlat Butonu
                    if BTN_START.collidepoint(m_pos): start_trigger = True
            # --- OYUN İÇİ OLAYLAR ---
            elif state == "GAME":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    pygame.mixer.music.stop()
                    state = "MENU"

        # --- 2. OYUN BAŞLATMA MANTIĞI ---
# --- 2. OYUN BAŞLATMA MANTIĞI ---
        if start_trigger:
            state = "GAME"
            SKIP_TIME = OG_SKIP_TIME / time_scale
            objects, route_index = [], 0
            
            # Değişkenleri sıfırla
            music_time = SKIP_TIME # Müziğin başlayacağı sanal süre
            start_timer = 1.0      # 1 saniye hazırlık süresi
            
            if custom_route: 
                route = custom_route; TOTAL_TIME = 600
            else:
                route = CACHED_DATA.get(current_song_path, [])
                p = current_song_path
                if time_scale > 1.0: p = SONGS[p].get("fast", p)
                elif time_scale < 1.0: p = SONGS[p].get("slow", p)
                pygame.mixer.music.load(p)
                TOTAL_TIME = pygame.mixer.Sound(p).get_length()

            spawn_times = [0]
            curr = 0
            for d in route:
                curr += d["duration"] / time_scale
                spawn_times.append(curr)
            
            # route_index'i SKIP_TIME'a göre ayarla (Mermileri atlamak için)
            route_index = 0
            while route_index < len(spawn_times) and spawn_times[route_index] < SKIP_TIME: 
                route_index += 1
            
            hp = 1 if is_1hp else 10
            player.x, player.y = W//2, H//2
            player.trail = []
            start_trigger = False
            continue
        # --- 3. GÜNCELLEME VE ÇİZİM ---
# --- 3. GÜNCELLEME VE ÇİZİM ---
        if state == "GAME":
            if start_timer > 0:
                start_timer -= dt
                # Geri sayım sırasında music_time sabit kalmalı (SKIP_TIME'da bekliyor)
                if start_timer <= 0:
                    pygame.mixer.music.play(start=SKIP_TIME)
            else:
                # Müzik çalarken süreyi Mixer'dan al
                m_pos = pygame.mixer.music.get_pos()
                if m_pos != -1:
                    music_time = (m_pos / 1000.0) + SKIP_TIME
                else:
                    music_time += dt

            # --- SPAWN MANTIĞI ---
            while route_index < len(route) and music_time >= spawn_times[route_index]:
                d = route[route_index]
                st = spawn_times[route_index]
                o_type = d.get("type", "object").lower()

                if o_type == "vfx":
                    current_vfx_start_time = music_time
                    current_vfx_duration = d.get("time_duration", 1.0)
                    target_bg = list(d["bg_color"])
                    target_player = list(d["p_color"])
                    is_vfx_smooth = d.get("smooth", True)
                    
                    # Eğer smooth değilse anında eşitle
                    if not is_vfx_smooth:
                        bg_color_1 = list(target_bg)
                        player_color = list(target_player)
                elif o_type == "block":
                    objects.append(Block(tuple(d["pos"]), tuple(d["size"]), tuple(d["color"]), st, d["etime"], d["adisplay"]))
                elif o_type == "object":
                    objects.append(Object(d["pos"], d["target"], d["easing"], d["color"], d["size"], d["time"], st, blast=d.get("blast", 0), effect=d.get("effect")))
                
                route_index += 1

            # --- GÖRSEL GEÇİŞLER (Sadece 1 saniye bekleme bittiyse başlar) ---
            if start_timer <= 0:
                # current_vfx_start_time tanımlanmamışsa hata vermemesi için basit bir try-except veya mantık kontrolü:
                if 'current_vfx_start_time' in locals() and is_vfx_smooth and music_time < (current_vfx_start_time + current_vfx_duration):
                    rem_time = (current_vfx_start_time + current_vfx_duration) - music_time
                    if rem_time > 0:
                        step = dt / rem_time
                        for i in range(3):
                            bg_color_1[i] += (target_bg[i] - bg_color_1[i]) * min(1.0, step)
                            player_color[i] += (target_player[i] - player_color[i]) * min(1.0, step)
                elif 'target_bg' in locals():
                    # Süre dolduysa tam hedefe sabitle (EKRANI SİYAH YAPAN HATA BURADAYDI)
                    bg_color_1 = list(target_bg)
                    player_color = list(target_player)

            # --- HAREKET VE ÇARPIŞMA KONTROLLERİ ---
            player.move(dt, keys, get_joy_axis())
            for obj in objects[:]:
                if isinstance(obj, Object):
                    obj.move(music_time)
                    if not is_zen and dmgcd <= 0 and player.rect.colliderect(obj.rect):
                        if obj.blast is None: hp -= 1; dmgcd, shake_amount, damage_flash = 2.0, 15, 1.0; hit_sound.play(); obj.remove()
                elif isinstance(obj, Block):
                    obj.update(music_time)
                    if obj.end: objects.remove(obj)
                    elif not is_zen and dmgcd <= 0 and obj.dmg and player.rect.colliderect(obj.rect):
                        hp -= 1; dmgcd, shake_amount, damage_flash = 1.0, 15, 1.0; hit_sound.play()

            if dmgcd > 0: dmgcd -= dt
            if damage_flash > 0: damage_flash -= dt * 2
            if shake_amount > 0: shake_amount -= 40 * (raw_ms / 1000.0)
            
            draw(
                objects, 
                player, 
                hp, 
                show_joystick, 
                joy_pos, 
                music_time, 
                bg_color_1,     # bg1: Arkaplan rengi
                (50, 50, 50),  # bg2: Gradyan için ikinci renk
                False,         # is_grad: Gradyan aktif mi?
                0,             # angle: Gradyan yönü
                player_color, # p_col: Oyuncu rengi
                shake_amount, 
                damage_flash
            )
            
            if hp <= 0 and not is_zen:
                percent = int((music_time / TOTAL_TIME) * 100)
                save_score(current_song_path, percent)
                state = "FAIL_SCREEN" # Fail ekranına geçiş
                pygame.mixer.music.stop()
            elif int(music_time) >= TOTAL_TIME - 0.5: # Tolerans payı
                save_score(current_song_path, 100)
                state = "WIN_SCREEN" # Win ekranına geçiş
                pygame.mixer.music.stop()

        elif state == "MENU":
            start_timer = 1
            music_time = 0
            bg_color_1 = [0, 0, 0]
            bg_color_2 = [0, 0, 0]
            is_gradient_active = False
            bg_angle = 0
            player_color = [255, 255, 255]
            draw_menu()
            pygame.display.flip()

        # --- Yeni State Mantıkları ---
        if state == "FAIL_SCREEN":
            restart_timer -= dt
            if restart_timer <= 0:
                progress_ratio = min(1.0, music_time / max(1, TOTAL_TIME))
                progress_percent = round(progress_ratio * 100, 1)
                # Oyun resetleme fonksiyonunu çağır (değişkenleri sıfırla)
                save_score(current_song_path, progress_percent)
                start_trigger = True
                start_timer = 1.0 # Başlarken de 1 sn bekle

        if state == "WIN_SCREEN":
            # Win ekranında oyuncu bir tuşa basana kadar bekleyebilir
            save_score(current_song_path, progress_percent)
            state == "MENU"

    # main içindeki EDITOR durumunda:
    # --- main() EN ALT KISIMDAKİ EDİTÖR DÖNGÜSÜ ---
        elif state == "EDITOR":
            if editor.playing:
                editor.current_time += dt / time_scale

            # 1. ZAMANA GÖRE AKTİF VFX'İ BUL (PREVIEW)
            active_vfx = None
            for obj in editor.route:
                if obj.get("type", "object") == "vfx" and obj.get("time", 0) <= editor.current_time:
                    active_vfx = obj
            
            # 2. HEDEF RENKLERİ GÜNCELLE
            if active_vfx:
                target_bg = list(active_vfx.get("bg_color", [0, 0, 0]))
                target_player = list(active_vfx.get("p_color", [0, 255, 255]))
                
                # Eğer Smooth kapalıysa şak diye hedef renge eşitle!
                if not active_vfx.get("smooth", True):
                    bg_color_1 = list(target_bg)
                    player_color = list(target_player)

            # 3. YUMUŞAK GEÇİŞ (EASING) HESAPLAMA
            for i in range(3):
                bg_color_1[i] += (target_bg[i] - bg_color_1[i]) * 0.05
                player_color[i] += (target_player[i] - player_color[i]) * 0.05

            # 4. ÇİZİM
            screen.fill(bg_color_1) # Artık düz siyah değil, gerçek bg rengi!
            editor.draw(screen)
            pygame.display.flip()

        await asyncio.sleep(0)

    pygame.quit()

asyncio.run(main())