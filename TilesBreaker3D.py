import sys
import os
import random
import math
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
first_program_dir = os.path.join(current_dir, "First Program")
sys.path.insert(0, first_program_dir)

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

window_width = 1000
window_height = 800

Paddle_width = 100
Paddle_height = 20
Paddle_depth = 30

Ball_radius = 10
Brick_width = 60
Brick_height = 25
Brick_depth = 40

GRID_ROWS = 8
GRID_COLS = 12
POWER_UP_SIZE = 15
PADDLE_MOVE_STEP = 30  

camera_pos = [250,250, 600] 
fovY = 60

scene_rotation_y = 0  # dan bam er ta ektu issue 

class GameState:
    def __init__(self):
        self.paddle_x = 0
        self.paddle_y = -300
        self.paddle_z = 0
        self.Paddle_width = Paddle_width
        
        self.balls = []
        self.bricks = []
        self.power_ups = []
        
        self.lives = 6  # Changed from 3 to 6
        self.score = 0
        self.level = 1
        self.streak = 0
        self.game_over = False
        self.game_won = False
        self.paused = False
        
        self.ball_speed_multiplier = 1.0
        self.paddle_expand_timer = 0
        
        self.reset_level()

    def reset_level(self):
        # Reset ball
        self.balls = [{
            'x': 0,
            'y': -200,
            'z': 0,
            'vel_x': 2 + self.level * 0.5,
            'vel_y': 3 + self.level * 0.3,
            'vel_z': 0
        }]
        
        # so paddle size will reset here, jokhon lagtese
        self.Paddle_width = Paddle_width
        self.ball_speed_multiplier = 1.0
        self.paddle_expand_timer = 0
        
        self.create_bricks()

    def create_bricks(self):
        self.bricks = []
        start_x = -350
        start_y = 100
        
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                x = start_x + col * (Brick_width + 10)
                y = start_y + row * (Brick_height + 10)
                z = -row * 15  
                
                if random.random() < 0.05:
                    continue
                brick_type = 'standard'
                if row < 2: 
                    if random.random() < 0.3 + self.level * 0.05:
                        brick_type = 'strong'
                    elif random.random() < 0.1:
                        brick_type = 'unbreakable'
                elif random.random() < 0.15:
                    brick_type = 'strong'
                
                hits_required = 1 if brick_type == 'standard' else (2 if brick_type == 'strong' else 999)
                
                self.bricks.append({
                    'x': x,
                    'y': y,
                    'z': z, 
                    'type': brick_type,
                    'hits_required': hits_required,
                    'current_hits': 0,
                    'has_power_up': random.random() < 0.2 
                })

game_state = GameState()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    "orthographic projection use kore text draw kora lagbe"
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_cube(x, y, z, width, height, depth, r, g, b):
    "coloured cube , specific position e"
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(r, g, b)
    glScalef(width/60.0, height/60.0, depth/60.0)
    glutSolidCube(60)
    glPopMatrix()

def draw_sphere(x, y, z, radius, r, g, b):
    "ekhane sphere"
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(r, g, b)
    gluSphere(gluNewQuadric(), radius, 10, 10)
    glPopMatrix()

def draw_paddle():
    #paddle ta o cube shape 
    draw_cube(game_state.paddle_x, game_state.paddle_y, 20,
              game_state.Paddle_width, Paddle_height, Paddle_depth, 0.2, 0.8, 1.0)

def draw_balls():
    
    for ball in game_state.balls:
        draw_sphere(ball['x'], ball['y'], ball['z'], Ball_radius, 1.0, 0, 0)

def draw_bricks():
    #based on type brick will have different xolours
    for brick in game_state.bricks:
        if brick['type'] == 'standard':
            r, g, b = 1.0, 0.5, 0.0 
        elif brick['type'] == 'strong':

            if brick['current_hits'] == 0:
                r, g, b = 1.0, 0.0, 0.0  
            else:
                r, g, b = 0.8, 0.2, 0.2  
        else:  
            r, g, b = 0.5, 0.5, 0.5  
            
        draw_cube(brick['x'], brick['y'], brick['z'],
                  Brick_width, Brick_height, Brick_depth, r, g, b)

