import pygame
import random
import sys
import asyncio

pygame.init()

CELL = 32
COLS = 10
ROWS = 20
PANEL_WIDTH = 250 # Panel biraz daraltıldı
BOARD_WIDTH = COLS * CELL
WIDTH = BOARD_WIDTH + PANEL_WIDTH
HEIGHT = ROWS * CELL

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tetris - Highscore & Next Piece")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

SHAPES = [
    [[(0,0),(0,1),(0,2),(0,3)], [(0,0),(1,0),(2,0),(3,0)]], # I
    [[(0,0),(1,0),(0,1),(1,1)]], # O
    [[(0,0),(1,0),(2,0),(1,1)], [(1,0),(0,1),(1,1),(1,2)], [(0,1),(1,1),(2,1),(1,0)], [(0,0),(0,1),(0,2),(1,1)]], # T
    [[(0,0),(0,1),(0,2),(1,2)], [(0,0),(1,0),(2,0),(0,1)], [(0,0),(1,0),(1,1),(1,2)], [(2,0),(0,1),(1,1),(2,1)]], # L
    [[(1,0),(1,1),(1,2),(0,2)], [(0,0),(0,1),(1,0),(2,0)], [(0,0),(0,1),(0,2),(1,0)], [(0,0),(1,1),(2,1),(0,1)]], # J
    [[(1,0),(2,0),(0,1),(1,1)], [(0,0),(0,1),(1,1),(1,2)]], # S
    [[(0,0),(1,0),(1,1),(2,1)], [(1,0),(0,1),(1,1),(0,2)]]  # Z
]

COLORS = [
    (0,0,0),
    (0,255,255), (255,255,0), (128,0,128),
    (255,165,0), (0,0,255), (0,255,0), (255,0,0)
]

# Buton boyutları
BTN_SIZE = 55
PANEL_X_START = BOARD_WIDTH + 10 # Panel başlama koordinatı

# Panel içinde buton yerleşimi (Daha ergonomik bir dizilim)
btn_left   = pygame.Rect(PANEL_X_START + 20,  HEIGHT - 140, BTN_SIZE, BTN_SIZE)
btn_right  = pygame.Rect(PANEL_X_START + 140, HEIGHT - 140, BTN_SIZE, BTN_SIZE)
btn_down   = pygame.Rect(PANEL_X_START + 80,  HEIGHT - 80,  BTN_SIZE, BTN_SIZE)
btn_rotate = pygame.Rect(PANEL_X_START + 80,  HEIGHT - 200, BTN_SIZE, BTN_SIZE)

