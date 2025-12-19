import pygame
import sys
import os

pygame.init()

# Screen setup
WIDTH, HEIGHT = 1280, 720
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Apollo Save Tool")

# Paths
images_path = "static/images"
font_path = "static/font/Adonais.ttf"
bg_music_path = os.path.join(images_path, "bg.mp3")

# Column configuration
TARGET_HEIGHT = 150
COLUMN_GAP = 20
COLUMN1_EXTRA_GAP = 50
COLUMN6_EXTRA_GAP = 80

# Per-column offsets and scales
column_offsets = [40, 11, 26, 0, 50, 0, 70]
column_scales = [1.0, 1.0, 1.0, 1.1, 1.0, 1.0, 1.0]

# Jar positioning adjustments
jar_offsets = [1, 1, 1, 1, 1, 1, 1]
jar_scale = 0.8 

# Jar labels
jar_labels = ["Trophies", "USB Saves", "HDD Saves", "Online DB", "Tools", "Settings", "About"]
label_font_size = 36  # bigger text
try:
    label_font = pygame.font.Font(font_path, label_font_size)
except FileNotFoundError:
    label_font = pygame.font.SysFont("Arial", label_font_size)

# Load and scale background images
apollo_img = pygame.image.load(os.path.join(images_path, "apollo.jpg")).convert_alpha()
intro_img = pygame.image.load(os.path.join(images_path, "buk_scr.png")).convert_alpha()

def resize_backgrounds(w, h):
    return pygame.transform.scale(apollo_img, (w, h)), intro_img

apollo_scaled, _ = resize_backgrounds(WIDTH, HEIGHT)

# Intro image scaling
intro_max_width, intro_max_height = 600, 400
iw, ih = intro_img.get_size()
scale_factor = min(intro_max_width / iw, intro_max_height / ih)
intro_scaled = pygame.transform.scale(intro_img, (int(iw * scale_factor), int(ih * scale_factor)))
intro_rect = intro_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2))

# Logo and text images
logo_img = pygame.image.load(os.path.join(images_path, "logo.png")).convert_alpha()
logo_img = pygame.transform.scale(logo_img, (280, 280))
logo_text_img = pygame.image.load(os.path.join(images_path, "logo_text.png")).convert_alpha()
orig_w, orig_h = logo_text_img.get_size()
scale_w = 500
scale_h = int(orig_h * (scale_w / orig_w))
logo_text_img = pygame.transform.scale(logo_text_img, (scale_w, scale_h))

# Credits (sticky bottom-left)
credits_text = "Created by MexrlDev"
try:
    credits_font = pygame.font.Font(font_path, 18)
except FileNotFoundError:
    credits_font = pygame.font.SysFont("Arial", 18)
credits_surface = credits_font.render(credits_text, True, (255, 255, 255))

# Load column images
column_files = [f"column_{i}.png" for i in range(1, 8)]
columns = [pygame.image.load(os.path.join(images_path, filename)).convert_alpha() for filename in column_files]

# Scale columns
scaled_columns = []
for i, col in enumerate(columns):
    w, h = col.get_size()
    scale_w = int(w * (TARGET_HEIGHT / h) * column_scales[i])
    scaled_columns.append(pygame.transform.scale(col, (scale_w, TARGET_HEIGHT)))

# Load jars and hover images
jar_names = ["jar_trophy", "jar_usb", "jar_hdd", "jar_db", "jar_bup", "jar_opt", "jar_about"]
jars, jars_hover = [], []

for name in jar_names:
    base_img = pygame.image.load(os.path.join(images_path, f"{name}.png")).convert_alpha()
    hover_img = pygame.image.load(os.path.join(images_path, f"{name}_hover.png")).convert_alpha()
    bw, bh = base_img.get_size()
    hw, hh = hover_img.get_size()
    jars.append(pygame.transform.scale(base_img, (int(bw * jar_scale), int(bh * jar_scale))))
    jars_hover.append(pygame.transform.scale(hover_img, (int(hw * jar_scale), int(hh * jar_scale))))

