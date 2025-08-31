import sys
import time
import random
from math import sin, cos, pi
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Window settings
WINDOW_SIZE = 600
FPS = 60

# Slider settings
SLIDER_WIDTH = 60
SLIDER_HEIGHT = 5
SLIDER_Y = 30
slider_x = (WINDOW_SIZE - SLIDER_WIDTH) // 2
SLIDER_SPEED = 10

# Ball settings
BALL_RADIUS = 6
ball_x = slider_x + SLIDER_WIDTH // 2
ball_y = SLIDER_Y + SLIDER_HEIGHT + BALL_RADIUS
ball_speed = 6
ball_launched = False
ball_dx = 0
ball_dy = 0

# Brick settings (for bottom row)
BRICK_WIDTH = 40
BRICK_HEIGHT = 15
BRICK_Y = 0  # At the very bottom
NUM_BRICKS = WINDOW_SIZE // BRICK_WIDTH

# Main bricks (top) settings
MAIN_BRICK_WIDTH = 40
MAIN_BRICK_HEIGHT = 15
MAIN_BRICK_Y = WINDOW_SIZE - MAIN_BRICK_HEIGHT - 10  # 10 px margin from top
MAIN_BRICK_X_START = 230
MAIN_BRICK_X_END = 600
MAIN_BRICK_SPACING = 0.5

# Input state
move_left = False
move_right = False
mouse_in_window = False

# Bricks dictionary: {level: [brick_dict, ...]}
bricks = {1: []}
score = 0
lives = 6  # Number of lives
game_over = False

def init_main_bricks():
    bricks[1].clear()
    y = 600 - MAIN_BRICK_HEIGHT  # Start from top (600) and go down
    row = 0
    while y >= 230:
        if row % 2 == 0:
            # Even row: full bricks, start at x=0
            x = 0
            while x + MAIN_BRICK_WIDTH <= WINDOW_SIZE:
                brick = {
                    'x': x,
                    'y': y,
                    'width': MAIN_BRICK_WIDTH,
                    'height': MAIN_BRICK_HEIGHT,
                    'alive': True
                }
                bricks[1].append(brick)
                x += MAIN_BRICK_WIDTH
        else:
            # Odd row: half-brick at start, then full bricks, then half-brick at end
            x = 0
            # Left half-brick
            brick = {
                'x': x,
                'y': y,
                'width': MAIN_BRICK_WIDTH // 2,
                'height': MAIN_BRICK_HEIGHT,
                'alive': True
            }
            bricks[1].append(brick)
            x += MAIN_BRICK_WIDTH // 2
            # Full bricks
            while x + MAIN_BRICK_WIDTH <= WINDOW_SIZE - MAIN_BRICK_WIDTH // 2:
                brick = {
                    'x': x,
                    'y': y,
                    'width': MAIN_BRICK_WIDTH,
                    'height': MAIN_BRICK_HEIGHT,
                    'alive': True
                }
                bricks[1].append(brick)
                x += MAIN_BRICK_WIDTH
            # Right half-brick
            brick = {
                'x': x,
                'y': y,
                'width': MAIN_BRICK_WIDTH // 2,
                'height': MAIN_BRICK_HEIGHT,
                'alive': True
            }
            bricks[1].append(brick)
        y -= MAIN_BRICK_HEIGHT
        row += 1

def draw_slider():
    glColor3f(0.2, 0.6, 1.0)
    glBegin(GL_QUADS)
    glVertex2f(slider_x, SLIDER_Y)
    glVertex2f(slider_x + SLIDER_WIDTH, SLIDER_Y)
    glVertex2f(slider_x + SLIDER_WIDTH, SLIDER_Y + SLIDER_HEIGHT)
    glVertex2f(slider_x, SLIDER_Y + SLIDER_HEIGHT)
    glEnd()

def draw_brick(x, y, width, height, spacing, color=(0.75, 0.75, 0.75)):
    glColor3f(*color)
    glBegin(GL_QUADS)
    glVertex2f(x + spacing, y + spacing)
    glVertex2f(x + width - spacing, y + spacing)
    glVertex2f(x + width - spacing, y + height - spacing)
    glVertex2f(x + spacing, y + height - spacing)
    glEnd()

