from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
# ==========================================
# GLOBAL STATE
# ==========================================
camera_angle = 0.0
camera_height = 200  
camera_dist = 700

# Dimensions
PITCH_LENGTH = 220 
INFIELD_RADIUS = 300 
BOUNDARY_RADIUS = 550
STUMP_Y_BOWLER = -(PITCH_LENGTH/2 - 10)
STUMP_Y_STRIKER = (PITCH_LENGTH/2 - 10)

# Day/Night State
day_factor = 1.0  
target_day_factor = 1.0
transition_speed = 0.02

# --- GAMEPLAY LOGIC GLOBALS ---
current_state = 0 # 0=Toss, 1=Choice, 2=Playing, 3=Break, 4=Over
game_msg = "TOSS: Press '1' (Heads) or '2' (Tails)"
center_msg = ""
player_role = "BAT" 
innings = 1
balls_bowled = 0
MAX_OVERS = 2
MAX_WICKETS = 5

score = 0
wickets = 0
target_score = 0
team_name = "PLAYER"
overs_txt = "0.0"

# Physics
ball_pos = [0, STUMP_Y_BOWLER, 10]
ball_vel = [0, 0, 0]
ball_moving = False
gravity = -0.18        
ground_friction = 0.96 
ball_hit = False
ball_bounced = False 

# Animation & Movement
is_bat_swinging = False
bat_angle = 0
swing_speed = 0
batsman_x = -8  
umpire_action = 0 
umpire_timer = 0
countdown_active = False
countdown_start_time = 0
cloud_offset = 0 
coin_angle = 0 

# --- FIELDERS ---
fielder_coords = [
    (200, 200), (-200, 300), (300, -100), (-100, -300),
    (0, 480), (0, -480), (150, 50), (-150, 50), (40, 160)
]

# Stars
stars = []
for _ in range(50): 
    sx = random.randint(-1500, 1500); sy = random.randint(200, 1000); sz = random.randint(-1500, 1500)
    stars.append((sx, sy, sz))

# ==========================================
# LIGHTING & PHYSICS
# ==========================================
def get_field_brightness():
    if day_factor < 0.4: return 1.0 
    return max(0.5, day_factor) 

def reset_match():
    global score, wickets, balls_bowled, innings, target_score, current_state, game_msg, overs_txt
    score = 0; wickets = 0; balls_bowled = 0; innings = 1; target_score = 0; overs_txt = "0.0"
    current_state = 0; game_msg = "TOSS: Press '1' (Heads) or '2' (Tails)"; reset_ball()

def reset_ball():
    global ball_pos, ball_vel, ball_moving, is_bat_swinging, bat_angle, countdown_active, center_msg, ball_hit, batsman_x, ball_bounced, swing_speed
    ball_pos = [0, STUMP_Y_BOWLER, 10]; ball_vel = [0, 0, 0]
    ball_moving = False; is_bat_swinging = False; bat_angle = 0
    swing_speed = 0 
    countdown_active = False; center_msg = ""; ball_hit = False
    ball_bounced = False 
    batsman_x = -8 

def declare_outcome(text, runs=0, wicket=False):
    global score, wickets, balls_bowled, game_msg, overs_txt, umpire_action, umpire_timer
    score += runs
    if wicket: 
        wickets += 1; umpire_action = 1; umpire_timer = 150
    elif runs == 4: umpire_action = 2; umpire_timer = 150
    elif runs == 6: umpire_action = 3; umpire_timer = 150
    elif runs == 1: umpire_action = 0; umpire_timer = 0 

    balls_bowled += 1; overs_txt = f"{balls_bowled//6}.{balls_bowled%6}"
    game_msg = text; reset_ball(); check_game_status()

