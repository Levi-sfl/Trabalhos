import pygame
import math
import random
import sys

pygame.init()

# ==============================
# CONFIGURAÇÕES
# ==============================

WIDTH, HEIGHT = 1000, 650
HALF_H = HEIGHT // 2
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PYTHON DOOM")
clock = pygame.time.Clock()

font = pygame.font.SysFont("consolas", 24, bold=True)
big_font = pygame.font.SysFont("consolas", 55, bold=True)

# ==============================
# MAPA
# ==============================

WORLD = [
    "111111111111",
    "100000001001",
    "100000000001",
    "101000001001",
    "110000001001",
    "101000001001",
    "100000000001",
    "101000010001",
    "101000110001",
    "111111111111",
]

MAP_W = len(WORLD[0])
MAP_H = len(WORLD)

# ==============================
# JOGADOR
# ==============================

px, py = 5.5, 5.5
angle = 0
player_health = 40
ammo = 50
score = 0

FOV = math.pi / 3
NUM_RAYS = 500
MAX_DEPTH = 12
DELTA_ANGLE = FOV / NUM_RAYS
SCALE = WIDTH / NUM_RAYS

# ==============================
# INIMIGOS
# ==============================

enemies = [
    {"x": 8.5, "y": 2.5, "health": 100, "attack": 0},
    {"x": 5.5, "y": 1.5, "health": 100, "attack": 0},
    {"x": 2.5, "y": 6.5, "health": 100, "attack": 0},
    {"x": 6.5, "y": 5.5, "health": 100, "attack": 0},
    {"x": 9.5, "y": 7.5, "health": 100, "attack": 0},
]

# ==============================
# ESTADO
# ==============================

game_state = "menu"
shooting = False
shoot_timer = 0
damage_flash = 0
depth_buffer = []

pygame.mouse.set_visible(True)

# ==============================
# FUNÇÕES
# ==============================

def wall_at(x, y):
    mx, my = int(x), int(y)

    if mx < 0 or my < 0 or mx >= MAP_W or my >= MAP_H:
        return True

    return WORLD[my][mx] == "1"


def move_player(dx, dy):
    global px, py

    if not wall_at(px + dx, py):
        px += dx

    if not wall_at(px, py + dy):
        py += dy




def cast_rays():
    global depth_buffer

    depth_buffer = []

    for ray in range(NUM_RAYS):

        ray_angle = angle - FOV / 2 + ray * DELTA_ANGLE

        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        depth = 0.0

        while depth < MAX_DEPTH:
            depth += 0.01

            x = px + depth * cos_a
            y = py + depth * sin_a

            if wall_at(x, y):
                break

        corrected_depth = depth * math.cos(angle - ray_angle)
        corrected_depth = max(corrected_depth, 0.001)

        depth_buffer.append(corrected_depth)

        wall_height = min(
            HEIGHT,
            int(HEIGHT / corrected_depth)
        )

        brightness = max(
            25,
            min(220, int(220 / (1 + corrected_depth * 0.12)))
        )

        color = (
            brightness,
            brightness // 2,
            brightness // 4
        )

        pygame.draw.rect(
            screen,
            color,
            (
                int(ray * SCALE),
                HALF_H - wall_height // 2,
                math.ceil(SCALE) + 1,
                wall_height
            )
        )




    
def draw_background():
    screen.fill((0, 0, 0))

    # Céu
    pygame.draw.rect(
        screen,
        (65, 85, 115),
        (0, 0, WIDTH, HALF_H)
    )

    # Chão
    pygame.draw.rect(
        screen,
        (90, 65, 45),
        (0, HALF_H, WIDTH, HALF_H)
    )