def draw_power_ups():
    #power up droplets
    for power_up in game_state.power_ups:
        if power_up['type'] == 'expand_paddle':
            r, g, b = 0.0, 1.0, 0.0 
        elif power_up['type'] == 'shrink_paddle':
            r, g, b = 1.0, 0.0, 1.0 
        elif power_up['type'] == 'multi_ball':
            r, g, b = 0.0, 0.0, 1.0 
        elif power_up['type'] == 'speed_up':
            r, g, b = 1.0, 1.0, 0.0  
        elif power_up['type'] == 'slow_down':
            r, g, b = 0.0, 1.0, 1.0 
        else:  
            r, g, b = 1.0, 0.5, 1.0 
            
        draw_sphere(power_up['x'], power_up['y'], power_up['z'], POWER_UP_SIZE, r, g, b)

def draw_walls():
   #3d depth diye boundary create kora
    draw_cube(-450, 0, -50, 20, 600, 200, 0.3, 0.3, 0.3)
    draw_cube(450, 0, -50, 20, 600, 200, 0.3, 0.3, 0.3)
    draw_cube(0, 350, -50, 900, 20, 200, 0.3, 0.3, 0.3)
    draw_cube(0, 0, -150, 900, 700, 20, 0.2, 0.2, 0.2)

def check_ball_paddle_collision(ball):
    "collision check between ball and paddle"
    paddle_left = game_state.paddle_x - game_state.Paddle_width/2
    paddle_right = game_state.paddle_x + game_state.Paddle_width/2
    paddle_top = game_state.paddle_y + Paddle_height/2
    paddle_bottom = game_state.paddle_y - Paddle_height/2
    
    if (ball['x'] + Ball_radius >= paddle_left and 
        ball['x'] - Ball_radius <= paddle_right and
        ball['y'] - Ball_radius <= paddle_top and
        ball['y'] + Ball_radius >= paddle_bottom):
        hit_pos = (ball['x'] - game_state.paddle_x) / (game_state.Paddle_width/2)
        ball['vel_x'] = hit_pos * 3
        ball['vel_y'] = abs(ball['vel_y'])
        ball['y'] = paddle_top + Ball_radius
        return True
    return False

def check_ball_brick_collision(ball):
    "Check collision between ball and bricks"
    for brick in game_state.bricks[:]:
        brick_left = brick['x'] - Brick_width/2
        brick_right = brick['x'] + Brick_width/2
        brick_top = brick['y'] + Brick_height/2
        brick_bottom = brick['y'] - Brick_height/2
        
        if (ball['x'] + Ball_radius >= brick_left and 
            ball['x'] - Ball_radius <= brick_right and
            ball['y'] + Ball_radius >= brick_bottom and
            ball['y'] - Ball_radius <= brick_top):
            
            overlap_left = ball['x'] + Ball_radius - brick_left
            overlap_right = brick_right - (ball['x'] - Ball_radius)
            overlap_top = brick_top - (ball['y'] - Ball_radius)
            overlap_bottom = ball['y'] + Ball_radius - brick_bottom
            
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
            
            if min_overlap == overlap_left or min_overlap == overlap_right:
                ball['vel_x'] = -ball['vel_x']
            else:
                ball['vel_y'] = -ball['vel_y']
            if brick['type'] != 'unbreakable':
                brick['current_hits'] += 1
                if brick['current_hits'] >= brick['hits_required']:
                    if brick['has_power_up']:
                        create_power_up(brick['x'], brick['y'])
                    
                    points = 100 if brick['type'] == 'standard' else 200
                    game_state.score += points + game_state.streak * 10
                    game_state.streak += 1
                    game_state.bricks.remove(brick)
                else:
                    game_state.streak = 0
            else:
                game_state.streak = 0
            
            return True
    return False

def create_power_up(x, y): #ekhane ektu issue ase
    "Create a power-up at specified position"
    power_types = ['expand_paddle', 'shrink_paddle', 'multi_ball', 'speed_up', 'slow_down', 'extra_life']
    power_type = random.choice(power_types)
    
    game_state.power_ups.append({
        'x': x,
        'y': y,
        'z': 0,
        'vel_y': -2,
        'type': power_type
    })

def check_power_up_collection():
    "Check if paddle collects power-ups"
    for power_up in game_state.power_ups[:]:
        paddle_left = game_state.paddle_x - game_state.Paddle_width/2
        paddle_right = game_state.paddle_x + game_state.Paddle_width/2
        paddle_top = game_state.paddle_y + Paddle_height/2
        
        if (power_up['x'] >= paddle_left and power_up['x'] <= paddle_right and
            power_up['y'] <= paddle_top and power_up['y'] >= paddle_top - 30):
            
            apply_power_up(power_up['type'])
            game_state.power_ups.remove(power_up)