def check_game_status():
    global innings, target_score, balls_bowled, current_state, game_msg, player_role, score, wickets, team_name
    
    if innings == 2 and score >= target_score:
        winner = team_name if player_role == "BAT" else "CPU"
        game_msg = f"{winner} WINS! Press 'r' to Restart."; current_state = 4; return

    if balls_bowled >= MAX_OVERS * 6 or wickets >= MAX_WICKETS:
        if innings == 1:
            innings = 2; target_score = score + 1; score = 0; wickets = 0; balls_bowled = 0; overs_txt = "0.0"
            player_role = "BOWL" if player_role == "BAT" else "BAT"
            team_name = "PLAYER" if player_role == "BAT" else "CPU"
            game_msg = f"Innings Break! Target: {target_score}. Press 'p' to start."; current_state = 3
        else:
            if score == target_score - 1: game_msg = "MATCH TIED! Press 'r' to Restart."
            else:
                winner = "CPU" if player_role == "BAT" else "PLAYER"
                game_msg = f"{winner} WINS! Press 'r' to Restart."
            current_state = 4

def update_physics():
    global ball_pos, ball_vel, ball_moving, is_bat_swinging, bat_angle, swing_speed, umpire_timer, umpire_action, ball_bounced
    global center_msg, countdown_active, countdown_start_time, ball_hit, cloud_offset, coin_angle

    if current_state == 0: coin_angle = (coin_angle + 2) % 360

    if umpire_timer > 0:
        umpire_timer -= 1
        if umpire_timer == 0: umpire_action = 0

    cloud_offset += 0.5
    if cloud_offset > 1200: cloud_offset = -1200

    if countdown_active:
        elapsed = time.time() - countdown_start_time
        if elapsed < 1: center_msg = "3"
        elif elapsed < 2: center_msg = "2"
        elif elapsed < 3: center_msg = "1"
        else:
            countdown_active = False; ball_moving = True
            ball_vel = [random.uniform(-0.6, 0.6), 4.2, random.uniform(2.5, 3.5)]

#  BAT LOGIC ---
    if is_bat_swinging:
        bat_angle += swing_speed
        if bat_angle < -60: swing_speed = 12
        if bat_angle > 80: 
            is_bat_swinging = False
            bat_angle = 0
            swing_speed = 0 
            
    if ball_moving:
        ball_pos[0]+=ball_vel[0]; ball_pos[1]+=ball_vel[1]; ball_pos[2]+=ball_vel[2]
        if ball_pos[2] > 0: ball_vel[2] += gravity
        
        if ball_pos[2] <= 0:
            ball_pos[2] = 0
            ball_vel[2] = -ball_vel[2] * 0.7
            ball_vel[1] *= ground_friction
            ball_bounced = True 
            
        if abs(ball_pos[1] - STUMP_Y_STRIKER) < 18 and ball_pos[2] < 25:
            if abs(ball_pos[0] - batsman_x) < 15: 
                if player_role == "BAT" and swing_speed > 0 and -25 < bat_angle < 65:
                    ball_vel[1] *= -1.6; ball_vel[2] = 7; ball_vel[0] = random.uniform(-12, 12); ball_hit = True
                elif player_role == "BOWL" and random.random() < 0.1: 
                    ball_vel[1] *= -1.4; ball_vel[2] = 8; ball_vel[0] = random.uniform(-10, 10); ball_hit = True

        if not ball_hit and abs(ball_pos[1] - STUMP_Y_STRIKER) < 5 and abs(ball_pos[0]) < 4 and ball_pos[2] < 28:
            ball_moving = False; declare_outcome("BOWLED!", 0, True); return

        if not ball_hit and ball_pos[1] > STUMP_Y_STRIKER + 20:
            ball_moving = False; declare_outcome("Dot Ball (Keeper)", 0, False); return

        dist = math.sqrt(ball_pos[0]**2 + ball_pos[1]**2)
        if dist > BOUNDARY_RADIUS:
            ball_moving = False
            if ball_bounced: declare_outcome("FOUR!", 4, False)
            else: declare_outcome("SIX!", 6, False)
            return
        
        if ball_hit and not ball_bounced and ball_pos[2] > 5: 
            for fx, fy in fielder_coords:
                if abs(ball_pos[0]-fx) < 22 and abs(ball_pos[1]-fy) < 22:
                    ball_moving = False; declare_outcome("CAUGHT OUT!", 0, True); return
        
        if abs(ball_vel[1]) < 0.1 and ball_pos[2] == 0: 
            ball_moving = False
            if ball_hit:
                dist_from_stumps = math.sqrt(ball_pos[0]**2 + (ball_pos[1]-STUMP_Y_STRIKER)**2)
                if dist_from_stumps > 40:
                    declare_outcome("1 Run", 1, False)
                else:
                    declare_outcome("Defended", 0, False)
            else:
                declare_outcome("Dot Ball", 0, False)
            return

