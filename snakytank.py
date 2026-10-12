
import tkinter as tk
import random
import time

# =========================
# settings
# =========================
ROWS = 25
COLS = 25
TILE_SIZE = 25

MOVE_INTERVAL = 120       
BULLET_INTERVAL = 30      
BULLET_STEP = 25
FRAME_INTERVAL = 16       

GAME_WIDTH = COLS * TILE_SIZE
GAME_HEIGHT = ROWS * TILE_SIZE

BG_COLOR = "#101820"
GRID_COLOR = "#1b2935"
TANK_COLOR = "#45d483"
TANK_DARK = "#247b50"
BARREL_COLOR = "#cbd5df"
FOOD_COLOR = "#ff4d5a"


# =========================
# classes
# =========================
class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = "Up"


class Bullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.direction = direction


# =========================
# window
# =========================
window = tk.Tk()
window.title("SNACK TANK")
window.resizable(False, False)
window.configure(bg=BG_COLOR)

header = tk.Frame(window, bg="#172532", padx=12, pady=8)
header.pack(fill="x")

title_label = tk.Label(
    header,
    text="SNACK TANK",
    bg="#172532",
    fg="#45d483",
    font=("Arial", 18, "bold")
)
title_label.pack(side="left")

score_label = tk.Label(
    header,
    text="SCORE: 0",
    bg="#172532",
    fg="white",
    font=("Arial", 13, "bold")
)
score_label.pack(side="right")

canvas = tk.Canvas(
    window,
    bg=BG_COLOR,
    width=GAME_WIDTH,
    height=GAME_HEIGHT,
    highlightthickness=0
)
canvas.pack()

footer = tk.Label(
    window,
    text="WASD / ARROWS: MOVE     SPACE: FIRE     R: RESTART",
    bg="#172532",
    fg="#cbd5df",
    font=("Arial", 10),
    padx=8,
    pady=8
)
footer.pack(fill="x")



snake = Tile(5 * TILE_SIZE, 5 * TILE_SIZE)
food = Tile(10 * TILE_SIZE, 10 * TILE_SIZE)

snake_body = []
bullets = []

game_over = False
score = 0
growth_pending = 0

active_key = None
space_held = False

last_move_time = time.monotonic()
last_bullet_time = time.monotonic()


DIRECTIONS = {
    "w": ("Up", 0, -1),
    "up": ("Up", 0, -1),
    "s": ("Down", 0, 1),
    "down": ("Down", 0, 1),
    "a": ("Left", -1, 0),
    "left": ("Left", -1, 0),
    "d": ("Right", 1, 0),
    "right": ("Right", 1, 0),
}



def place_food():
    while True:
        x = random.randrange(COLS) * TILE_SIZE
        y = random.randrange(ROWS) * TILE_SIZE

        if x == snake.x and y == snake.y:
            continue

        if any(t.x == x and t.y == y for t in snake_body):
            continue

        food.x = x
        food.y = y
        return


def grow_tail():
    global growth_pending
    growth_pending += 1


# =========================
# movement
# =========================
def on_key_press(event):
    global active_key, last_move_time, space_held

    key = event.keysym.lower()

    if key == "r":
        restart_game()
        return

    if game_over:
        return

    if key in DIRECTIONS:
        direction, dx, dy = DIRECTIONS[key]


        if active_key != key:
            active_key = key
            snake.direction = direction
            last_move_time = time.monotonic() - MOVE_INTERVAL / 1000

    elif key == "space":
        if not space_held:
            shoot()
            space_held = True


def on_key_release(event):
    global active_key, space_held

    key = event.keysym.lower()


    if key == active_key:
        active_key = None

    if key == "space":
        space_held = False


