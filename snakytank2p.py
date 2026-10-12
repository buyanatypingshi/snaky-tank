
import tkinter as tk
import random
import time


# =========================
# settings
# =========================

ROWS = 25
COLS = 25
TILE_SIZE = 25

WIDTH = COLS * TILE_SIZE
HEIGHT = ROWS * TILE_SIZE

MOVE_INTERVAL = 120
BULLET_INTERVAL = 16
BULLET_SPEED = 8
FRAME_INTERVAL = 16

BG_COLOR = "#101820"
GRID_COLOR = "#1d2a35"


# =========================
# window
# =========================

window = tk.Tk()
window.title("Snack Tank - 2 Players")
window.resizable(False, False)

score_label = tk.Label(
    window,
    text="",
    font=("Arial", 13, "bold"),
    bg="#101820",
    fg="white",
    pady=8
)
score_label.pack(fill="x")

canvas = tk.Canvas(
    window,
    width=WIDTH,
    height=HEIGHT,
    bg=BG_COLOR,
    highlightthickness=0
)
canvas.pack()

help_label = tk.Label(
    window,
    text="P1: WASD + SPACE     |     P2: ARROWS + ENTER     |     R: RESTART",
    font=("Arial", 9, "bold"),
    bg="#101820",
    fg="#cbd5e1",
    pady=8
)
help_label.pack(fill="x")


# =========================
# tank class
# =========================

class Tank:
    def __init__(self, name, color, head, direction):
        self.name = name
        self.color = color
        self.head = head
        self.direction = direction
        self.tail = []
        self.score = 0
        self.growth_pending = 0
        self.last_move_time = time.monotonic()


# =========================
# arrow class
# =========================

class Bullet:
    def __init__(self, owner, x, y, dx, dy):
        self.owner = owner
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy


# =========================
# players
# =========================

player1 = Tank(
    "1-р тоглогч",
    "#40e060",
    (3, 12),
    (1, 0)
)

player2 = Tank(
    "2-р тоглогч",
    "#40a9ff",
    (21, 12),
    (-1, 0)
)

players = [player1, player2]

bullets = []
food = None

game_over = False
winner = None

last_bullet_time = time.monotonic()

held_keys = set()
held_order = []

P1_KEYS = {
    "w": (0, -1),
    "a": (-1, 0),
    "s": (0, 1),
    "d": (1, 0)
}

P2_KEYS = {
    "up": (0, -1),
    "left": (-1, 0),
    "down": (0, 1),
    "right": (1, 0)
}

SHOOT_KEYS = {
    "space": player1,
    "return": player2
}


# =========================
# food
# =========================

def place_food():
    global food

    occupied = set()

    for tank in players:
        occupied.add(tank.head)
        occupied.update(tank.tail)

    free_cells = [
        (x, y)
        for x in range(COLS)
        for y in range(ROWS)
        if (x, y) not in occupied
    ]

    if not free_cells:
        end_game(None)
        return

    food = random.choice(free_cells)


# =========================
# growing tail
# =========================

def grow_tail(tank):
    tank.growth_pending += 1
    tank.score += 1


# =========================
# gameover
# =========================

def end_game(winning_player):
    global game_over, winner

    if game_over:
        return

    game_over = True
    winner = winning_player


# =========================
# controls 
# =========================

def on_key_press(event):
    key = event.keysym.lower()

    if key == "r":
        restart_game()
        return

    if key not in held_keys:
        held_keys.add(key)
        held_order.append(key)

        if key in SHOOT_KEYS and not game_over:
            shoot(SHOOT_KEYS[key])


def on_key_release(event):
    key = event.keysym.lower()

    held_keys.discard(key)

    if key in held_order:
        held_order.remove(key)


def get_active_direction(tank):
    for key in reversed(held_order):
        if key not in held_keys:
            continue

        if tank is player1 and key in P1_KEYS:
            return P1_KEYS[key]

        if tank is player2 and key in P2_KEYS:
            return P2_KEYS[key]

    return None


# =========================
# movement
# =========================

def move_tank(tank):
    if game_over:
        return

    direction = get_active_direction(tank)

    if direction is None:
        return

    tank.direction = direction

    dx, dy = direction
    x, y = tank.head
    new_head = (x + dx, y + dy)

    nx, ny = new_head

    enemy = player2 if tank is player1 else player1


    if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
        end_game(enemy)
        return


    if new_head == enemy.head:
        end_game(enemy)
        return


    if new_head in enemy.tail:
        end_game(enemy)
        return


    own_tail = tank.tail

    if tank.growth_pending == 0 and own_tail:
        own_tail = own_tail[:-1]

    if new_head in own_tail:
        end_game(enemy)
        return

    ate_food = new_head == food

    if ate_food:
        grow_tail(tank)

    if tank.growth_pending > 0:
        tank.growth_pending -= 1
    elif tank.tail:
        tank.tail.pop()

    tank.tail.insert(0, tank.head)
    tank.head = new_head

    if ate_food:
        place_food()


# =========================
# shoot
# =========================

def shoot(tank):
    if game_over:
        return

    dx, dy = tank.direction

    x = tank.head[0] * TILE_SIZE + TILE_SIZE / 2
    y = tank.head[1] * TILE_SIZE + TILE_SIZE / 2

    bullets.append(
        Bullet(
            tank,
            x + dx * 15,
            y + dy * 15,
            dx,
            dy
        )
    )


# =========================
# arrow collision
# =========================