# ==========================================
# DRAWING
# ==========================================
def draw_text_bitmap(x, y, z, text):
    glColor3f(1, 1, 1)
    glRasterPos3f(x, y, z)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

def draw_text_hud(x, y, text, large=False):
    glColor3f(1, 1, 1); glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    w = glutGet(GLUT_WINDOW_WIDTH); h = glutGet(GLUT_WINDOW_HEIGHT)
    if w==0:w=1; 
    if h==0:h=1
    gluOrtho2D(0, w, 0, h); glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f((x/1000)*w, (y/800)*h)
    font = GLUT_BITMAP_TIMES_ROMAN_24 if large else GLUT_BITMAP_HELVETICA_18
    for ch in text:
        try: glutBitmapCharacter(font, ord(ch))
        except: pass
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_cylinder(radius, height, r, g, b):
    glColor3f(r, g, b); q = gluNewQuadric(); gluCylinder(q, radius, radius, height, 10, 10)

def draw_filled_circle(x, y, z, radius, r, g, b):
    glColor3f(r, g, b); glBegin(GL_TRIANGLE_FAN); glVertex3f(x, y, z) 
    for i in range(0, 361, 5): rad=math.radians(i); glVertex3f(x+math.cos(rad)*radius, y+math.sin(rad)*radius, z)
    glEnd()

# --- SCENE ---
def draw_pitch_realistic():
    light = get_field_brightness()
    glBegin(GL_QUADS); glColor3f(0.82 * light, 0.70 * light, 0.55 * light) 
    z_h = 0.5; h_l = PITCH_LENGTH / 2; h_w = 30 
    glVertex3f(-h_w, h_l, z_h); glVertex3f(h_w, h_l, z_h); glVertex3f(h_w, -h_l, z_h); glVertex3f(-h_w, -h_l, z_h); glEnd()
    glColor3f(1 * light, 1 * light, 1 * light); line_z = z_h + 0.1
    for end in [1, -1]:
        stump_y = STUMP_Y_STRIKER * end
        glBegin(GL_QUADS); glVertex3f(-h_w, stump_y + 1, line_z); glVertex3f(h_w, stump_y + 1, line_z); glVertex3f(h_w, stump_y - 1, line_z); glVertex3f(-h_w, stump_y - 1, line_z); glEnd()
        glBegin(GL_QUADS); glVertex3f(-h_w - 15, stump_y-25, line_z); glVertex3f(h_w + 15, stump_y-25, line_z); glVertex3f(h_w + 15, stump_y-27, line_z); glVertex3f(-h_w - 15, stump_y-27, line_z); glEnd()