def apply_power_up(power_type):
    #"Apply power-up effect"
    if power_type == 'expand_paddle':
        game_state.Paddle_width = min(200, game_state.Paddle_width * 1.5)
        game_state.paddle_expand_timer = 300  # 5 seconds at 60 FPS
    elif power_type == 'shrink_paddle':
        game_state.Paddle_width = max(50, game_state.Paddle_width * 0.7)
        game_state.paddle_expand_timer = 300
    elif power_type == 'multi_ball': #ekhane baraite parbo dorkar e
        if len(game_state.balls) == 1:
            ball = game_state.balls[0]
            for _ in range(2):
                new_ball = ball.copy()
                new_ball['vel_x'] += random.uniform(-1, 1)
                new_ball['vel_y'] += random.uniform(-0.5, 0.5)
                game_state.balls.append(new_ball)
    elif power_type == 'speed_up':
        game_state.ball_speed_multiplier = min(2.0, game_state.ball_speed_multiplier * 1.3)
    elif power_type == 'slow_down':
        game_state.ball_speed_multiplier = max(0.5, game_state.ball_speed_multiplier * 0.7)
    elif power_type == 'extra_life':
        game_state.lives += 1

def update_game():
    ####very important game state update
    if game_state.game_over or game_state.paused:
        return
    if game_state.paddle_expand_timer > 0:
        game_state.paddle_expand_timer -= 1
        if game_state.paddle_expand_timer == 0:
            game_state.Paddle_width = Paddle_width

    for ball in game_state.balls[:]:
        ball['x'] += ball['vel_x'] * game_state.ball_speed_multiplier
        ball['y'] += ball['vel_y'] * game_state.ball_speed_multiplier
        
        
        if ball['x'] <= -430 or ball['x'] >= 430:
            ball['vel_x'] = -ball['vel_x']
        if ball['y'] >= 330:
            ball['vel_y'] = -ball['vel_y']
        
    
        if ball['y'] < -350:
            game_state.balls.remove(ball)
            game_state.streak = 0
            continue
        

        check_ball_paddle_collision(ball)
        check_ball_brick_collision(ball)
    
    for power_up in game_state.power_ups[:]:
        power_up['y'] += power_up['vel_y']
        if power_up['y'] < -350:
            game_state.power_ups.remove(power_up)
    
    check_power_up_collection()
    if not game_state.balls:
        game_state.lives -= 1
        if game_state.lives <= 0:
            game_state.game_over = True
        else:
            game_state.balls = [{
                'x': 0,
                'y': -200,
                'z': 0,
                'vel_x': 2 + game_state.level * 0.5,
                'vel_y': 3 + game_state.level * 0.3,
                'vel_z': 0
            }]
 
    breakable_bricks = [b for b in game_state.bricks if b['type'] != 'unbreakable']
    if not breakable_bricks:
        game_state.level += 1
        if game_state.level > 10:
            game_state.game_won = True
        else:
            game_state.score += 1000 
            game_state.reset_level()

def keyboardListener(key, x, y):
    #keyboard
    global game_state, camera_pos, scene_rotation_y
    if key == b'a' or key == b'A':
        game_state.paddle_x = max(-400, game_state.paddle_x - PADDLE_MOVE_STEP)
    elif key == b'd' or key == b'D':
        game_state.paddle_x = min(400, game_state.paddle_x + PADDLE_MOVE_STEP)
    elif key == b'r' or key == b'R':
        game_state = GameState()
    elif key == b'p' or key == b'P':
        game_state.paused = not game_state.paused
    elif key == b'q' or key == b'Q':  
        glutLeaveMainLoop() 
    elif ord(key) == 27:  
        glutLeaveMainLoop()
    elif key == b'g' or key == b'G':
        camera_pos[2] -= 50
    elif key == b'h' or key == b'H':
        camera_pos[2] += 50
    elif key == b'y' or key == b'Y': 
        camera_pos[1] -= 50
    elif key == b'b' or key == b'B':
        camera_pos[1] += 50
    elif key == b'j' or key == b'J':  # Rotate left
        scene_rotation_y -= 5
    elif key == b'l' or key == b'L':  # Rotate right
        scene_rotation_y += 5