# Functions to update positions based on window size
def update_positions(w, h):
    logo_rect = logo_img.get_rect(center=(w // 2, h // 2 - 177))
    logo_text_rect = logo_text_img.get_rect(midtop=(logo_rect.centerx, logo_rect.bottom + 2))
    credits_rect = credits_surface.get_rect(bottomleft=(10, h - 10))
    return logo_rect, logo_text_rect, credits_rect

# Initialize positions
logo_rect, logo_text_rect, credits_rect = update_positions(WIDTH, HEIGHT)

def get_column_positions(w, h, gap=COLUMN_GAP, extra_gap=COLUMN1_EXTRA_GAP, gap6=COLUMN6_EXTRA_GAP):
    total_width = sum(col.get_width() for col in scaled_columns) + gap * (len(scaled_columns) - 1) + (extra_gap - gap) + (gap6 - gap)
    start_x = (w - total_width) // 2
    positions = []
    x = start_x
    for i, col in enumerate(scaled_columns):
        rect = col.get_rect(midbottom=(x + col.get_width() // 2, h))
        rect.y += column_offsets[i]
        positions.append(rect)
        if i == 0:
            x += col.get_width() + extra_gap
        elif i == 5:
            x += col.get_width() + gap6
        else:
            x += col.get_width() + gap
    return positions

column_rects = get_column_positions(WIDTH, HEIGHT)

def get_jar_positions():
    return [
        jars[i].get_rect(midbottom=(column_rects[i].centerx, column_rects[i].top + jar_offsets[i]))
        for i in range(len(jars))
    ]

jar_rects = get_jar_positions()

# Music setup
try:
    pygame.mixer.music.load(bg_music_path)
except pygame.error:
    print("Background music not found.")

clock = pygame.time.Clock()

# States
STATE_INTRO = "intro"
STATE_SHOW_APOLLO = "show_apollo"
STATE_FADE_OUT = "fade_out"
state = STATE_INTRO

# Timing variables
intro_start = None
apollo_start = None
white_overlay_start = None
music_started = False

# Overlay surface for fade effects
overlay = pygame.Surface((WIDTH, HEIGHT)).convert()
overlay.fill((255, 255, 255))

# Fade functions
def fade_in(surface, duration, start_time):
    elapsed = pygame.time.get_ticks() - start_time
    alpha = max(0, 255 - int(255 * (elapsed / duration)))
    surface.set_alpha(alpha)
    return alpha

def fade_out(surface, duration, start_time):
    elapsed = pygame.time.get_ticks() - start_time
    alpha = min(255, int(255 * (elapsed / duration)))
    surface.set_alpha(alpha)
    return alpha

# Main loop
running = True
while running:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(jar_rects):
                if rect.collidepoint(mouse_pos):
                    print(f"Jar {jar_labels[i]} clicked!")
        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
            # Rescale backgrounds
            apollo_scaled, _ = resize_backgrounds(WIDTH, HEIGHT)
            overlay = pygame.Surface((WIDTH, HEIGHT)).convert()
            overlay.fill((255, 255, 255))
            # Update positions
            logo_rect, logo_text_rect, credits_rect = update_positions(WIDTH, HEIGHT)
            column_rects = get_column_positions(WIDTH, HEIGHT)
            jar_rects = get_jar_positions()
            intro_rect = intro_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2))

    # Clear screen
    screen.fill((0, 0, 0))

    if state == STATE_INTRO:
        if intro_start is None:
            intro_start = current_time
        elapsed = current_time - intro_start
        if elapsed < 1000:
            fade_in(intro_scaled, 1000, intro_start)
            screen.blit(intro_scaled, intro_rect)
        elif elapsed < 3100:
            screen.blit(intro_scaled, intro_rect)
        elif elapsed < 4100:
            fade_out(intro_scaled, 1000, intro_start + 2100)
            screen.blit(intro_scaled, intro_rect)
        else:
            state = STATE_SHOW_APOLLO
            apollo_start = current_time

    elif state == STATE_SHOW_APOLLO:
        # Show Apollo background
        screen.blit(apollo_scaled, (0, 0))
        if not music_started:
            try:
                pygame.mixer.music.play(-1)
                music_started = True
            except:
                pass

        # Draw logo and text
        screen.blit(logo_img, logo_rect)
        screen.blit(logo_text_img, logo_text_rect)

        # Draw credits (bottom-left)
        credits_rect = credits_surface.get_rect(bottomleft=(10, HEIGHT - 10))
        screen.blit(credits_surface, credits_rect)

        # Draw columns
        for col, rect in zip(scaled_columns, column_rects):
            screen.blit(col, rect)

        # Draw jars, hover overlays, and labels
        jar_rects = get_jar_positions()
        for i, rect in enumerate(jar_rects):
            screen.blit(jars[i], rect)
            if rect.collidepoint(mouse_pos):
                screen.blit(jars_hover[i], rect)

            # Labels above jars
            label_surface = label_font.render(jar_labels[i], True, (0, 0, 0))
            label_surface.set_alpha(22)  # very faint when idle
            if rect.collidepoint(mouse_pos):
                label_surface.set_alpha(255)  # fully visible on hover
            label_rect = label_surface.get_rect(midbottom=(rect.centerx, rect.top - 5))
            screen.blit(label_surface, label_rect)


        # Transition to fade out
        state = STATE_FADE_OUT

    elif state == STATE_FADE_OUT:
        # Draw static elements
        screen.blit(apollo_scaled, (0, 0))
        screen.blit(logo_img, logo_rect)
        screen.blit(logo_text_img, logo_text_rect)

        # Draw credits
        credits_rect = credits_surface.get_rect(bottomleft=(10, HEIGHT - 10))
        screen.blit(credits_surface, credits_rect)

        # Draw columns
        for col, rect in zip(scaled_columns, column_rects):
            screen.blit(col, rect)

        # Draw jars, hover overlays, and labels
        jar_rects = get_jar_positions()
        for i, rect in enumerate(jar_rects):
            screen.blit(jars[i], rect)
            if rect.collidepoint(mouse_pos):
                screen.blit(jars_hover[i], rect)

            label_surface = label_font.render(jar_labels[i], True, (0, 0, 0))
            label_surface.set_alpha(80)
            if rect.collidepoint(mouse_pos):
                label_surface.set_alpha(255)
            label_rect = label_surface.get_rect(midbottom=(rect.centerx, rect.top - 5))
            screen.blit(label_surface, label_rect)

        # Draw white overlay fading out
        if white_overlay_start is None:
            white_overlay_start = current_time
        elapsed = current_time - white_overlay_start
        alpha = max(0, 255 - int(255 * (elapsed / 5000)))
        overlay.set_alpha(alpha)
        screen.blit(overlay, (0, 0))

    # Update display
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()