def draw_stadium_structure():
    f_light = get_field_brightness(); s_light = 0.6 if day_factor < 0.4 else max(0.4, day_factor)
    draw_filled_circle(0, 0, -2.0, 4000, 0.05, 0.25, 0.05) 
    draw_filled_circle(0, 0, -1.0, BOUNDARY_RADIUS, 0.1*f_light, 0.6*f_light, 0.1*f_light)
    draw_filled_circle(0, 0, -0.5, INFIELD_RADIUS, 0.15*f_light, 0.7*f_light, 0.15*f_light)
    radius_stands = BOUNDARY_RADIUS + 120 
    glColor3f(1*f_light, 1*f_light, 1*f_light)
    for angle in range(0, 360, 10): 
        if (85 < angle < 95) or (265 < angle < 275): continue
        rad=math.radians(angle); x=math.cos(rad)*radius_stands; y=math.sin(rad)*radius_stands
        glPushMatrix(); glTranslatef(x,y,0); glRotatef(angle+90,0,0,1) 
        for tier in range(3):
            c=(0.5+tier*0.1)*s_light; glColor3f(c,c,c); glPushMatrix(); glTranslatef(0,tier*20,tier*25); glScalef(15,2,2); glutSolidCube(40); glPopMatrix()
        glPopMatrix()
    for direction in [1, -1]:
        glPushMatrix(); glTranslatef(0, direction*(BOUNDARY_RADIUS+140), 40)
        glColor3f(0.95*s_light, 0.95*s_light, 0.95*s_light); glScalef(80, 2, 80); glutSolidCube(1); glPopMatrix()