def draw_bricks_row():
    spacing = 0.5  # Space between bricks for the "border" effect

    # --- Bottom row (original) ---
    for i in range(NUM_BRICKS):
        x = i * BRICK_WIDTH + spacing // 2
        y = BRICK_Y
        draw_brick(x, y, BRICK_WIDTH, BRICK_HEIGHT, spacing)

    # --- Top row (centered over gaps, with half-bricks at ends) ---
    top_y = BRICK_Y + BRICK_HEIGHT

    # Left half-brick
    x = spacing // 2
    draw_brick(x, top_y, BRICK_WIDTH // 2, BRICK_HEIGHT, spacing)

    # Middle full bricks
    for i in range(NUM_BRICKS - 1):
        x = (i + 0.5) * BRICK_WIDTH + spacing // 2
        draw_brick(x, top_y, BRICK_WIDTH, BRICK_HEIGHT, spacing)

    # Right half-brick
    x = (NUM_BRICKS - 0.5) * BRICK_WIDTH + spacing // 2
    draw_brick(x, top_y, BRICK_WIDTH // 2, BRICK_HEIGHT, spacing)

def draw_main_bricks():
    color = (0.4, 0.8, 0.4)  # Greenish color for main bricks
    for brick in bricks[1]:
        if not brick['alive']:
            continue
        x, y, w, h = brick['x'], brick['y'], brick['width'], brick['height']
        s = MAIN_BRICK_SPACING
        draw_brick(x, y, w, h, s, color)

def draw_ball():
    glColor3f(1.0, 0.3, 0.3)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(ball_x, ball_y)
    for i in range(32 + 1):
        angle = 2 * pi * i / 32
        glVertex2f(ball_x + cos(angle) * BALL_RADIUS, ball_y + sin(angle) * BALL_RADIUS)
    glEnd()

def draw_heart(cx, cy, size=20, color=(1.0, 0.1, 0.3), segments=128, filled=True):
    """
    Draw a heart centered at (cx, cy).

    Args:
        cx, cy         : center coordinates in screen space (same coordinate system as your GL)
        size           : overall size scale (default 20). Increase to make it larger.
                         (Interpretation: approximate half-width ~ size)
        color          : tuple RGB (0..1)
        segments       : how many samples around curve (higher = smoother)
        filled         : if True draws filled heart (GL_TRIANGLE_FAN), else outline (GL_LINE_LOOP)
    """
    base_half_width = 16.0  # the x-coordinates from the parametric formula reach ~ +/-16
    s = size / base_half_width

    glColor3f(*color)

    if filled:
        glBegin(GL_TRIANGLE_FAN)
        glVertex2f(cx, cy)
        for i in range(segments + 1):
            t = 2 * pi * i / segments
            x = 16 * (sin(t) ** 3)
            y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t)
            glVertex2f(cx + s * x, cy + s * y)
        glEnd()
    else:
        glLineWidth(2.0)
        glBegin(GL_LINE_LOOP)
        for i in range(segments):
            t = 2 * pi * i / segments
            x = 16 * (sin(t) ** 3)
            y = 13 * cos(t) - 5 * cos(2 * t) - 2 * cos(3 * t) - cos(4 * t)
            glVertex2f(cx + s * x, cy + s * y)
        glEnd()

def check_ball_brick_collision():
    global ball_dx, ball_dy, score
    for brick in bricks[1]:
        if not brick['alive']:
            continue

        bx, by, bw, bh = brick['x'], brick['y'], brick['width'], brick['height']

        # Check overlap (with ball radius)
        if (bx - BALL_RADIUS <= ball_x <= bx + bw + BALL_RADIUS and
            by - BALL_RADIUS <= ball_y <= by + bh + BALL_RADIUS):

            brick['alive'] = False
            score += 1

            # Distances to brick sides
            overlap_left   = abs(ball_x - bx)
            overlap_right  = abs(ball_x - (bx + bw))
            overlap_bottom = abs(ball_y - by)
            overlap_top    = abs(ball_y - (by + bh))

            # Find the nearest side → bounce accordingly
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
            if min_overlap == overlap_left or min_overlap == overlap_right:
                ball_dx = -ball_dx
            else:
                ball_dy = -ball_dy
            break

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_bricks_row()
    draw_main_bricks()
    draw_slider()
    draw_ball()
    # Draw score
    glColor3f(1, 1, 1)
    glRasterPos2f(10, WINDOW_SIZE - 20)
    for ch in f"Score: {score}":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    # Draw lives (hearts) LAST so they appear on top
    for i in range(lives):
        cx = 25 + i * 32
        cy = WINDOW_SIZE - 35
        draw_heart(cx, cy, size=16, color=(1.0, 0.1, 0.3), segments=64, filled=True)
    # Game Over message
    if game_over:
        msg = "GAME OVER! Press R to Restart"
        glColor3f(1, 0.2, 0.2)
        glRasterPos2f(WINDOW_SIZE // 2 - 120, WINDOW_SIZE // 2)
        for ch in msg:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    glutSwapBuffers()

def update():
    global slider_x, ball_x, ball_y, ball_launched, ball_dx, ball_dy, lives, game_over
    if game_over:
        glutPostRedisplay()
        time.sleep(1 / FPS)
        return
    # Slider movement
    if move_left:
        slider_x = max(0, slider_x - SLIDER_SPEED)
    if move_right:
        slider_x = min(WINDOW_SIZE - SLIDER_WIDTH, slider_x + SLIDER_SPEED)

    # Ball follows slider if not launched
    if not ball_launched:
        global ball_x, ball_y
        ball_x = slider_x + SLIDER_WIDTH // 2
        ball_y = SLIDER_Y + SLIDER_HEIGHT + BALL_RADIUS
    else:
        # Ball movement
        ball_x += ball_dx
        ball_y += ball_dy

        # Wall collision
        if ball_x - BALL_RADIUS < 0:
            ball_x = BALL_RADIUS
            ball_dx = -ball_dx
        if ball_x + BALL_RADIUS > WINDOW_SIZE:
            ball_x = WINDOW_SIZE - BALL_RADIUS
            ball_dx = -ball_dx
        if ball_y + BALL_RADIUS > WINDOW_SIZE:
            ball_y = WINDOW_SIZE - BALL_RADIUS
            ball_dy = -ball_dy

        # Ball falls below window
        if ball_y - BALL_RADIUS < 0:
            if ball_launched:
                lives -= 1
                if lives <= 0:
                    lives = 0
                    game_over = True
                ball_launched = False

        # Ball collision with slider (paddle-based angle)
        if (
            SLIDER_Y + SLIDER_HEIGHT <= ball_y - BALL_RADIUS <= SLIDER_Y + SLIDER_HEIGHT + abs(ball_dy)
            and slider_x <= ball_x <= slider_x + SLIDER_WIDTH
            and ball_dy < 0
        ):
            hit_pos = (ball_x - slider_x) / SLIDER_WIDTH - 0.5  # -0.5 (left) → 0 (center) → +0.5 (right)
            angle = hit_pos * (pi/3)  # max 60° angle
            speed = (ball_dx**2 + ball_dy**2)**0.5 or ball_speed
            ball_dx = speed * sin(angle)
            ball_dy = abs(speed * cos(angle))  # always go upward
            ball_y = SLIDER_Y + SLIDER_HEIGHT + BALL_RADIUS

    if ball_launched:
        check_ball_brick_collision()

    glutPostRedisplay()
    time.sleep(1 / FPS)

def keyboard(key, x, y):
    global move_left, move_right, ball_launched, ball_dx, ball_dy, game_over, lives, score
    key = key.decode('utf-8').lower()
    if game_over and key == 'r':
        # Restart game
        lives = 6
        score = 0
        game_over = False
        init_main_bricks()
        ball_launched = False
        return
    if key in ['a', '\x1b']:
        move_left = True
    if key in ['d']:
        move_right = True
    if key == ' ' and not ball_launched and not game_over:
        ball_launched = True
        angle = random.uniform(-pi/3, pi/3)
        speed = ball_speed
        ball_dx = speed * sin(angle)
        ball_dy = speed * cos(angle)

def keyboard_up(key, x, y):
    global move_left, move_right
    key = key.decode('utf-8').lower()
    if key in ['a', '\x1b']:
        move_left = False
    if key in ['d']:
        move_right = False

def special_input(key, x, y):
    global move_left, move_right
    if key == GLUT_KEY_LEFT:
        move_left = True
    if key == GLUT_KEY_RIGHT:
        move_right = True

def special_up(key, x, y):
    global move_left, move_right
    if key == GLUT_KEY_LEFT:
        move_left = False
    if key == GLUT_KEY_RIGHT:
        move_right = False

def mouse(button, state, x, y):
    global ball_launched, ball_dx, ball_dy
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not ball_launched:
        ball_launched = True
        # Launch at a random angle between -60° and +60°
        angle = random.uniform(-pi/3, pi/3)
        speed = ball_speed
        ball_dx = speed * sin(angle)
        ball_dy = speed * cos(angle)

def mouse_wheel(wheel, direction, x, y):
    global slider_x
    if direction > 0:
        slider_x = min(WINDOW_SIZE - SLIDER_WIDTH, slider_x + SLIDER_SPEED*2)
    elif direction < 0:
        slider_x = max(0, slider_x - SLIDER_SPEED*2)

def entry(state):
    global mouse_in_window
    mouse_in_window = (state == GLUT_ENTERED)
    # You can use mouse_in_window for any visual effect or logic

def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_SIZE, 0, WINDOW_SIZE)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def main():
    init_main_bricks()
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(WINDOW_SIZE, WINDOW_SIZE)
    glutCreateWindow(b"Tile Breaker")
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glutDisplayFunc(display)
    glutIdleFunc(update)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special_input)
    glutSpecialUpFunc(special_up)
    glutMouseFunc(mouse)
    # Register mouse wheel function (FreeGLUT required)
    try:
        glutMouseWheelFunc(mouse_wheel)
    except AttributeError:
        pass  # If not available, ignore
    glutEntryFunc(entry)
    glutMainLoop()

if __name__ == "__main__":
    main()