def draw_enemies():

    # Desenha primeiro os inimigos mais distantes
    visible_enemies = sorted(
        enemies,
        key=lambda e: math.hypot(e["x"] - px, e["y"] - py),
        reverse=True
    )

    for enemy in visible_enemies:

        if enemy["health"] <= 0:
            continue

        dx = enemy["x"] - px
        dy = enemy["y"] - py

        distance = math.hypot(dx, dy)

        if distance < 0.3:
            continue

        enemy_angle = math.atan2(dy, dx)

        difference = (
            enemy_angle - angle + math.pi
        ) % (2 * math.pi) - math.pi

        if abs(difference) > FOV / 2:
            continue

        screen_x = int(
            (0.5 + difference / FOV) * WIDTH
        )

        size = int(HEIGHT / distance * 0.65)

        ray_index = int(screen_x / SCALE)
        ray_index = max(0, min(NUM_RAYS - 1, ray_index))

        # Comparação usando a distância corrigida
        corrected_distance = distance * math.cos(difference)

        if corrected_distance > depth_buffer[ray_index]:
            continue

        rect = pygame.Rect(
            screen_x - size // 3,
            HALF_H - size // 2,
            size * 2 // 3,
            size
        )

        # Corpo
        pygame.draw.rect(
            screen,
            (130, 20, 20),
            rect
        )

        # Cabeça
        pygame.draw.circle(
            screen,
            (170, 40, 30),
            (screen_x, rect.y + size // 5),
            max(3, size // 5)
        )

        # Olhos
        pygame.draw.circle(
            screen,
            (255, 255, 0),
            (screen_x - size // 12, rect.y + size // 5),
            max(2, size // 20)
        )

        pygame.draw.circle(
            screen,
            (255, 255, 0),
            (screen_x + size // 12, rect.y + size // 5),
            max(2, size // 20)
        )



def shoot():
    global ammo, score, shooting, shoot_timer

    if ammo <= 0:
        return

    ammo -= 1
    shooting = True
    shoot_timer = 10

    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        dx = enemy["x"] - px
        dy = enemy["y"] - py

        distance = math.hypot(dx, dy)

        target_angle = math.atan2(dy, dx)

        difference = (
            target_angle - angle + math.pi
        ) % (2 * math.pi) - math.pi

        if abs(difference) < 0.12 and distance < 8:
            enemy["health"] -= 50

            if enemy["health"] <= 0:
                score += 100

            break


def update_enemies(dt):
    global player_health, damage_flash

    for enemy in enemies:
        if enemy["health"] <= 0:
            continue

        dx = px - enemy["x"]
        dy = py - enemy["y"]

        distance = math.hypot(dx, dy)

        if distance > 0.7:
            speed = 0.7 * dt

            mx = dx / distance * speed
            my = dy / distance * speed

            nx = enemy["x"] + mx
            ny = enemy["y"] + my

            if not wall_at(nx, enemy["y"]):
                enemy["x"] = nx

            if not wall_at(enemy["x"], ny):
                enemy["y"] = ny

        else:
            enemy["attack"] += dt

            if enemy["attack"] >= 1:
                player_health -= 10
                enemy["attack"] = 0
                damage_flash = 8


def draw_weapon():
    global shooting, shoot_timer

    weapon_y = HEIGHT - 160

    if shooting:
        weapon_y += 25

        shoot_timer -= 1

        if shoot_timer <= 0:
            shooting = False

    pygame.draw.rect(
        screen,
        (65, 65, 70),
        (WIDTH // 2 - 45, weapon_y, 90, 130)
    )

    pygame.draw.rect(
        screen,
        (25, 25, 30),
        (WIDTH // 2 - 20, weapon_y - 35, 40, 65)
    )

    pygame.draw.rect(
        screen,
        (120, 120, 125),
        (WIDTH // 2 - 15, weapon_y - 35, 30, 50)
    )

    if shooting:
        pygame.draw.circle(
            screen,
            (255, 220, 60),
            (WIDTH // 2, weapon_y - 65),
            35
        )


def draw_hud():
    pygame.draw.rect(
        screen,
        (10, 10, 10),
        (0, HEIGHT - 45, WIDTH, 45)
    )

    text = font.render(
        f"VIDA: {player_health}    "
        f"MUNIÇÃO: {ammo}    "
        f"FRAGS: {score}",
        True,
        (255, 255, 255)
    )

    screen.blit(text, (20, HEIGHT - 38))

    pygame.draw.line(
        screen,
        (255, 255, 255),
        (WIDTH // 2 - 10, HALF_H),
        (WIDTH // 2 + 10, HALF_H),
        2
    )

    pygame.draw.line(
        screen,
        (255, 255, 255),
        (WIDTH // 2, HALF_H - 10),
        (WIDTH // 2, HALF_H + 10),
        2
    )


def draw_menu():
    screen.fill((15, 5, 5))

    title = big_font.render(
        "DOOM 2.0 CLARAMENTE BEM FEITO :D",
        True,
        (220, 30, 20)
    )

    subtitle = font.render(
        "PRESSIONE ENTER PARA JOGAR",
        True,
        (255, 255, 255)
    )

    screen.blit(
        title,
        title.get_rect(center=(WIDTH // 2, 240))
    )

    screen.blit(
        subtitle,
        subtitle.get_rect(center=(WIDTH // 2, 340))
    )


# ==============================
# LOOP PRINCIPAL
# ==============================

while True:
    dt = min(clock.tick(FPS) / 1000, 0.05)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:

            if game_state == "menu":
                if event.key == pygame.K_RETURN:
                    game_state = "playing"
                    pygame.mouse.set_visible(False)
                    pygame.mouse.get_rel()

            elif game_state == "gameover":
                if event.key == pygame.K_RETURN:
                    pygame.quit()
                    sys.exit()

            elif event.key == pygame.K_ESCAPE:
                game_state = "menu"
                pygame.mouse.set_visible(True)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if game_state == "playing" and event.button == 1:
                shoot()

    if game_state == "menu":
        draw_menu()

    elif game_state == "playing":

        keys = pygame.key.get_pressed()

        # Movimento
        speed = 3 * dt

        dx = 0
        dy = 0

        forward = (
            keys[pygame.K_w] - keys[pygame.K_s]
        )

        strafe = (
            keys[pygame.K_d] - keys[pygame.K_a]
        )

        dx = (
            math.cos(angle) * forward
            - math.sin(angle) * strafe
        ) * speed

        dy = (
            math.sin(angle) * forward
            + math.cos(angle) * strafe
        ) * speed

        move_player(dx, dy)

        # Mouse
        move_player(dx, dy)

        # Mouse
        if pygame.mouse.get_focused():
            mx, my = pygame.mouse.get_rel()
            angle += mx * 0.003

        # Renderização
        draw_background()
        cast_rays()
        draw_enemies()
        draw_weapon()
        draw_hud()

        # Renderização
        draw_background()
        cast_rays()
        draw_enemies()
        draw_weapon()
        draw_hud()

        update_enemies(dt)

        if damage_flash > 0:
            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            overlay.fill((255, 0, 0, 55))
            screen.blit(overlay, (0, 0))

            damage_flash -= 1

        if player_health <= 0:
            game_state = "gameover"
            pygame.mouse.set_visible(True)

        if all(e["health"] <= 0 for e in enemies):
            game_state = "victory"
            pygame.mouse.set_visible(True)

    elif game_state == "gameover":
        screen.fill((30, 0, 0))

        title = big_font.render(
            "VOCÊ PERDEU D:",
            True,
            (255, 30, 30)
        )

        subtitle = font.render(
            "PRESSIONE ENTER PARA SAIR",
            True,
            (255, 255, 255)
        )

        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2, 250))
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(center=(WIDTH // 2, 350))
        )

    elif game_state == "victory":
        screen.fill((10, 35, 10))

        title = big_font.render(
            "VOCÊ GANHOU :D!",
            True,
            (50, 255, 80)
        )

        screen.blit(
            title,
            title.get_rect(center=(WIDTH // 2, 270))
        )

    pygame.display.flip()