def draw_environment_extras():
    if day_factor > 0.5:
        glPushMatrix(); glTranslatef(-500, 800, 500); glColor3f(1.0, 1.0, 0.0); gluSphere(gluNewQuadric(), 60, 20, 20); glPopMatrix() 
        glPushMatrix(); glTranslatef(cloud_offset, 0, 0); glColor3f(0.95, 0.95, 0.95)
        for cx, cy, cz in [(-300, 700, 400), (-100, 750, 450), (-400, 720, 380)]:
            glPushMatrix(); glTranslatef(cx, cy, cz); gluSphere(gluNewQuadric(), 30, 10, 10)
            glTranslatef(25, 0, 0); gluSphere(gluNewQuadric(), 25, 10, 10); glPopMatrix()
        glPopMatrix()
    else:
        glPushMatrix(); glTranslatef(-500, 800, 500); glColor3f(0.9, 0.9, 0.9); gluSphere(gluNewQuadric(), 40, 20, 20); glPopMatrix()
        glPointSize(2.0); glBegin(GL_POINTS); glColor3f(1, 1, 1); [glVertex3f(sx,sy,sz) for (sx,sy,sz) in stars]; glEnd()
    glColor3f(1.0, 0.0, 0.0) 
    for i in range(0, 360, 2):
        glPushMatrix(); rad = math.radians(i); x = math.cos(rad) * BOUNDARY_RADIUS; y = math.sin(rad) * BOUNDARY_RADIUS
        glTranslatef(x, y, 6); glRotatef(i, 0, 0, 1); glScalef(2.0, 4.5, 2.0); glutSolidCube(5); glPopMatrix()
    board_dist = BOUNDARY_RADIUS + 40
    for angle in range(0, 360, 15): 
        glPushMatrix(); rad = math.radians(angle); x = math.cos(rad) * board_dist; y = math.sin(rad) * board_dist
        glTranslatef(x, y, 15); glRotatef(angle, 0, 0, 1) 
        idx = (angle // 15) % 4
        if idx == 0: glColor3f(1, 0.8, 0) 
        elif idx == 1: glColor3f(0, 1, 1) 
        elif idx == 2: glColor3f(1, 0, 1) 
        elif idx == 3: glColor3f(0.2, 1, 0.2) 
        glScalef(2, 70, 30); glutSolidCube(1); glPopMatrix()
    for angle in range(0, 360, 20):
        rad = math.radians(angle); tx = math.cos(rad) * 900; ty = math.sin(rad) * 900
        draw_tree(tx, ty)

def draw_creative_scoreboard():
    board_x = -BOUNDARY_RADIUS - 60; board_width = 400; board_height = 150; elevation = 100 
    glPushMatrix(); glTranslatef(board_x, -120, 0); draw_cylinder(10, elevation+board_height/2, 0.4, 0.4, 0.45); glPopMatrix()
    glPushMatrix(); glTranslatef(board_x, 120, 0); draw_cylinder(10, elevation+board_height/2, 0.4, 0.4, 0.45); glPopMatrix()
    glPushMatrix(); glTranslatef(board_x, 0, elevation + board_height/2 - 20)
    glColor3f(0.3, 0.3, 0.35); glScalef(10, board_width + 20, board_height + 20); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(board_x + 6, 0, elevation + board_height/2 - 20)
    glColor3f(0.05, 0.05, 0.05); glScalef(5, board_width, board_height); glutSolidCube(1); glPopMatrix()
    
    draw_text_bitmap(board_x + 25, -40, elevation + 75 + 20, f"{team_name} {score}/{wickets}")
    draw_text_bitmap(board_x + 25, -40, elevation + 75 - 20, f"OVERS: {overs_txt}")
    draw_text_bitmap(board_x + 25, -40, elevation + 75 - 60, f"TARGET: {target_score}")

def draw_floodlight(x, y):
    glPushMatrix(); glTranslatef(x, y, 0); draw_cylinder(6, 180, 0.6, 0.6, 0.6)
    glTranslatef(0, 0, 180); glRotatef(-45, 0, 1, 0); glColor3f(0.2, 0.2, 0.2); glScalef(1, 0.2, 1); glutSolidCube(60)
    if day_factor < 0.5: glColor3f(1, 1, 1)
    else: glColor3f(0.3, 0.3, 0.3)
    for i in range(-20, 25, 12):
        for j in range(-20, 25, 12): glPushMatrix(); glTranslatef(i, 10, j); gluSphere(gluNewQuadric(), 4, 6, 6); glPopMatrix()
    glPopMatrix()

def draw_person(x, y, z, r, g, b, has_bat=False, is_umpire=False, swing=False):
    glPushMatrix(); glTranslatef(x, y, z); light = get_field_brightness()
    glColor3f(0.85*light, 0.75*light, 0.65*light); glPushMatrix(); glTranslatef(0, 0, 26); gluSphere(gluNewQuadric(), 5, 8, 8); glPopMatrix()
    glColor3f(r*light, g*light, b*light); glPushMatrix(); glTranslatef(0, 0, 15); glScalef(0.4, 0.25, 0.75); glutSolidCube(25); glPopMatrix()
    glColor3f(1*light, 1*light, 1*light); 
    for lx in [-4, 4]: 
        glPushMatrix(); glTranslatef(lx, 0, 5); glScalef(0.15, 0.2, 0.8); glutSolidCube(25); glPopMatrix()
    
    if is_umpire:
        if umpire_action == 1: glPushMatrix(); glTranslatef(8,0,25); glScalef(2,2,10); glColor3f(0,0,0); glutSolidCube(1); glPopMatrix()
        elif umpire_action == 2: glPushMatrix(); glTranslatef(15,0,15); glScalef(20,2,2); glColor3f(0,0,0); glutSolidCube(1); glPopMatrix()
        elif umpire_action == 3: glPushMatrix(); glTranslatef(8,0,25); glScalef(2,2,10); glColor3f(0,0,0); glutSolidCube(1); glPopMatrix(); glPushMatrix(); glTranslatef(-8,0,25); glScalef(2,2,10); glColor3f(1,1,1); glutSolidCube(1); glPopMatrix()
    elif has_bat:
        # --- FIXED BAT POSITION & COLOR ---
        angle = bat_angle if swing else 0
        glPushMatrix()
        glTranslatef(0, -10, 22) # Pivot at Hands
        glRotatef(angle - 20, 1, 0, 0)
        glTranslatef(0, 0, -8) # Hang down
        glColor3f(0, 0, 0) # White Bat
        glScalef(1.8, 0.4, 9.0)
        glutSolidCube(2)
        glPopMatrix()
    glPopMatrix()

def draw_stumps(x, y, z):
    glPushMatrix(); glTranslatef(x, y, z); col = (0.7, 0.5, 0.2)
    for ix in [-3, 0, 3]: glPushMatrix(); glTranslatef(ix, 0, 0); draw_cylinder(1.2, 28, *col); glPopMatrix()
    glPopMatrix()

def draw_tree(x, y):
    glPushMatrix(); glTranslatef(x, y, 0); draw_cylinder(15, 60, 0.4, 0.2, 0.0) 
    glTranslatef(0, 0, 40); glColor3f(0.0, 0.5, 0.0)
    gluCylinder(gluNewQuadric(), 40, 0, 100, 10, 10) 
    glPopMatrix()

def draw_toss_menu():
    glDisable(GL_LIGHTING); glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800); glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS); glVertex2f(200, 200); glVertex2f(800, 200); glVertex2f(800, 600); glVertex2f(200, 600); glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    
    glPushMatrix(); cx = camera_dist*math.sin(math.radians(camera_angle)); cy = -camera_dist*math.cos(math.radians(camera_angle))
    glTranslatef(0, 0, 150); glRotatef(coin_angle, 0, 1, 0); glRotatef(90, 1, 0, 0)
    # Coin edge
    glColor3f(1.0, 0.84, 0.0); gluCylinder(gluNewQuadric(), 40, 40, 10, 20, 1)
    # Coin Face 1 (Flattened sphere)
    glPushMatrix(); glScalef(1, 1, 0.1); gluSphere(gluNewQuadric(), 40, 20, 20); glPopMatrix()
    # Coin Face 2
    glTranslatef(0,0,10); glPushMatrix(); glScalef(1, 1, 0.1); gluSphere(gluNewQuadric(), 40, 20, 20); glPopMatrix(); glPopMatrix()

    if current_state == 0:
        draw_text_hud(330, 550, "--- TOSS TIME ---", large=True)
        draw_text_hud(400, 450, "HEADS (1)", large=True)
        draw_text_hud(400, 350, "TAILS (2)", large=True)
    elif current_state == 1:
        draw_text_hud(330, 550, "YOU WON THE TOSS!", large=True)
        draw_text_hud(300, 450, "Press '1' to BAT", large=True)
        draw_text_hud(300, 350, "Press '2' to BOWL", large=True)