def move_bullets():
    if game_over:
        return

    for bullet in bullets[:]:
        old_x = bullet.x
        old_y = bullet.y

        bullet.x += bullet.dx * BULLET_SPEED
        bullet.y += bullet.dy * BULLET_SPEED

        if (
            bullet.x < 0
            or bullet.x >= WIDTH
            or bullet.y < 0
            or bullet.y >= HEIGHT
        ):
            bullets.remove(bullet)
            continue


        steps = max(
            1,
            int(max(
                abs(bullet.x - old_x),
                abs(bullet.y - old_y)
            ) / 3)
        )

        hit_cells = set()

        for i in range(steps + 1):
            ratio = i / steps

            px = old_x + (bullet.x - old_x) * ratio
            py = old_y + (bullet.y - old_y) * ratio

            cell = (
                int(px // TILE_SIZE),
                int(py // TILE_SIZE)
            )

            hit_cells.add(cell)


        if food in hit_cells:
            grow_tail(bullet.owner)
            bullets.remove(bullet)
            place_food()

            if game_over:
                return

            continue

        tail_hit = any(
            cell in tank.tail
            for cell in hit_cells
            for tank in players
        )

        if tail_hit:
            enemy = (
                player2 if bullet.owner is player1
                else player1
            )

            end_game(enemy)
            return


        enemy = (
            player2 if bullet.owner is player1
            else player1
        )

        if enemy.head in hit_cells:
            end_game(bullet.owner)
            return


# =========================
# draw
# =========================

def draw_grid():
    for x in range(0, WIDTH, TILE_SIZE):
        canvas.create_line(
            x, 0, x, HEIGHT,
            fill=GRID_COLOR
        )

    for y in range(0, HEIGHT, TILE_SIZE):
        canvas.create_line(
            0, y, WIDTH, y,
            fill=GRID_COLOR
        )


def draw_food():
    if food is None:
        return

    x, y = food

    left = x * TILE_SIZE
    top = y * TILE_SIZE

    canvas.create_oval(
        left + 4,
        top + 4,
        left + TILE_SIZE - 4,
        top + TILE_SIZE - 4,
        fill="#ff4545",
        outline="#ffaaaa",
        width=2
    )


def draw_tank(tank):
    for x, y in tank.tail:
        left = x * TILE_SIZE
        top = y * TILE_SIZE

        canvas.create_rectangle(
            left + 3,
            top + 3,
            left + TILE_SIZE - 3,
            top + TILE_SIZE - 3,
            fill=tank.color,
            outline="#ffffff",
            width=1
        )

        canvas.create_rectangle(
            left + 8,
            top + 8,
            left + TILE_SIZE - 8,
            top + TILE_SIZE - 8,
            fill="#23313c",
            outline=""
        )

    x, y = tank.head

    left = x * TILE_SIZE
    top = y * TILE_SIZE

    canvas.create_rectangle(
        left + 2,
        top + 2,
        left + TILE_SIZE - 2,
        top + TILE_SIZE - 2,
        fill=tank.color,
        outline="white",
        width=1
    )

    canvas.create_rectangle(
        left + 7,
        top + 7,
        left + TILE_SIZE - 7,
        top + TILE_SIZE - 7,
        fill="#23313c",
        outline=""
    )

    cx = left + TILE_SIZE / 2
    cy = top + TILE_SIZE / 2

    dx, dy = tank.direction

    canvas.create_line(
        cx,
        cy,
        cx + dx * 17,
        cy + dy * 17,
        fill=tank.color,
        width=6,
        capstyle=tk.ROUND
    )


def draw_bullets():
    for bullet in bullets:
        canvas.create_oval(
            bullet.x - 4,
            bullet.y - 4,
            bullet.x + 4,
            bullet.y + 4,
            fill="#ffe66d",
            outline="white"
        )


def draw():
    canvas.delete("all")

    draw_grid()
    draw_food()

    for tank in players:
        draw_tank(tank)

    draw_bullets()

    score_label.config(
        text=(
            f"player 1 score: {player1.score} "
            f"       |       "
            f"player 2 score: {player2.score}"
        )
    )

    if game_over:
        if winner is None:
            message = "draw!"
        else:
            message = f"{winner.name} won!"

        canvas.create_rectangle(
            70, 245,
            WIDTH - 70, 380,
            fill="#101820",
            outline="#ffffff",
            width=2
        )

        canvas.create_text(
            WIDTH / 2,
            285,
            text=message,
            fill="#ffe66d",
            font=("Arial", 22, "bold")
        )

        canvas.create_text(
            WIDTH / 2,
            335,
            text="press 'R' to restart",
            fill="white",
            font=("Arial", 13)
        )


# =========================
# gameloop
# =========================

def game_loop():
    global last_bullet_time

    now = time.monotonic()

    if not game_over:
        for tank in players:
            if now - tank.last_move_time >= MOVE_INTERVAL / 1000:
                move_tank(tank)
                tank.last_move_time = now

                if game_over:
                    break

        if (
            not game_over
            and now - last_bullet_time >= BULLET_INTERVAL / 1000
        ):
            move_bullets()
            last_bullet_time = now

    draw()

    window.after(FRAME_INTERVAL, game_loop)


# =========================
# restart
# =========================

def restart_game():
    global player1, player2
    global players, bullets, food
    global game_over, winner
    global last_bullet_time

    player1 = Tank(
        "1-р тоглогч",
        "#40e060",
        (3, 12),
        (1, 0)
    )

    player2 = Tank(
        "2-р тоглогч",
        "#40a9ff",
        (21, 12),
        (-1, 0)
    )

    players = [player1, player2]


    SHOOT_KEYS["space"] = player1
    SHOOT_KEYS["return"] = player2

    bullets = []
    food = None

    game_over = False
    winner = None

    held_keys.clear()
    held_order.clear()

    last_bullet_time = time.monotonic()

    place_food()
    draw()



window.bind("<KeyPress>", on_key_press)
window.bind("<KeyRelease>", on_key_release)

place_food()
game_loop()

window.mainloop()