# =========================
# move tank
# =========================
def move_tank():
    global game_over, score, growth_pending

    if active_key not in DIRECTIONS:
        return

    direction, dx, dy = DIRECTIONS[active_key]
    snake.direction = direction

    old_x = snake.x
    old_y = snake.y

    new_x = old_x + dx * TILE_SIZE
    new_y = old_y + dy * TILE_SIZE

    # wall collision
    if (
        new_x < 0 or new_x >= GAME_WIDTH
        or new_y < 0 or new_y >= GAME_HEIGHT
    ):
        game_over = True
        return


    if growth_pending > 0:
        if snake_body:
            last = snake_body[-1]
            snake_body.append(Tile(last.x, last.y))
        else:
            snake_body.append(Tile(old_x, old_y))

        growth_pending -= 1


    for i in range(len(snake_body) - 1, 0, -1):
        snake_body[i].x = snake_body[i - 1].x
        snake_body[i].y = snake_body[i - 1].y

    if snake_body:
        snake_body[0].x = old_x
        snake_body[0].y = old_y

    snake.x = new_x
    snake.y = new_y


    for tile in snake_body:
        if snake.x == tile.x and snake.y == tile.y:
            game_over = True
            return


    if snake.x == food.x and snake.y == food.y:
        score += 1
        grow_tail()
        place_food()


# =========================
# shooting
# =========================
def shoot():
    x = snake.x + TILE_SIZE // 2
    y = snake.y + TILE_SIZE // 2

    bullets.append(Bullet(x, y, snake.direction))



def segment_hits_tile(x1, y1, x2, y2, tile):
    left = tile.x
    right = tile.x + TILE_SIZE
    top = tile.y
    bottom = tile.y + TILE_SIZE

    if y1 == y2:
        return (
            top <= y1 <= bottom
            and min(x1, x2) <= right
            and max(x1, x2) >= left
        )

    if x1 == x2:
        return (
            left <= x1 <= right
            and min(y1, y2) <= bottom
            and max(y1, y2) >= top
        )

    return False



def move_bullets():
    global game_over, score

    for bullet in bullets[:]:
        old_x = bullet.x
        old_y = bullet.y

        if bullet.direction == "Up":
            bullet.y -= BULLET_STEP
        elif bullet.direction == "Down":
            bullet.y += BULLET_STEP
        elif bullet.direction == "Left":
            bullet.x -= BULLET_STEP
        elif bullet.direction == "Right":
            bullet.x += BULLET_STEP


        if segment_hits_tile(
            old_x, old_y, bullet.x, bullet.y, food
        ):
            bullets.remove(bullet)
            score += 1
            grow_tail()
            place_food()
            continue


        for tile in snake_body:
            if segment_hits_tile(
                old_x, old_y, bullet.x, bullet.y, tile
            ):
                if bullet in bullets:
                    bullets.remove(bullet)

                game_over = True
                return


        if (
            bullet.x < 0 or bullet.x > GAME_WIDTH
            or bullet.y < 0 or bullet.y > GAME_HEIGHT
        ):
            if bullet in bullets:
                bullets.remove(bullet)


# =========================
# draw
# =========================
def draw_grid():
    for x in range(0, GAME_WIDTH, TILE_SIZE):
        canvas.create_line(
            x, 0, x, GAME_HEIGHT,
            fill=GRID_COLOR
        )

    for y in range(0, GAME_HEIGHT, TILE_SIZE):
        canvas.create_line(
            0, y, GAME_WIDTH, y,
            fill=GRID_COLOR
        )


def draw_food():

    canvas.create_oval(
        food.x + 3, food.y + 5,
        food.x + TILE_SIZE - 2, food.y + TILE_SIZE - 1,
        fill="#742b35",
        outline=""
    )


    canvas.create_oval(
        food.x + 4, food.y + 4,
        food.x + TILE_SIZE - 4, food.y + TILE_SIZE - 4,
        fill=FOOD_COLOR,
        outline="#ff9b9b",
        width=2
    )


    canvas.create_line(
        food.x + 13, food.y + 6,
        food.x + 16, food.y + 1,
        fill="#78e08f",
        width=3
    )