# ==========================================
# SYSTEM
# ==========================================
def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    sky = 0.05 + (0.8 * day_factor); glClearColor(0.05, 0.05, sky, 1); glLoadIdentity()
    w = glutGet(GLUT_WINDOW_WIDTH); h = glutGet(GLUT_WINDOW_HEIGHT); glViewport(0, 0, w, h)
    gluPerspective(60, w/h, 0.1, 4000); gluLookAt(camera_dist*math.sin(math.radians(camera_angle)), -camera_dist*math.cos(math.radians(camera_angle)), camera_height, 0, 0, 0, 0, 0, 1)
    
    draw_pitch_realistic(); draw_stadium_structure(); draw_creative_scoreboard()
    fl = BOUNDARY_RADIUS+100; [draw_floodlight(fx, fy) for fx, fy in [(fl,fl),(-fl,fl),(fl,-fl),(-fl,-fl)]]
    draw_environment_extras()
    draw_stumps(0, STUMP_Y_STRIKER, 0); draw_stumps(0, STUMP_Y_BOWLER, 0)
    
    # --- DYNAMIC TEAM COLORS ---
    if player_role == "BAT":
        # User is batting: User=Red, CPU=Blue
        br, bg, bb = 0.9, 0.1, 0.1 # Red Batsman
        fr, fg, fb = 0.0, 0.4, 0.8 # Blue Fielders
    else:
        # User is bowling: User=Red(Fielding), CPU=Blue(Batting)
        br, bg, bb = 0.0, 0.4, 0.8 # Blue Batsman
        fr, fg, fb = 0.9, 0.1, 0.1 # Red Fielders

    draw_person(batsman_x, STUMP_Y_STRIKER, 0, br, bg, bb, has_bat=True, swing=True) 
    
    
    draw_person(20, STUMP_Y_BOWLER, 0, br, bg, bb, has_bat=True, swing=False) 
    
    draw_person(-10, STUMP_Y_BOWLER - 50, 0, fr, fg, fb) 
    draw_person(-5, STUMP_Y_STRIKER + 40, 0, fr, fg, fb) 
    draw_person(0, STUMP_Y_BOWLER - 30, 0, 0.2, 0.2, 0.2, is_umpire=True) 
    for fx, fy in fielder_coords: draw_person(fx, fy, 0, fr, fg, fb) 
    glPushMatrix(); glTranslatef(ball_pos[0], ball_pos[1], ball_pos[2]); glColor3f(1,1,1); gluSphere(gluNewQuadric(), 3.5, 12, 12); glPopMatrix()
    
    if current_state >= 2:
        draw_text_hud(10, 770, game_msg)
        if center_msg: draw_text_hud(480, 400, center_msg, large=True)
    else:
        draw_toss_menu()
    glutSwapBuffers()

