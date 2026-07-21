import csv
import os
import random
import sys
import math

import pygame


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "assets")

pygame.init()

WIDTH, HEIGHT = 1280, 720
FPS = 60

WHITE = (245, 247, 255)
BLACK = (0, 0, 0) # black or white
SKY_TOP = (103, 176, 255)
SKY_BOTTOM = (182, 229, 255)
GREEN = (72, 201, 120)
DARK_GREEN = (38, 120, 70)
ORANGE = (255, 161, 72)
RED = (255, 84, 84)
NAVY = (8, 15, 33)
PANEL = (15, 22, 44)
PANEL_SOFT = (28, 38, 66)
BUTTON = (246, 247, 251)
BUTTON_HOVER = (255, 229, 184)
TEXT_DIM = (195, 205, 230)
PANEL_TEXT = (140, 110, 80)
AWS_ORANGE = (163, 0, 255) 

STATE_MENU = "MENU"
STATE_GET_READY = "GET_READY"
STATE_CREDITS = "CREDITS"
STATE_PLAYING = "PLAYING"
STATE_QUIZ = "QUIZ"
STATE_GAME_OVER = "GAME_OVER"
STATE_SPIN_WHEEL = "SPIN_WHEEL"

def _load_aws_words():
    return [
        {"word": "ec2", "meaning": "Elastic Compute Cloud"},
        {"word": "kyashwanth", "meaning": "michael jackson fan"},
        {"word": "s3", "meaning": "Simple Storage Service"},
        {"word": "lambda", "meaning": "Serverless Compute"},
        {"word": "dynamodb", "meaning": "NoSQL Database"},
        {"word": "vpc", "meaning": "Virtual Private Cloud"},
        {"word": "rds", "meaning": "Relational Database Service"},
        {"word": "iam", "meaning": "Identity and Access Management"},
        {"word": "cloudfront", "meaning": "Content Delivery Network"},
        {"word": "route53", "meaning": "Scalable DNS"},
        {"word": "cloudwatch", "meaning": "Monitoring and Management"},
        {"word": "ec2", "meaning": "Virtual Servers"},
        {"word": "lambda", "meaning": "Serverless Compute"},
        {"word": "lightsail", "meaning": "Simplified Virtual Private Servers"},
        {"word": "elastic_beanstalk", "meaning": "Platform as a Service Deployment"},
        {"word": "batch", "meaning": "Managed Batch Computing"},
        {"word": "app_runner", "meaning": "Managed Web Application Deployment"},
        {"word": "outposts", "meaning": "AWS Infrastructure On Premises"},
        {"word": "local_zones", "meaning": "Low Latency AWS Infrastructure"},
        {"word": "wavelength", "meaning": "Edge Computing for 5G Networks"}
    ]

AWS_WORDS = _load_aws_words()

THEMES = {
    "grass": {"ground": "groundGrass.png", "rock_up": "rockGrass.png",    "rock_down": "rockGrassDown.png"},
    "dirt":  {"ground": "groundDirt.png",  "rock_up": "rock.png",          "rock_down": "rockDown.png"},
    "ice":   {"ground": "groundIce.png",   "rock_up": "rockIce.png",       "rock_down": "rockIceDown.png"},
    "snow":  {"ground": "groundSnow.png",  "rock_up": "rockSnow.png",      "rock_down": "rockSnowDown.png"},
}
PLANE_COLORS = ["Blue", "Green", "Red", "Yellow"]

PIPE_SPACING      = 340   # base spacig for pipe spawingng
PIPE_WIDTH        = 90
GROUND_HEIGHT     = 71
PLAYABLE_H        = HEIGHT - GROUND_HEIGHT
GAP_MIN           = 155
GAP_MAX           = 215
GAP_MARGIN        = 80
MAX_GAP_SHIFT     = 140
STAR_SPAWN_CHANCE = 0.65


def ensure_assets_dir():
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)


def load_png_image(name, fallback_color, size, *, alpha=True):
    path = os.path.join(ASSETS_DIR, "PNG", name)
    if os.path.exists(path):
        try:
            image = pygame.image.load(path)
            image = image.convert_alpha() if alpha else image.convert()
            return pygame.transform.smoothscale(image, size)
        except pygame.error:
            pass
    surface = pygame.Surface(size, pygame.SRCALPHA if alpha else 0)
    surface.fill(fallback_color)
    return surface


def load_plane_frames(color):
    return [load_png_image(f"Planes/plane{color}{i}.png", ORANGE, (54, 45)) for i in range(1, 4)]


def load_fonts():
    font_path = os.path.join(ASSETS_DIR, "fonts", "PressStart2P-Regular.ttf")
    if not os.path.exists(font_path):

        font_path = os.path.join(ASSETS_DIR, "font.ttf")

    standard_font = pygame.font.SysFont("segoe ui", 16)
    if os.path.exists(font_path):
        return {
            "logo":       pygame.font.Font(font_path, 50),
            "menu_title": pygame.font.Font(font_path, 20),
            "title":      pygame.font.Font(font_path, 26),
            "subtitle":   pygame.font.Font(font_path, 14),
            "body":       pygame.font.Font(font_path, 12),
            "small":      pygame.font.Font(font_path, 9),
            "standard":   standard_font,
        }
    return {
        "logo":       pygame.font.SysFont("georgia",  72, bold=True),
        "menu_title": pygame.font.SysFont("georgia",  40, bold=True),
        "title":      pygame.font.SysFont("georgia",  56, bold=True),
        "subtitle":   pygame.font.SysFont("segoe ui", 28, bold=True),
        "body":       pygame.font.SysFont("segoe ui", 26),
        "small":      pygame.font.SysFont("segoe ui", 18),
        "standard":   standard_font,
    }


def get_viewport(window_size):
    ww, wh = window_size
    scale = min(ww / WIDTH, wh / HEIGHT)
    sw, sh = int(WIDTH * scale), int(HEIGHT * scale)
    return scale, (ww - sw) // 2, (wh - sh) // 2, sw, sh


def to_internal(pos, viewport):
    scale, xo, yo, _, _ = viewport
    return (pos[0] - xo) / scale, (pos[1] - yo) / scale


def wrap_text(text, font, max_width):
    words, lines, current = text.split(), [], ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current: lines.append(current)
            current = word
    if current: lines.append(current)
    return lines or [""]