def draw_tank():
    x = snake.x
    y = snake.y


    canvas.create_rectangle(
        x + 1, y + 3,
        x + 7, y + TILE_SIZE - 3,
        fill="#243a32",
        outline="#83b89b"
    )
    canvas.create_rectangle(
        x + TILE_SIZE - 7, y + 3,
        x + TILE_SIZE - 1, y + TILE_SIZE - 3,
        fill="#243a32",
        outline="#83b89b"
    )


    for i in range(3):
        yy = y + 7 + i * 6

        canvas.create_line(
            x + 2, yy, x + 6, yy,
            fill="#9aa9a0"
        )
        canvas.create_line(
            x + TILE_SIZE - 6, yy,
            x + TILE_SIZE - 2, yy,
            fill="#9aa9a0"
        )


    canvas.create_rectangle(
        x + 5, y + 5,
        x + TILE_SIZE - 5, y + TILE_SIZE - 5,
        fill=TANK_COLOR,
        outline="#b7ffd6",
        width=2
    )


    if snake.direction == "Up":
        barrel = (
            x + 10, y - 3,
            x + 15, y + 13
        )
    elif snake.direction == "Down":
        barrel = (
            x + 10, y + 12,
            x + 15, y + TILE_SIZE + 3
        )
    elif snake.direction == "Left":
        barrel = (
            x - 3, y + 10,
            x + 13, y + 15
        )
    else:
        barrel = (
            x + 12, y + 10,
            x + TILE_SIZE + 3, y + 15
        )

    canvas.create_rectangle(
        *barrel,
        fill=BARREL_COLOR,
        outline="white",
        width=1
    )


    canvas.create_oval(
        x + 9, y + 9,
        x + TILE_SIZE - 9, y + TILE_SIZE - 9,
        fill=TANK_DARK,
        outline="#d3ffe6"
    )


def draw():
    canvas.delete("all")

    draw_grid()
    draw_food()


    for tile in snake_body:
        canvas.create_rectangle(
            tile.x + 3, tile.y + 3,
            tile.x + TILE_SIZE - 3,
            tile.y + TILE_SIZE - 3,
            fill=TANK_DARK,
            outline=TANK_COLOR,
            width=2
        )

    draw_tank()


    for bullet in bullets:
        canvas.create_oval(
            bullet.x - 4, bullet.y - 4,
            bullet.x + 4, bullet.y + 4,
            fill="#ffe66d",
            outline="#fff9c4",
            width=1
        )

    score_label.config(text=f"SCORE: {score}")

    if game_over:
        canvas.create_rectangle(
            0, 0, GAME_WIDTH, GAME_HEIGHT,
            fill="#080d12",
            stipple="gray50",
            outline=""
        )

        canvas.create_text(
            GAME_WIDTH / 2,
            GAME_HEIGHT / 2 - 30,
            text="GAME OVER",
            fill="#ff5d67",
            font=("Arial", 30, "bold")
        )

        canvas.create_text(
            GAME_WIDTH / 2,
            GAME_HEIGHT / 2 + 15,
            text=f"FINAL SCORE: {score}",
            fill="white",
            font=("Arial", 16, "bold")
        )

        canvas.create_text(
            GAME_WIDTH / 2,
            GAME_HEIGHT / 2 + 50,
            text="Press R to play again",
            fill="#45d483",
            font=("Arial", 13, "bold")
        )


# =========================
# gameloop
# =========================
def game_loop():
    global last_move_time, last_bullet_time

    now = time.monotonic()

    if not game_over:
        if active_key in DIRECTIONS:
            if (now - last_move_time) * 1000 >= MOVE_INTERVAL:
                move_tank()
                last_move_time = now

        if (now - last_bullet_time) * 1000 >= BULLET_INTERVAL:
            move_bullets()
            last_bullet_time = now

    draw()

    window.after(FRAME_INTERVAL, game_loop)


# =========================
# restart
# =========================
def restart_game():
    global snake, food, snake_body, bullets
    global game_over, score, growth_pending
    global active_key, space_held
    global last_move_time, last_bullet_time

    snake = Tile(5 * TILE_SIZE, 5 * TILE_SIZE)
    food = Tile(10 * TILE_SIZE, 10 * TILE_SIZE)

    snake_body = []
    bullets = []

    game_over = False
    score = 0
    growth_pending = 0

    active_key = None
    space_held = False

    last_move_time = time.monotonic()
    last_bullet_time = time.monotonic()

    place_food()
    draw()



window.bind("<KeyPress>", on_key_press)
window.bind("<KeyRelease>", on_key_release)

place_food()
game_loop()

window.mainloop()