def specialKeyListener(key, x, y):
    #"Handle special keys (arrow keys)"
    global camera_pos
    if key == GLUT_KEY_LEFT:
        game_state.paddle_x = max(-400, game_state.paddle_x - PADDLE_MOVE_STEP)
    elif key == GLUT_KEY_RIGHT:
        game_state.paddle_x = min(400, game_state.paddle_x + PADDLE_MOVE_STEP)
    elif key == GLUT_KEY_UP:
        camera_pos[1] += 20  
    elif key == GLUT_KEY_DOWN:
        camera_pos[1] -= 20 

def mouseListener(button, state, x, y):
    #amra chaile ei ta add korte pare j , mouse diyeo kaj kora gelo, apadoto blank funtion banay rakhsi
    pass

def setupCamera():
     
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, window_width / window_height, 1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], 0, 0, 0, 0, 1, 0)
    glRotatef(scene_rotation_y, 0, 1, 0)  # Rotate scene left/right

TARGET_FPS = 60
FRAME_DURATION = 1.0 / TARGET_FPS
last_frame_time = None  # Will be set in main()

def idle():
    #continous update er jonno idle funtion at fps 60
    global last_frame_time
    if last_frame_time is None:
        last_frame_time = time.time()
    current_time = time.time()
    if current_time - last_frame_time >= FRAME_DURATION:
        update_game()
        glutPostRedisplay()
        last_frame_time = current_time

def draw_heart(x, y, size):
   #important na , heart shape draw
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, window_width, 0, window_height)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glTranslatef(x, y, 0)
    glScalef(size, size, 1)
    glColor3f(1, 0, 0)
    glBegin(GL_POLYGON)
    for angle in range(0, 360, 10):
        rad = math.radians(angle)
        # Heart parametric equation , https://en.wikipedia.org/wiki/Heart#Parametric_equation #booth strap eo ase i guess
        xh = 16 * math.sin(rad) ** 3
        yh = 13 * math.cos(rad) - 5 * math.cos(2 * rad) - 2 * math.cos(3 * rad) - math.cos(4 * rad)
        glVertex2f(xh, yh)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def showScreen():
    ## Main display function ***
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, window_width, window_height)
    
    setupCamera()
    
    if game_state.game_over:
        draw_text(400, 400, "GAME OVER!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(350, 350, f"Final Score: {game_state.score}")
        draw_text(350, 300, "Press R to restart")
    elif game_state.game_won:
        draw_text(350, 400, "CONGRATULATIONS!", GLUT_BITMAP_TIMES_ROMAN_24)
        draw_text(350, 350, "You completed all levels!")
        draw_text(350, 300, f"Final Score: {game_state.score}")
        draw_text(350, 250, "Press R to play again")
    else:
        draw_walls()
        draw_paddle()
        draw_balls()
        draw_bricks()
        draw_power_ups()

        # Draw hearts for lives in the top right corner
        for i in range(game_state.lives):
            draw_heart(window_width - 40 - i * 35, window_height - 40, 1.2)

        draw_text(10, 770, f"Lives: {game_state.lives}")
        draw_text(10, 740, f"Score: {game_state.score}")
        draw_text(10, 710, f"Level: {game_state.level}")
        draw_text(10, 680, f"Streak: {game_state.streak}")
        
        if game_state.paused:
            draw_text(400, 400, "PAUSED", GLUT_BITMAP_TIMES_ROMAN_24)
            draw_text(350, 350, "Press P to continue")
    
        draw_text(780, 70, "Controls:")
        draw_text(780, 50, "A/D or Arrow Keys: Move paddle")
        draw_text(780, 30, "P: Pause, R: Restart")
        draw_text(780, 10, "Q or ESC: Quit, PgUp/Dn: Zoom")
    
    glutSwapBuffers()

def main():
    """Main function"""
    global last_frame_time
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"3D Tiles Breaker Game")
    
    glEnable(GL_DEPTH_TEST)
    
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)

    light_pos = [200, 400, 300, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)

    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

    glClearColor(0.1, 0.1, 0.3, 1.0)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    last_frame_time = time.time()  # Initialize after window setup

    glutMainLoop()

if __name__ == "__main__":
    main()


#Alhamdulillah 