class Game:
    def __init__(self):
        self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.timer = 0
        self.speed = 0.5
        self.score = 0
        self.highscore = 0
        self.end = False
        
        # Gelecek parçayı belirle
        self.next_shape_idx = random.randint(0, len(SHAPES)-1)
        self.next_color_idx = random.randint(1, len(COLORS)-1)
        
        self.spawn_piece()

    def spawn_piece(self):
        # Mevcut parça, "gelecek parça"dan gelir
        self.piece_group = SHAPES[self.next_shape_idx]
        self.piece = random.choice(self.piece_group)
        self.color = self.next_color_idx
        
        # Yeni bir "gelecek parça" oluştur
        self.next_shape_idx = random.randint(0, len(SHAPES)-1)
        self.next_color_idx = random.randint(1, len(COLORS)-1)

        self.px = COLS // 2 - 2
        self.py = 0

        if self.collision(self.px, self.py):
            self.end = True
            if self.score > self.highscore:
                self.highscore = self.score

    def collision(self, x, y, piece=None):
        if piece is None: piece = self.piece
        for dx, dy in piece:
            nx, ny = x + dx, y + dy
            if nx < 0 or nx >= COLS or ny >= ROWS: return True
            if ny >= 0 and self.board[ny][nx] != 0: return True
        return False

    def lock_piece(self):
        for dx, dy in self.piece:
            self.board[self.py + dy][self.px + dx] = self.color
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
            new_board = [row for row in self.board if 0 in row]
            lines_cleared = ROWS - len(new_board)
            
            while len(new_board) < ROWS:
                new_board.insert(0, [0 for _ in range(COLS)])
            
            self.board = new_board
            
            # Skorlama
            scores = [0, 100, 300, 500, 800]
            self.score += scores[min(lines_cleared, 4)]

            # --- HIZLANMA MANTIĞI ---
            # Her 500 puanda bir hızı %10 artır (yani bekleme süresini azalt)
            # 0.1 saniyenin altına düşmemesini sağlayarak oyunun imkansızlaşmasını önlüyoruz.
            base_speed = 0.5
            speed_multiplier = (self.score // 500) * 0.05
            self.speed = max(0.1, base_speed - speed_multiplier)

    def update(self, dt):
        if self.end: return
        self.timer += dt
        if self.timer >= self.speed:
            self.timer = 0
            if not self.collision(self.px, self.py + 1):
                self.py += 1
            else:
                self.lock_piece()

    def move(self, dx):
        if not self.collision(self.px + dx, self.py):
            self.px += dx

    def rotate(self):
        # List comprehension ile 90 derece döndürme matrisi (y, -x)
        new_piece = [(y, -x) for (x, y) in self.piece]
        # Koordinatları normalize et (0,0'a çek)
        min_x = min(x for x, y in new_piece)
        min_y = min(y for x, y in new_piece)
        new_piece = [(x - min_x, y - min_y) for x, y in new_piece]

        for shift in [0, -1, 1, -2, 2]:
            if not self.collision(self.px + shift, self.py, new_piece):
                self.piece = new_piece
                self.px += shift
                break

    def draw(self):
        screen.fill((20, 20, 20)) # Arka planı biraz gri yapalım

        # Oyun Alanını Çiz
        for y in range(ROWS):
            for x in range(COLS):
                color = COLORS[self.board[y][x]]
                rect = (x*CELL, y*CELL, CELL, CELL)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (40, 40, 40), rect, 1)

        # Hareket Eden Parçayı Çiz
        if not self.end:
            for dx, dy in self.piece:
                rect = ((self.px + dx)*CELL, (self.py + dy)*CELL, CELL, CELL)
                pygame.draw.rect(screen, COLORS[self.color], rect)
                pygame.draw.rect(screen, (255, 255, 255), rect, 1)

        # --- PANEL ÇİZİMİ ---
        panel_x = BOARD_WIDTH + 20
        
        # Skorlar
        score_txt = font.render(f"Score: {self.score}", True, (255, 255, 255))
        high_txt = font.render(f"High: {self.highscore}", True, (255, 215, 0))
        screen.blit(score_txt, (panel_x, 50))
        screen.blit(high_txt, (panel_x, 90))

        # Sonraki Parça (Next Piece)
        next_txt = font.render("Next Piece:", True, (200, 200, 200))
        screen.blit(next_txt, (panel_x, 180))
        
        next_shape_preview = SHAPES[self.next_shape_idx][0] # İlk rotasyonu göster
        for dx, dy in next_shape_preview:
            p_rect = (panel_x + dx*CELL, 230 + dy*CELL, CELL, CELL)
            pygame.draw.rect(screen, COLORS[self.next_color_idx], p_rect)
            pygame.draw.rect(screen, (255, 255, 255), p_rect, 1)

        if self.end:
            over_txt = font.render("GAME OVER! Press R", True, (255, 50, 50))
            screen.blit(over_txt, (panel_x - 30, HEIGHT // 2))


    def draw_controls(self):
        # Buton listesi: (Rect, Etiket, Renk)
        btns = [
            (btn_left, "<", (70, 70, 70)), 
            (btn_right, ">", (70, 70, 70)), 
            (btn_down, "V", (70, 70, 70)), 
            (btn_rotate, "ROT", (50, 120, 200)) # Döndürme butonu farklı renk
        ]
        
        for rect, label, color in btns:
            # Buton gölgesi/çerçevesi
            pygame.draw.rect(screen, color, rect, border_radius=12)
            pygame.draw.rect(screen, (200, 200, 200), rect, 2, border_radius=12)
            
            # Etiket yazısı
            txt = font.render(label, True, (255, 255, 255))
            text_rect = txt.get_rect(center=rect.center)
            screen.blit(txt, text_rect)

    def reset(self):
        self.board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.end = False
        self.spawn_piece()

game = Game()

async def main():
    while True:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Klavye Kontrolleri
            if event.type == pygame.KEYDOWN:
                if not game.end:
                    if event.key == pygame.K_LEFT: game.move(-1)
                    if event.key == pygame.K_RIGHT: game.move(1)
                    if event.key == pygame.K_DOWN: game.update(1)
                    if event.key == pygame.K_UP: game.rotate()
                else:
                    if event.key == pygame.K_r: game.reset()

            # MOBİL / DOKUNMATİK KONTROLLER (MOUSEBUTTONDOWN dokunmayı da kapsar)
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if not game.end:
                    if btn_left.collidepoint(pos): game.move(-1)
                    if btn_right.collidepoint(pos): game.move(1)
                    if btn_down.collidepoint(pos): game.update(1)
                    if btn_rotate.collidepoint(pos): game.rotate()
                else:
                    # Oyun bittiyse ekranın herhangi bir yerine basınca resetle
                    game.reset()

        game.update(dt)
        game.draw()
        game.draw_controls() # Butonları ekrana basar
        pygame.display.flip()
        await asyncio.sleep(0)

asyncio.run(main())