def keyboardListener(key, x, y):
    global current_state, player_role, ball_moving, ball_vel, is_bat_swinging, swing_speed, countdown_active, countdown_start_time, target_day_factor, team_name, game_msg, batsman_x
    
    if current_state == 0:
        bet = None
        if key == b'1': bet = "HEADS"
        elif key == b'2': bet = "TAILS"
        if bet:
            outcome = random.choice(["HEADS", "TAILS"])
            if bet == outcome: current_state = 1 
            else:
                cpu_choice = random.choice(["BAT", "BOWL"])
                player_role = "BOWL" if cpu_choice == "BAT" else "BAT"
                team_name = "PLAYER" if player_role == "BAT" else "CPU"
                current_state = 2; game_msg = f"Lost Toss. CPU chose to {cpu_choice}. Press 'p' to start."
    elif current_state == 1:
        if key == b'1': player_role = "BAT"; team_name = "PLAYER"; current_state = 2; game_msg = "You Chose to BAT. Press 'p'."
        elif key == b'2': player_role = "BOWL"; team_name = "CPU"; current_state = 2; game_msg = "You Chose to BOWL. Press 'p'."

    elif current_state in [2, 3]:
        if key == b'a': # Move Left
            batsman_x -= 4
            if batsman_x < -20: batsman_x = -20 
        if key == b'd': # Move Right
            batsman_x += 4
            if batsman_x > 20: batsman_x = 20 

        if key == b'p' and not ball_moving and not countdown_active:
            if player_role == "BAT": countdown_active = True; countdown_start_time = time.time(); game_msg = "CPU Bowling..."
            else: ball_moving = True; ball_vel = [random.uniform(-0.5,0.5), 4.2, random.uniform(2.5,3.5)]; game_msg = "Bowling..."
        if key == b' ' and player_role == "BAT": is_bat_swinging = True; swing_speed = -12
    
    if key == b'r' and current_state == 4: reset_match()
    if key == b'n': target_day_factor = 0.0 if target_day_factor > 0.5 else 1.0
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_angle, camera_height
    if key == GLUT_KEY_LEFT: camera_angle -= 5
    elif key == GLUT_KEY_RIGHT: camera_angle += 5
    elif key == GLUT_KEY_UP: camera_height += 20
    elif key == GLUT_KEY_DOWN: camera_height -= 20
    glutPostRedisplay()

def idle():
    global day_factor; update_physics()
    if abs(day_factor - target_day_factor) > 0.01: day_factor += (target_day_factor - day_factor) * 0.05
    glutPostRedisplay()

def main():
    glutInit(); glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800); wind = glutCreateWindow(b"Perfect Cricket")
    glutDisplayFunc(showScreen); glutKeyboardFunc(keyboardListener); glutSpecialFunc(specialKeyListener); glutIdleFunc(idle)
    glEnable(GL_DEPTH_TEST); glutMainLoop()

if __name__ == "__main__": main()