def draw_centered_lines(surface, lines, font, color, cx, top_y, gap=8):
    y = top_y
    for line in lines:
        t = font.render(line, True, color)
        surface.blit(t, (cx - t.get_width() // 2, y))
        y += t.get_height() + gap


def draw_button(surface, rect, label, fonts, button_img=None, mouse_pos=None):
    hovered = mouse_pos is not None and rect.collidepoint(mouse_pos)
    sr = rect.inflate(16, 10) if hovered else rect
    if button_img:
        surface.blit(pygame.transform.smoothscale(button_img, (sr.width, sr.height)), sr.topleft)
        if hovered:
            ov = pygame.Surface((sr.width, sr.height), pygame.SRCALPHA)
            ov.fill((255, 255, 255, 45))
            surface.blit(ov, sr.topleft)
    else:
        pygame.draw.rect(surface, BUTTON_HOVER if hovered else BUTTON, sr, border_radius=18)
        pygame.draw.rect(surface, NAVY, sr, width=3, border_radius=18)
    text = fonts["subtitle"].render(label, True, NAVY)
    surface.blit(text, (sr.centerx - text.get_width() // 2, sr.centery - text.get_height() // 2))


def _build_mask(surf):
    return pygame.mask.from_surface(surf)


class Bird:
    def __init__(self):
        self.width = 54; self.height = 45
        self.x = 200.0; self.y = 360.0
        self.velocity = 0.0; self.gravity = 0.45; self.jump_strength = -8.8
        self.rect = pygame.Rect(int(self.x), int(self.y), self.width, self.height)
        self.frames = []; self.frame_index = 0; self.animation_counter = 0

    def set_frames(self, frames):
        self.frames = frames; self.frame_index = 0; self.animation_counter = 0

    def reset(self):
        self.x = 200.0; self.y = 360.0; self.velocity = 0.0
        self.rect.topleft = (int(self.x), int(self.y))

    def jump(self): self.velocity = self.jump_strength

    def update(self):
        self.velocity = min(self.velocity + self.gravity, 12)
        self.y += self.velocity
        self.rect.topleft = (int(self.x), int(self.y))
        if self.frames:
            self.animation_counter += 1
            if self.animation_counter >= 5:
                self.animation_counter = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)

    def _surf(self):
        if self.frames:
            angle = max(-30, min(30, -self.velocity * 2.5))
            return pygame.transform.rotate(self.frames[self.frame_index], angle)
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA); s.fill(ORANGE); return s

    def draw(self, surface):
        s = self._surf()
        r = s.get_rect(center=(int(self.x + self.width / 2), int(self.y + self.height / 2)))
        surface.blit(s, r.topleft)

    def get_draw_info(self):
        s = self._surf()
        r = s.get_rect(center=(int(self.x + self.width / 2), int(self.y + self.height / 2)))
        return s, r.topleft


class Pipe:
    """
    Pixel-perfect collision pipe using pygame.mask.
    The bounding rects are kept for a cheap broad-phase pass before
    the more expensive mask overlap test.
    """
    def __init__(self, x, speed, gap_center_y, gap_size):
        self.x = float(x); self.speed = speed; self.width = PIPE_WIDTH
        self.gap_center_y = gap_center_y; self.gap_size = gap_size
        half = gap_size // 2
        self.top_height   = gap_center_y - half
        self.bottom_y     = gap_center_y + half
        self.bottom_height = HEIGHT - self.bottom_y
        self.passed = False
        self.top_rect    = pygame.Rect(int(x), 0, PIPE_WIDTH, max(1, self.top_height))
        self.bottom_rect = pygame.Rect(int(x), self.bottom_y, PIPE_WIDTH, max(1, self.bottom_height))
        self._top_surf = self._bottom_surf = None
        self._top_mask = self._bottom_mask = None

    def update(self):
        self.x -= self.speed
        self.top_rect.x = self.bottom_rect.x = int(self.x)

    @property
    def right(self): return self.x + self.width

    def _ensure(self, top_image, bottom_image):
        """
        Build cached composite surfaces for each half of the pipe.

        Each rock sprite (108×239) contains a pointed tip + a body section.
        We scale it to PIPE_WIDTH wide and keep aspect ratio for height.
        If the pipe section is taller than the natural rock height, we
        fill the remaining space by stretching a 1-pixel slice from the 
        widest base part of the rock. This forms a seamless pillar body.
        """
        W = self.width

        if self._top_surf is None:
            h = max(1, self.top_height)
            surf = pygame.Surface((W, h), pygame.SRCALPHA)

            if top_image and h > 0:
                nat_h = int(W * top_image.get_height() / max(1, top_image.get_width()))
                nat_h = min(nat_h, h)

                body_h = h - nat_h
                if body_h > 0:
                    slice_y = min(5, top_image.get_height() - 1)
                    body_sample = top_image.subsurface((0, slice_y, top_image.get_width(), 1))
                    body_sample = pygame.transform.scale(body_sample, (W, body_h))
                    surf.blit(body_sample, (0, 0))

                tip_surf = pygame.transform.smoothscale(top_image, (W, nat_h))
                surf.blit(tip_surf, (0, body_h))
            else:
                surf.fill(DARK_GREEN)

            self._top_surf = surf
            self._top_mask = _build_mask(surf)

        if self._bottom_surf is None:
            h = max(1, self.bottom_height)
            surf = pygame.Surface((W, h), pygame.SRCALPHA)

            if bottom_image and h > 0:
                nat_h = int(W * bottom_image.get_height() / max(1, bottom_image.get_width()))
                nat_h = min(nat_h, h)

                body_h = h - nat_h
                if body_h > 0:
                    slice_y = max(0, bottom_image.get_height() - 6)
                    body_sample = bottom_image.subsurface((0, slice_y, bottom_image.get_width(), 1))
                    body_sample = pygame.transform.scale(body_sample, (W, body_h))
                    surf.blit(body_sample, (0, nat_h))

                tip_surf = pygame.transform.smoothscale(bottom_image, (W, nat_h))
                surf.blit(tip_surf, (0, 0))
            else:
                surf.fill(GREEN)

            self._bottom_surf = surf
            self._bottom_mask = _build_mask(surf)

    def invalidate_cache(self): self._top_surf = self._bottom_surf = self._top_mask = self._bottom_mask = None

    def draw(self, surface, top_image, bottom_image):
        self._ensure(top_image, bottom_image)
        if self.top_height > 0:    surface.blit(self._top_surf,    (int(self.x), 0))
        if self.bottom_height > 0: surface.blit(self._bottom_surf, (int(self.x), self.bottom_y))

    def collides_with_bird(self, bird_surf, bird_pos, top_image, bottom_image):
        """Pixel-perfect collision — broad rect check first, then mask overlap."""
        self._ensure(top_image, bottom_image)
        bird_rect = bird_surf.get_rect(topleft=bird_pos)
        bm = None
        if self.top_height > 0 and bird_rect.colliderect(self.top_rect):
            bm = bm or _build_mask(bird_surf)
            offset = (self.top_rect.x - bird_pos[0], self.top_rect.y - bird_pos[1])
            if bm.overlap(self._top_mask, offset): return True
        if self.bottom_height > 0 and bird_rect.colliderect(self.bottom_rect):
            bm = bm or _build_mask(bird_surf)
            offset = (self.bottom_rect.x - bird_pos[0], self.bottom_rect.y - bird_pos[1])
            if bm.overlap(self._bottom_mask, offset): return True
        return False


def draw_score(surface, score_val, x_center, y, number_images, dw=26, dh=39):
    score_str = str(int(score_val))
    spacing = int(dw * 1.08)
    start_x = x_center - len(score_str) * spacing // 2
    for ch in score_str:
        d = int(ch)
        if number_images[d]:
            surface.blit(pygame.transform.smoothscale(number_images[d], (dw, dh)), (start_x, y))
        start_x += spacing


class LevelGenerator:
    """
    Generates consistent pipe positions:
    - Horizontal spacing is randomised per-pipe for an erratic feel.
    - Gap center drifts by at most MAX_GAP_SHIFT between consecutive pipes.
    - Gap size shrinks with score (difficulty scaling).
    - Stars placed inside the gap near centre.
    """
    def __init__(self):
        self.last_center = PLAYABLE_H // 2

    def reset(self):
        self.last_center = PLAYABLE_H // 2

    def gap_size(self, score):
        return max(GAP_MIN, GAP_MAX - (score // 5) * 10)

    def next_pipe(self, score):
        """Return (gap_center_y, gap_size) only — x is computed by spawn_pipe()."""
        gsz  = self.gap_size(score)
        half = gsz // 2
        y_min = GAP_MARGIN + half
        y_max = PLAYABLE_H - GAP_MARGIN - half
        # Occasionally apply a big sudden jump for extra chaos
        if random.random() < 0.25:
            drift = random.randint(-MAX_GAP_SHIFT, MAX_GAP_SHIFT) * 2
        else:
            drift = random.randint(-MAX_GAP_SHIFT, MAX_GAP_SHIFT)
        center = max(y_min, min(y_max, self.last_center + drift))
        self.last_center = center
        return center, gsz

    def star_in_gap(self, gap_center_y, gap_size):
        half      = gap_size // 2
        max_off   = int(half * 0.4)
        sy        = gap_center_y + random.randint(-max_off, max_off) - 20
        sx_rel    = random.randint(80, 260)
        return sx_rel, sy


def main():
    ensure_assets_dir()
    global window
    window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("AWS fireplane")
    # taskbar icon
    _icon_path = os.path.join(ASSETS_DIR, "aws cloud club.png")
    if os.path.exists(_icon_path):
        _icon = pygame.image.load(_icon_path).convert_alpha()
        _icon = pygame.transform.smoothscale(_icon, (64, 64))
        pygame.display.set_icon(_icon)
    clock  = pygame.time.Clock()
    canvas = pygame.Surface((WIDTH, HEIGHT))
    fonts  = load_fonts()

    button_image    = load_png_image("UI/buttonLarge.png",  BUTTON, (300, 58))
    get_ready_image = load_png_image("UI/textGetReady.png", ORANGE, (300, 54))
    tap_image       = load_png_image("UI/tap.png",          WHITE,  (60,  60))
    tap_tick_image  = load_png_image("UI/tapTick.png",      WHITE,  (60,  60))
    ui_bg_image     = load_png_image("UI/UIbg.png",         PANEL,  (660, 360))

    # collectibles pool size to 40,40
    _SZ = (40, 40)
    def _load(path, fallback=ORANGE):
        p = os.path.join(ASSETS_DIR, path)
        if os.path.exists(p):
            return pygame.transform.smoothscale(pygame.image.load(p).convert_alpha(), _SZ)
        s = pygame.Surface(_SZ, pygame.SRCALPHA); s.fill(fallback); return s

    collectible_images = [
        _load("PNG/starGold.png",   ORANGE),
        _load("PNG/starSilver.png", (200, 200, 200)),
        _load("PNG/starBronze.png", (180, 100, 30)),
        _load("tunk_tunk.png",      (255, 200, 0)),
        _load("peach.png",          (255, 180, 120)),
        _load("ElastiCache.png",    (255, 153, 0)),
        _load("Managed Blockchain.png", (0, 164, 228)),
        _load("Quantum Ledger Database.png", (140, 75, 255)),
    ]
    for root_file in os.listdir(ASSETS_DIR):
        if root_file.lower().endswith(".png") and root_file.lower() != "aws cloud club.png":
            img_item = _load(root_file, ORANGE)
            if img_item not in collectible_images:
                collectible_images.append(img_item)
    icons_dir = os.path.join(ASSETS_DIR, "PNG", "Icons")
    if os.path.exists(icons_dir):
        for icon_file in os.listdir(icons_dir):
            if icon_file.lower().endswith(".png"):
                collectible_images.append(_load(os.path.join("PNG", "Icons", icon_file), ORANGE))

    def _load_puff(name, size):
        p = os.path.join(ASSETS_DIR, "PNG", name)
        if os.path.exists(p):
            return pygame.transform.smoothscale(pygame.image.load(p).convert_alpha(), size)
        s = pygame.Surface(size, pygame.SRCALPHA); s.fill((220, 220, 220, 180)); return s

    puff_imgs = [
        _load_puff("puffLarge.png", (52, 52)),
        _load_puff("puffSmall.png", (30, 30)),
    ]

    def load_anim_sequence(folder_name, prefix, count, size):
        frames = []
        folder = os.path.join(ASSETS_DIR, "PNG", folder_name)
        for i in range(1, count + 1):
            p = os.path.join(folder, f"{prefix}{i}.png")
            if os.path.exists(p):
                try:
                    img = pygame.image.load(p).convert_alpha()
                    img = pygame.transform.smoothscale(img, size)
                    frames.append(img)
                except pygame.error:
                    pass
        return frames

    plane_burst_frames = load_anim_sequence("Explosion_two_colors", "Explosion_two_colors", 10, (160, 160))
    plane_fire_frames  = load_anim_sequence("Fire", "Fire", 6, (110, 110))

    collectible_explosion_types = [
        load_anim_sequence("Circle_explosion", "Circle_explosion", 10, (120, 120)),
        load_anim_sequence("Explosion", "Explosion", 10, (120, 120)),
        load_anim_sequence("Explosion_blue_circle", "Explosion_blue_circle", 10, (120, 120)),
        load_anim_sequence("Explosion_blue_oval", "Explosion_blue_oval", 10, (120, 120)),
        load_anim_sequence("Explosion_gas", "Explosion_gas", 10, (120, 120)),
        load_anim_sequence("Explosion_gas_circle", "Explosion_gas_circle", 10, (120, 120)),
    ]
    collectible_explosion_types = [f for f in collectible_explosion_types if len(f) > 0]

    _ml_path = os.path.join(ASSETS_DIR, "aws cloud club.png")
    if os.path.exists(_ml_path):
        _ml_raw     = pygame.image.load(_ml_path).convert_alpha()
        _ml_w       = 110
        _ml_h       = int(_ml_raw.get_height() * _ml_w / max(1, _ml_raw.get_width()))
        menu_logo   = pygame.transform.smoothscale(_ml_raw, (_ml_w, _ml_h))
    else:
        menu_logo = None


    number_images = []
    for i in range(10):
        p = os.path.join(ASSETS_DIR, "PNG", "Numbers", f"number{i}.png")
        number_images.append(pygame.image.load(p).convert_alpha() if os.path.exists(p) else None)

    bg_raw           = pygame.image.load(os.path.join(ASSETS_DIR, "PNG", "background.png")).convert()
    background_image = pygame.transform.smoothscale(bg_raw, (1200, HEIGHT))
    bg_x = 0.0; ground_x = 0.0

    pipe_top_image = pipe_bottom_image = ground_image = None
    current_theme_name = "grass"

    bird       = Bird()
    pipes      = []
    stars      = []
    puffs      = []   # remove all the particles (plane poop)
    collectible_effects = []
    crash_cx   = 200.0
    crash_cy   = 360.0
    level_gen  = LevelGenerator()

    state            = STATE_MENU
    score            = 0
    time_survived_ms = 0
    base_speed       = 4.2
    current_speed    = base_speed
    typed_text       = ""
    current_word     = ""
    current_meaning  = ""
    quiz_feedback_text  = ""
    quiz_feedback_timer = 0
    invulnerable_timer  = 0
    game_over_timer     = 0
    credits_scroll_y    = 0.0   
    aws_credits         = 0
    max_aws_credits     = 3
    score_multiplier    = 1
    multiplier_timer    = 0
    typing_test_timer   = 0
    wheel_timer         = 0
    wheel_options       = [0.5, 1.25, 1.5, 2.0, 2.5, 3.0, 5.0]
    wheel_duration      = 2500

    MENU_EXIT_MS    = 380        
    menu_exit_surf  = None        
    menu_exit_timer = -1         
    menu_exit_target = None        

    start_button   = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 - 10,  300, 58)
    credits_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 66,  300, 58)
    quiz_modal     = pygame.Rect(WIDTH // 2 - 300, HEIGHT // 2 - 150, 600, 300)
    panel_rect     = pygame.Rect(WIDTH // 2 - 330, HEIGHT // 2 - 180, 660, 360)
    vis_cx         = WIDTH // 2 - 12
    vis_bottom     = panel_rect.bottom - 25
    retry_button   = pygame.Rect(vis_cx - 150, vis_bottom - 110, 300, 52)
    menu_button    = pygame.Rect(vis_cx - 150, vis_bottom - 50,  300, 52)

    def load_theme(theme_name):
        nonlocal pipe_top_image, pipe_bottom_image, ground_image, current_theme_name
        current_theme_name = theme_name
        t = THEMES[theme_name]
        pipe_top_image    = pygame.image.load(os.path.join(ASSETS_DIR, "PNG", t["rock_down"])).convert_alpha()
        pipe_bottom_image = pygame.image.load(os.path.join(ASSETS_DIR, "PNG", t["rock_up"])).convert_alpha()
        ground_image      = pygame.image.load(os.path.join(ASSETS_DIR, "PNG", t["ground"])).convert_alpha()
        bird.set_frames(load_plane_frames(random.choice(PLANE_COLORS)))
        for pipe in pipes: pipe.invalidate_cache()

    def sync_speed():
        for pipe in pipes: pipe.speed = current_speed

    def spawn_pipe():
        cy, gsz = level_gen.next_pipe(score)
        if pipes:
            spacing = random.randint(350, 500)   
            x = int(pipes[-1].x) + spacing
        else:
            x = WIDTH + 60
        pipe = Pipe(x, current_speed, cy, gsz)
        pipes.append(pipe)
        if random.random() < STAR_SPAWN_CHANCE:
            sx_rel, sy = level_gen.star_in_gap(cy, gsz)
            sx = x + sx_rel
            sy = max(pipe.top_height + 10, min(pipe.bottom_y - 50, sy))
            img = random.choice(collectible_images)
            stars.append({"x": float(sx), "rect": pygame.Rect(int(sx), int(sy), 40, 40), "img": img})

    def reset_game(start_state=STATE_PLAYING):
        nonlocal bird, pipes, stars, puffs, score, time_survived_ms, current_speed
        nonlocal typed_text, current_word, current_meaning, state
        nonlocal quiz_feedback_text, quiz_feedback_timer, invulnerable_timer, game_over_timer
        nonlocal credits_scroll_y, aws_credits, score_multiplier, multiplier_timer, typing_test_timer, wheel_timer
        nonlocal collectible_effects, crash_cx, crash_cy
        load_theme(random.choice(list(THEMES.keys())))
        level_gen.reset()
        bird.reset(); pipes = []; stars = []; puffs = []; collectible_effects = []
        score = 0; time_survived_ms = 0; current_speed = base_speed
        typed_text = ""; current_word = ""; current_meaning = ""
        quiz_feedback_text = ""; quiz_feedback_timer = 0
        invulnerable_timer = 0; game_over_timer = 0; credits_scroll_y = 0.0
        aws_credits = 0; score_multiplier = 1; multiplier_timer = 0; typing_test_timer = 0; wheel_timer = 0
        crash_cx = bird.x + bird.width / 2; crash_cy = bird.y + bird.height / 2
        for _ in range(4): spawn_pipe()
        state = start_state

    def start_quiz():
        nonlocal state, typed_text, current_word, current_meaning, typing_test_timer
        q = random.choice(AWS_WORDS)
        current_word = q["word"]; current_meaning = q["meaning"]
        typed_text = ""; state = STATE_QUIZ
        typing_test_timer = 5000 

    def do_game_over():
        nonlocal state, game_over_timer, crash_cx, crash_cy
        state = STATE_GAME_OVER; game_over_timer = 0
        crash_cx = bird.x + bird.width / 2
        crash_cy = bird.y + bird.height / 2

    def do_jump():
        """Jump the bird and emit a puff of exhaust smoke."""
        bird.jump()
        tail_x = bird.x - 10
        tail_y = bird.y + bird.height // 2
        for _ in range(random.randint(1, 2)):
            img_src = random.choice(puff_imgs)
            surf    = img_src.copy()   
            puffs.append({
                "surf":      surf,
                "x":         float(tail_x - surf.get_width() // 2 + random.randint(-6, 6)),
                "y":         float(tail_y - surf.get_height() // 2 + random.randint(-8, 8)),
                "timer":     0,
                "max_timer": random.randint(320, 480),
                "dx":        random.uniform(-1.8, -0.4),   
            })
        if tap_tick_image:
            puffs.append({
                "surf":      pygame.transform.smoothscale(tap_tick_image, (28, 28)),
                "x":         float(tail_x - 14),
                "y":         float(tail_y - 14),
                "timer":     0,
                "max_timer": 320,
                "dx":        random.uniform(-1.2, -0.3),
            })

    def imouse(event): return to_internal(event.pos, get_viewport(window.get_size()))

    reset_game(STATE_MENU)

    while True:
        dt       = clock.tick(FPS)
        viewport = get_viewport(window.get_size())

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.VIDEORESIZE:
                window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                viewport = get_viewport(window.get_size())

            if state == STATE_MENU and menu_exit_timer < 0:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mp = imouse(event)
                    if start_button.collidepoint(mp):
                        menu_exit_surf = canvas.copy()
                        menu_exit_timer = 0
                        menu_exit_target = "start"
                    elif credits_button.collidepoint(mp):
                        menu_exit_surf = canvas.copy()
                        menu_exit_timer = 0
                        menu_exit_target = "credits"
            elif state == STATE_CREDITS:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    state = STATE_MENU
            elif state == STATE_GET_READY:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    do_jump(); state = STATE_PLAYING
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    do_jump(); state = STATE_PLAYING
            elif state == STATE_PLAYING:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE: do_jump()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: do_jump()
            elif state == STATE_QUIZ and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    typed_text = typed_text[:-1]
                elif event.key == pygame.K_RETURN:
                    if typed_text.strip().lower() == current_word:
                        quiz_feedback_text = "CORRECT!"
                        state = STATE_SPIN_WHEEL
                        random.shuffle(wheel_options)
                        wheel_timer = wheel_duration
                    else:
                        quiz_feedback_text = "WRONG!"; invulnerable_timer = 750  
                        quiz_feedback_timer = 1000; state = STATE_PLAYING
                elif event.unicode.isalnum() and len(typed_text) < 20:
                    typed_text += event.unicode
            elif state == STATE_GAME_OVER:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mp = imouse(event)
                    if retry_button.collidepoint(mp): reset_game(STATE_GET_READY)
                    elif menu_button.collidepoint(mp): reset_game(STATE_MENU)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: reset_game(STATE_GET_READY)
                    elif event.key in (pygame.K_ESCAPE, pygame.K_m): reset_game(STATE_MENU)

        scroll = current_speed if state in (STATE_PLAYING, STATE_GET_READY) else 0.0
        if state == STATE_GAME_OVER: game_over_timer += dt
        elif state == STATE_QUIZ:
            typing_test_timer -= dt
            if typing_test_timer <= 0:
                quiz_feedback_text = "TIME'S UP!"
                quiz_feedback_timer = 1000
                invulnerable_timer = 750
                state = STATE_PLAYING
        elif state == STATE_SPIN_WHEEL:
            wheel_timer -= dt
            if wheel_timer <= 0:
                progress    = 1.0
                total_spins = 3 * len(wheel_options)
                final_spin  = (1 - (1 - progress)**3) * total_spins
                final_idx   = int(final_spin) % len(wheel_options)
                score_multiplier = wheel_options[final_idx]
                multiplier_timer = 5000
                invulnerable_timer = 1500
                score += int(10 * score_multiplier)   
                quiz_feedback_text = f"{score_multiplier}x! +{int(10 * score_multiplier)} pts!"
                quiz_feedback_timer = 2000
                state = STATE_PLAYING

        if menu_exit_timer >= 0:
            menu_exit_timer += dt
            if menu_exit_timer >= MENU_EXIT_MS:
                if menu_exit_target == "start":
                    reset_game(STATE_GET_READY)
                elif menu_exit_target == "credits":
                    credits_scroll_y = 0.0; state = STATE_CREDITS
                menu_exit_timer = -1
                menu_exit_surf  = None
                menu_exit_target = None

        bg_x     -= scroll * 0.15
        if bg_x <= -1200: bg_x += 1200
        ground_x -= scroll
        if ground_x <= -808: ground_x += 808

        if state in (STATE_MENU, STATE_GET_READY):
            bird.y = 330 + math.sin(pygame.time.get_ticks() * 0.005) * 15
            bird.rect.topleft = (int(bird.x), int(bird.y))
            if bird.frames:
                bird.animation_counter += 1
                if bird.animation_counter >= 5:
                    bird.animation_counter = 0
                    bird.frame_index = (bird.frame_index + 1) % len(bird.frames)

        elif state == STATE_PLAYING:
            time_survived_ms += dt
            current_speed += 0.075 * (dt / 1000.0)
            sync_speed()
            if invulnerable_timer  > 0: invulnerable_timer  = max(0, invulnerable_timer  - dt)
            if quiz_feedback_timer > 0: quiz_feedback_timer = max(0, quiz_feedback_timer - dt)
            if multiplier_timer > 0:
                multiplier_timer = max(0, multiplier_timer - dt)
                if multiplier_timer == 0:
                    score_multiplier = 1
            bird.update()

            for pipe in pipes:
                pipe.update()
                if not pipe.passed and pipe.right < bird.x:
                    pipe.passed = True; score += 1 * score_multiplier
                    if score % 5 == 0:
                        current_speed += 0.4; sync_speed()
                        tl = list(THEMES.keys())
                        load_theme(tl[(tl.index(current_theme_name)+1) % len(tl)])

            for star in stars[:]:
                star["x"] -= current_speed; star["rect"].x = int(star["x"])
                if bird.rect.colliderect(star["rect"]):
                    if collectible_explosion_types:
                        anim = random.choice(collectible_explosion_types)
                        collectible_effects.append({
                            "x": float(star["rect"].centerx),
                            "y": float(star["rect"].centery),
                            "frames": anim,
                            "timer": 0,
                            "max_timer": 350
                        })
                    stars.remove(star)
                    score += int(1 * score_multiplier)
                    aws_credits += 1
                    if aws_credits >= max_aws_credits:
                        aws_credits = 0; start_quiz()
                    break
                if star["x"] + 40 < 0: stars.remove(star)

            # Update collectible explosion effects
            for fx in collectible_effects[:]:
                fx["timer"] += dt
                fx["x"] -= current_speed
                if fx["timer"] >= fx["max_timer"]:
                    collectible_effects.remove(fx)

            for puff in puffs[:]:
                puff["timer"] += dt
                puff["x"]    += puff["dx"] - current_speed
                if puff["timer"] >= puff["max_timer"]:
                    puffs.remove(puff)

            if pipes and pipes[0].right < -120:
                pipes.pop(0); spawn_pipe()

            if bird.y <= 0 or bird.y + bird.height >= HEIGHT - GROUND_HEIGHT:
                if invulnerable_timer == 0: do_game_over()

            if state == STATE_PLAYING and invulnerable_timer == 0:
                bsurf, bpos = bird.get_draw_info()
                for pipe in pipes:
                    if pipe.collides_with_bird(bsurf, bpos, pipe_top_image, pipe_bottom_image): do_game_over(); break

        # Draw/ bliut
        canvas.blit(background_image, (int(bg_x), 0))
        canvas.blit(background_image, (int(bg_x)+1200, 0))
        canvas.blit(background_image, (int(bg_x)+2400, 0))

        if state in (STATE_PLAYING, STATE_QUIZ, STATE_GAME_OVER, STATE_SPIN_WHEEL):
            for pipe in pipes: pipe.draw(canvas, pipe_top_image, pipe_bottom_image)
            for star in stars:
                img = star.get("img")
                if img:
                    canvas.blit(img, (int(star["rect"].x), int(star["rect"].y)))
                else:
                    pygame.draw.rect(canvas, ORANGE, star["rect"])

            for fx in collectible_effects:
                progress = fx["timer"] / fx["max_timer"]
                idx = int(progress * len(fx["frames"]))
                idx = max(0, min(idx, len(fx["frames"]) - 1))
                img = fx["frames"][idx]
                canvas.blit(img, (int(fx["x"] - img.get_width() / 2), int(fx["y"] - img.get_height() / 2)))

        if ground_image is not None:
            for dx in (0, 808, 1616): canvas.blit(ground_image, (int(ground_x)+dx, HEIGHT-GROUND_HEIGHT))
        else:
            pygame.draw.rect(canvas, GREEN, (0, HEIGHT-GROUND_HEIGHT, WIDTH, GROUND_HEIGHT))

        for puff in puffs:
            alpha = max(0, int(255 * (1 - puff["timer"] / puff["max_timer"])))
            puff["surf"].set_alpha(alpha)
            canvas.blit(puff["surf"], (int(puff["x"]), int(puff["y"])))

        if invulnerable_timer == 0 or (pygame.time.get_ticks()//100)%2==0: bird.draw(canvas)

        if state == STATE_GAME_OVER:
            burst_duration = 450
            if game_over_timer < burst_duration and plane_burst_frames:
                idx = int((game_over_timer / burst_duration) * len(plane_burst_frames))
                idx = min(idx, len(plane_burst_frames) - 1)
                img = plane_burst_frames[idx]
                canvas.blit(img, (int(crash_cx - img.get_width() / 2), int(crash_cy - img.get_height() / 2)))
            elif plane_fire_frames:
                fire_timer = game_over_timer - burst_duration
                idx = int((fire_timer / 100)) % len(plane_fire_frames)
                img = plane_fire_frames[idx]
                canvas.blit(img, (int(crash_cx - img.get_width() / 2), int(crash_cy - img.get_height() + 10)))

        if state == STATE_MENU:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((6,10,25,90)); canvas.blit(ov,(0,0))

            aws_s  = fonts["logo"].render("AWS CLOUD CLUB", True, AWS_ORANGE)
            game_s = fonts["menu_title"].render("AWS fireplane", True, ORANGE)

            logo_h     = menu_logo.get_height() + 12 if menu_logo else 0
            total_h    = logo_h + aws_s.get_height() + 14 + game_s.get_height()
            block_top  = start_button.top - total_h - 24

            if menu_logo:
                canvas.blit(menu_logo, (WIDTH // 2 - menu_logo.get_width() // 2, block_top))
            text_top = block_top + logo_h
            canvas.blit(aws_s,  (WIDTH // 2 - aws_s.get_width()  // 2, text_top))
            canvas.blit(game_s, (WIDTH // 2 - game_s.get_width() // 2, text_top + aws_s.get_height() + 14))

            mp = to_internal(pygame.mouse.get_pos(),viewport) if pygame.mouse.get_focused() else None
            draw_button(canvas, start_button,   "START",   fonts, button_image, mp)
            draw_button(canvas, credits_button, "CREDITS", fonts, button_image, mp)
            footer = fonts["standard"].render("© 2026 Yashwanth K", True, WHITE)
            canvas.blit(footer,(24,HEIGHT-34))

        elif state == STATE_CREDITS:
            
            canvas.fill((0, 0, 0))

            SCROLL_SPEED = 0.9   
            BG_COL       = (0, 0, 0)
            HDR_COL      = (255, 153, 0)
            NAME_COL     = (255, 255, 255) 
            ROLE_COL     = (180, 185, 200) 
            DIVIDER_COL  = (60, 65, 80)

            # credit data 
            # Each item is either:
            #   ("HEADER", "Section Title")       – centred section heading
            #   ("ENTRY",  "Name", "Role")        – two-column name | role
            #   ("SPACER", height)                – vertical gap
            #   ("CENTER", "text", color)         – centred one-liner
            CREDIT_DATA = [
                ("SPACER", 40),
                ("HEADER", "AWS fireplane"),
                ("CENTER", "A Boring and very used idea for a 2D platformer #AWSCloudClub", ROLE_COL),
                ("SPACER", 36),

                ("HEADER", "Developed By"),
                ("ENTRY",  "Yashwanth K",          "Creative Director"),
                ("ENTRY",  "Yashwanth K",          "Game Design"),
                ("ENTRY",  "Michael Jackson",          "Programming"),
                ("ENTRY",  "Yashwanth K",          "Game Systems"),
                ("ENTRY",  "Yashwanth K",          "Level Design"),
                ("ENTRY",  "Yashwanth K",          "UI/UX Design"),
                ("SPACER", 32),

                ("HEADER", "Art & Assets"),
                ("ENTRY",  "Kenney.nl",             "Pixel Art"),
                ("ENTRY",  "Kenney.nl",             "Character Sprites"),
                ("ENTRY",  "Kenney.nl",             "Environment Art"),
                ("ENTRY",  "Kenney.nl",             "Animations"),
                ("ENTRY",  "CRAFTPIX.NET",             "Explosion Animations"),
                ("SPACER", 32),

                ("HEADER", "Special Thanks"),
                ("ENTRY",  "AWS Cloud Club VITC",  "Community & Support"),
                ("SPACER", 32),

                # ("HEADER", "Built With"),
                # ("ENTRY",  "Python 3",             "Language"),
                # ("ENTRY",  "Pygame-CE",            "Game Framework"),
                # ("SPACER", 48),

                ("CENTER", "© 2026 Yashwanth K", ROLE_COL),
                ("CENTER", "All Rights Reserved.", ROLE_COL),
                ("SPACER", 16),
                ("CENTER", "Thank you for playing!", HDR_COL),
                ("SPACER", 80),
            ]

            MID          = WIDTH // 2
            NAME_RIGHT   = MID - 24   
            ROLE_LEFT    = MID + 24   
            ENTRY_H      = 38
            HDR_H        = 54

            # Build content surface (one per state, but simple enough 
            #    to rebuild each frame    no caching needed at 60fps)
            total_h = 0
            for item in CREDIT_DATA:
                if item[0] == "HEADER":
                    total_h += HDR_H + 8
                elif item[0] == "ENTRY":
                    total_h += ENTRY_H
                elif item[0] == "SPACER":
                    total_h += item[1]
                elif item[0] == "CENTER":
                    total_h += ENTRY_H

            content = pygame.Surface((WIDTH, total_h), pygame.SRCALPHA)
            cy = 0

            for item in CREDIT_DATA:
                if item[0] == "HEADER":
                    pygame.draw.line(content, DIVIDER_COL,
                                     (MID - 260, cy + HDR_H // 2 - 1),
                                     (MID + 260, cy + HDR_H // 2 - 1), 1)
                    hdr_s = fonts["subtitle"].render(item[1], True, HDR_COL)
                    bg_pad = 18
                    bg_r = pygame.Rect(MID - hdr_s.get_width()//2 - bg_pad,
                                       cy + HDR_H//2 - hdr_s.get_height()//2 - 2,
                                       hdr_s.get_width() + bg_pad*2, hdr_s.get_height() + 4)
                    pygame.draw.rect(content, BG_COL, bg_r)
                    content.blit(hdr_s, (MID - hdr_s.get_width()//2, cy + HDR_H//2 - hdr_s.get_height()//2))
                    cy += HDR_H + 8

                elif item[0] == "ENTRY":
                    _, name, role = item
                    name_s = fonts["body"].render(name, True, NAME_COL)
                    role_s = fonts["small"].render(role.upper(), True, ROLE_COL)
                    ey = cy + ENTRY_H // 2
                    
                    content.blit(name_s, (NAME_RIGHT - name_s.get_width(),
                                          ey - name_s.get_height() // 2))
                    content.blit(role_s, (ROLE_LEFT,
                                          ey - role_s.get_height() // 2))
                    cy += ENTRY_H

                elif item[0] == "SPACER":
                    cy += item[1]

                elif item[0] == "CENTER":
                    _, text, color = item
                    ts = fonts["small"].render(text, True, color)
                    content.blit(ts, (MID - ts.get_width()//2, cy + ENTRY_H//2 - ts.get_height()//2))
                    cy += ENTRY_H

            credits_scroll_y += SCROLL_SPEED
            if credits_scroll_y >= total_h:
                credits_scroll_y = 0.0

            sy = int(credits_scroll_y)
            SCROLL_TOP    = 72
            SCROLL_BOTTOM = HEIGHT - 34
            view_h = SCROLL_BOTTOM - SCROLL_TOP

            scroll_surf = pygame.Surface((WIDTH, view_h))
            scroll_surf.fill(BG_COL)
            scroll_surf.blit(content, (0, -sy))
            if sy + view_h > total_h:
                scroll_surf.blit(content, (0, total_h - sy))

            FADE_H = 60
            for i in range(FADE_H):
                a_top = int(255 * (1 - i / FADE_H))
                a_bot = int(255 * (i / FADE_H))
                fade_top = pygame.Surface((WIDTH, 1)); fade_top.fill(BG_COL); fade_top.set_alpha(a_top)
                fade_bot = pygame.Surface((WIDTH, 1)); fade_bot.fill(BG_COL); fade_bot.set_alpha(a_bot)
                scroll_surf.blit(fade_top, (0, i))
                scroll_surf.blit(fade_bot, (0, view_h - FADE_H + i))

            canvas.blit(scroll_surf, (0, SCROLL_TOP))

            pygame.draw.rect(canvas, BG_COL, (0, 0, WIDTH, SCROLL_TOP))
            cred_h = fonts["menu_title"].render("CREDITS", True, WHITE)
            canvas.blit(cred_h, (MID - cred_h.get_width() // 2, SCROLL_TOP // 2 - cred_h.get_height() // 2))
            pygame.draw.line(canvas, DIVIDER_COL, (0, SCROLL_TOP - 1), (WIDTH, SCROLL_TOP - 1), 1)

            pygame.draw.rect(canvas, BG_COL, (0, SCROLL_BOTTOM, WIDTH, HEIGHT - SCROLL_BOTTOM))
            hint = fonts["small"].render("Press ESC to return", True, (90, 100, 120))
            canvas.blit(hint, (MID - hint.get_width()//2, SCROLL_BOTTOM + 8))

        elif state == STATE_GET_READY:
            if get_ready_image:
                canvas.blit(get_ready_image, (WIDTH // 2 - get_ready_image.get_width() // 2, HEIGHT // 3 - 50))
            
            ticks = pygame.time.get_ticks()
            pulse = math.sin(ticks * 0.008) * 6
            bounce_y = HEIGHT // 2 + 30 + pulse
            
            # Bottom UI prompt: tap and tapTick pulsing animation
            tap_prompt_frames = [tap_image, tap_tick_image]
            tap_prompt_frames = [f for f in tap_prompt_frames if f is not None]
            if tap_prompt_frames:
                frame_idx = (ticks // 400) % len(tap_prompt_frames)
                curr_img  = tap_prompt_frames[frame_idx]
                sz_w = int(55 + pulse)
                sz_h = int(55 + pulse)
                scaled_tap = pygame.transform.smoothscale(curr_img, (max(10, sz_w), max(10, sz_h)))
                canvas.blit(scaled_tap, (WIDTH // 2 - scaled_tap.get_width() // 2, int(bounce_y - scaled_tap.get_height() // 2)))

        elif state == STATE_PLAYING:
            draw_score(canvas, score, WIDTH//2, 50, number_images)
            bar_w = 300; bar_h = 32
            pygame.draw.rect(canvas, PANEL, (20, 20, bar_w, bar_h), border_radius=16)
            if aws_credits > 0:
                fill_w = int(bar_w * (aws_credits / max_aws_credits))
                pygame.draw.rect(canvas, AWS_ORANGE, (20, 20, fill_w, bar_h), border_radius=16)
            pygame.draw.rect(canvas, WHITE, (20, 20, bar_w, bar_h), width=2, border_radius=16)
            credit_s = fonts["subtitle"].render(f"AWS Credits: {aws_credits}/{max_aws_credits}", True, WHITE)
            canvas.blit(credit_s, (20 + bar_w//2 - credit_s.get_width()//2, 20 + bar_h//2 - credit_s.get_height()//2 + 1))
            
            if score_multiplier != 1:
                mult_s = fonts["subtitle"].render(f"{score_multiplier}x MULTIPLIER! {multiplier_timer//1000}s", True, AWS_ORANGE)
                canvas.blit(mult_s, (20, 55))
            if quiz_feedback_timer > 0:
                col = GREEN if "CORRECT" in quiz_feedback_text or "x!" in quiz_feedback_text else RED
                fb  = fonts["title"].render(quiz_feedback_text,True,col)
                canvas.blit(fb,(WIDTH//2-fb.get_width()//2,HEIGHT//2-50))

        elif state == STATE_QUIZ:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((5,8,16,180)); canvas.blit(ov,(0,0))
            if ui_bg_image: canvas.blit(ui_bg_image,(quiz_modal.centerx-330,quiz_modal.centery-180))
            else: pygame.draw.rect(canvas,PANEL,quiz_modal,border_radius=28)
            t = fonts["subtitle"].render("AWS TYPING TEST",True,AWS_ORANGE)
            canvas.blit(t,(quiz_modal.centerx-t.get_width()//2,quiz_modal.top+20))
            timer_s = fonts["subtitle"].render(f"Time: {max(0, typing_test_timer//1000)}s", True, RED)
            canvas.blit(timer_s,(quiz_modal.right-120,quiz_modal.top+20))
            draw_centered_lines(canvas,wrap_text(f"Type: {current_word.upper()} ({current_meaning})",fonts["subtitle"],quiz_modal.width-60),
                fonts["subtitle"],WHITE,quiz_modal.centerx,quiz_modal.top+74,8)
            ib = pygame.Rect(quiz_modal.left+46,quiz_modal.bottom-104,quiz_modal.width-92,54)
            pygame.draw.rect(canvas,(239,243,255),ib,border_radius=14)
            pygame.draw.rect(canvas,NAVY,ib,width=2,border_radius=14)
            ts = fonts["body"].render(typed_text+"|",True,NAVY)
            canvas.blit(ts,(ib.centerx-ts.get_width()//2,ib.centery-ts.get_height()//2-2))
            pr = fonts["small"].render("Type the word and press ENTER/RETURN",True,PANEL_TEXT)
            canvas.blit(pr,(quiz_modal.centerx-pr.get_width()//2,quiz_modal.bottom-45))

        elif state == STATE_SPIN_WHEEL:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((5,8,16,180)); canvas.blit(ov,(0,0))
            wheel_cx = WIDTH//2; wheel_cy = HEIGHT//2
            
            pygame.draw.rect(canvas, PANEL, (wheel_cx-150, wheel_cy-160, 300, 320), border_radius=20)
            pygame.draw.rect(canvas, NAVY, (wheel_cx-150, wheel_cy-160, 300, 320), width=4, border_radius=20)
            
            title = fonts["subtitle"].render("MULTIPLIER WHEEL", True, AWS_ORANGE)
            canvas.blit(title, (wheel_cx - title.get_width()//2, wheel_cy-130))
            
            progress = 1.0 - (max(0, wheel_timer) / wheel_duration)
            total_spins = 3 * len(wheel_options)
            current_spin = (1 - (1 - progress)**3) * total_spins
            
            box_rect = pygame.Rect(wheel_cx-100, wheel_cy-80, 200, 160)
            pygame.draw.rect(canvas, PANEL_SOFT, box_rect, border_radius=10)
            
            highlight_rect = pygame.Rect(wheel_cx-100, wheel_cy-30, 200, 60)
            pygame.draw.rect(canvas, (40, 60, 100), highlight_rect)
            pygame.draw.rect(canvas, ORANGE, highlight_rect, width=3)
            
            old_clip = canvas.get_clip()
            canvas.set_clip(box_rect)
            
            item_h = 60
            offset_y = (current_spin % 1) * item_h
            base_idx = int(current_spin) % len(wheel_options)
            
            for i in range(-2, 3):
                idx = (base_idx + i) % len(wheel_options)
                val = wheel_options[idx]
                val_text = fonts["title"].render(f"{val}x", True, WHITE)
                y = wheel_cy - val_text.get_height()//2 + offset_y - i * item_h
                canvas.blit(val_text, (wheel_cx - val_text.get_width()//2, y))
                
            canvas.set_clip(old_clip)

        elif state == STATE_GAME_OVER:
            ov = pygame.Surface((WIDTH,HEIGHT),pygame.SRCALPHA); ov.fill((5,8,16,210)); canvas.blit(ov,(0,0))
            # Phase 1: big shrinking text
            t1 = min(game_over_timer, 700)
            ease = 1-(1-t1/700)**3
            big_scale = 3.0-2.0*ease
            big_y = HEIGHT//2-int(140*ease)
            bs = fonts["menu_title"].render("GAME OVER",True,RED)
            sw,sh = int(bs.get_width()*big_scale), int(bs.get_height()*big_scale)
            if sw>0 and sh>0:
                canvas.blit(pygame.transform.smoothscale(bs,(sw,sh)),(WIDTH//2-sw//2,big_y-sh//2))
            # Phase 2: panel + score + buttons
            if game_over_timer >= 800:
                alpha = min(255, int(255*(game_over_timer-800)/300))
                ps = pygame.Surface((panel_rect.width,panel_rect.height),pygame.SRCALPHA)
                if ui_bg_image: ps.blit(ui_bg_image,(0,0))
                else: pygame.draw.rect(ps,PANEL,ps.get_rect(),border_radius=28)
                ps.set_alpha(alpha); canvas.blit(ps,(panel_rect.left,panel_rect.top))
                # Medal
                mf = "UI/medalGold.png" if score>=15 else "UI/medalSilver.png" if score>=8 else "UI/medalBronze.png"
                mi = load_png_image(mf,ORANGE,(70,70))
                if mi: ms2=mi.copy();ms2.set_alpha(alpha);canvas.blit(ms2,(panel_rect.left+28,panel_rect.top+28))
                # Score
                vis_cx = WIDTH // 2 - 12
                sl = fonts["subtitle"].render("SCORE",True,PANEL_TEXT); sl.set_alpha(alpha)
                canvas.blit(sl,(vis_cx-sl.get_width()//2,panel_rect.top+20))
                draw_score(canvas,score,vis_cx,panel_rect.top+50,number_images, dw=38, dh=57)
                tl2 = fonts["subtitle"].render(f"Time: {time_survived_ms/1000:.1f}s",True,PANEL_TEXT); tl2.set_alpha(alpha)
                canvas.blit(tl2,(vis_cx-tl2.get_width()//2,panel_rect.top+118))
                # Buttons — inside the panel
                mp2 = to_internal(pygame.mouse.get_pos(),viewport) if pygame.mouse.get_focused() else None
                draw_button(canvas,retry_button,"RETRY  [R]",fonts,button_image,mp2)
                draw_button(canvas,menu_button,"MAIN MENU  [M]",fonts,button_image,mp2)
                # ht = fonts["small"].render("R = Retry   M = Main Menu",True,PANEL_TEXT); ht.set_alpha(alpha)
                # canvas.blit(ht,(vis_cx-ht.get_width()//2,panel_rect.bottom-35))

        # menu exit slide animation overlay 
        if menu_exit_timer >= 0 and menu_exit_surf is not None:
            progress = min(1.0, menu_exit_timer / MENU_EXIT_MS)
            ease     = 1 - (1 - progress) ** 3   
            half_h   = HEIGHT // 2
            offset   = int(ease * (half_h + 60))
            if menu_exit_target == "start" or menu_exit_target is None:
                canvas.blit(background_image, (int(bg_x), 0))
                canvas.blit(background_image, (int(bg_x) + 1200, 0))
                canvas.blit(background_image, (int(bg_x) + 2400, 0))
            else:
                canvas.fill(BLACK)
            canvas.blit(menu_exit_surf, (0, -offset),
                        pygame.Rect(0, 0, WIDTH, half_h))
            canvas.blit(menu_exit_surf, (0, half_h + offset),
                        pygame.Rect(0, half_h, WIDTH, HEIGHT - half_h))

        _, xo, yo, sw2, sh2 = viewport
        canvas2 = pygame.transform.smoothscale(canvas,(sw2,sh2))
        window.fill(BLACK); window.blit(canvas2,(xo,yo)); pygame.display.flip()


if __name__ == "__main__":
    main()