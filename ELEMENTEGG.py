import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame
from pygame import freetype
import sys
import json
import random
import time
import datetime
import math
import colorsys
import pygame.mixer
import noise
import threading

# Initialize Pygame
pygame.init()
pygame.mixer.init()
pygame.freetype.init()

# Screen dimensions
width, height = 900, 800
WIDTH, HEIGHT = width, height  # Add this line
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

# Define colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DIRT_BROWN = (139, 69, 19)
GRASS_GREEN = (34, 139, 34)
WATER_BLUE = (65, 105, 225)
ROCK_GRAY = (128, 128, 128)
NUTRIENT_COLOR = (255, 215, 0)  # Gold
WATER_COLOR = (0, 191, 255)  # Deep Sky Blue
MINERAL_COLOR = (192, 192, 192)  # Silver
BLACK_HOLE_COLOR = (75, 0, 130)  # Indigo
HEALTH_BAR_COLOR = (50, 205, 50)  # Lime Green for health
ENERGY_BAR_COLOR = (30, 144, 255)  # Dodger Blue for energy

debug_mode = False
debug_font = pygame.font.Font(None, 24)

SOUND_FILE = "sound_preference.json"
MUSIC_FILE = "music_preference.json"
THEME_SONG_1 = './SOUNDS/Element_Egg_001.mp3'
THEME_SONG_2 = './SOUNDS/Element_Egg_002.mp3'

def load_sound_preference():
    if os.path.exists(SOUND_FILE):
        with open(SOUND_FILE, 'r') as f:
            return json.load(f)['sound_on']
    return True  # Default to sound on if file doesn't exist

def save_sound_preference(sound_on):
    with open(SOUND_FILE, 'w') as f:
        json.dump({'sound_on': sound_on}, f)

def load_music_preference():
    try:
        with open(MUSIC_FILE, 'r') as f:
            prefs = json.load(f)
            music_on = prefs.get('music_on', True)
            current_theme = prefs.get('current_theme', THEME_SONG_1)
    except (FileNotFoundError, json.JSONDecodeError):
        music_on = True
        current_theme = THEME_SONG_1
    
    return music_on, current_theme

def start_theme_song():
    if music_on:
        pygame.mixer.music.load(current_theme)
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()

def switch_theme():
    global current_theme
    if current_theme == THEME_SONG_1:
        current_theme = THEME_SONG_2
    else:
        current_theme = THEME_SONG_1
    save_music_preference(music_on, current_theme)
    start_theme_song()

def toggle_music():
    global music_on
    music_on = not music_on
    if music_on:
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()
    save_music_preference(music_on, current_theme)

def save_music_preference(music_on, current_theme):
    with open(MUSIC_FILE, 'w') as f:
        json.dump({'music_on': music_on, 'current_theme': current_theme}, f)

def validate_theme():
    global current_theme
    if current_theme not in [THEME_SONG_1, THEME_SONG_2]:
        current_theme = THEME_SONG_1  # Default to THEME_SONG_1 if invalid

def apply_music_state():
    if music_on:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()

# Now we can safely load music preferences and start the theme song
music_on, current_theme = load_music_preference()
start_theme_song()

def ensure_valid_color(color):
    """Ensure the color is a valid tuple of 3 integers between 0 and 255."""
    return tuple(max(0, min(255, int(c))) for c in color)

class Spot:
    def __init__(self, x, y, z, color, size):
        self.x = x
        self.y = y
        self.z = z
        self.base_color = ensure_valid_color(color)
        self.color = self.base_color
        self.size = size
        self.hue_shift = 0

    def update_color(self, shift):
        self.hue_shift = (self.hue_shift + shift) % 1.0
        r, g, b = self.base_color
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        h = (h + self.hue_shift) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.color = ensure_valid_color((r*255, g*255, b*255))

class EggCreature:
    def __init__(self, screen_width, screen_height, egg_width=100, egg_height=140):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.width = egg_width
        self.height = egg_height
        self.base_color = (200, 150, 100)
        self.color = self.base_color
        self.rotation = 0
        self.rotation_speed = 1
        self.highlight_intensity = 0.5
        self.light_azimuth = 2.23
        self.light_elevation = -0.45
        self.spots = self.generate_spots()
        self.surface = pygame.Surface((egg_width, egg_height), pygame.SRCALPHA)
        self.hue_shift = 0
        self.color_shift_speed = 0.005

    def generate_spots(self):
        spots = []
        colors = [WHITE, (255, 200, 200), (200, 255, 200), (200, 200, 255)]
        for _ in range(5):
            u = random.uniform(0, 1)
            v = random.uniform(0, 1)
            theta = 2 * math.pi * u
            phi = math.acos(2 * v - 1)
            x = math.sin(phi) * math.cos(theta)
            y = math.sin(phi) * math.sin(theta)
            z = math.cos(phi)
            color = random.choice(colors)
            size = random.uniform(0.05, 0.15)
            spots.append(Spot(x, y, z, color, size))
            
            for _ in range(random.randint(1, 3)):
                dx = random.uniform(-0.1, 0.1)
                dy = random.uniform(-0.1, 0.1)
                dz = random.uniform(-0.1, 0.1)
                spots.append(Spot(x + dx, y + dy, z + dz, color, size * random.uniform(0.5, 1.5)))
        
        return spots

    def update(self):
        self.rotation = (self.rotation + self.rotation_speed) % 360
        self.hue_shift = (self.hue_shift + self.color_shift_speed) % 1.0
        
        r, g, b = self.base_color
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        h = (h + self.hue_shift) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        self.color = ensure_valid_color((r*255, g*255, b*255))
        
        for spot in self.spots:
            spot.update_color(self.color_shift_speed)

    def draw(self, surface):
        self.surface.fill((0, 0, 0, 0))  # Clear the surface
        center_x, center_y = self.width // 2, self.height // 2

        # Draw egg shape (simplified)
        pygame.draw.ellipse(self.surface, self.color, (0, 0, self.width, self.height))

        # Draw spots
        angle = math.radians(self.rotation)
        for spot in self.spots:
            rotated_x = spot.x * math.cos(angle) - spot.z * math.sin(angle)
            rotated_z = spot.x * math.sin(angle) + spot.z * math.cos(angle)
            
            if rotated_z > 0:
                x = int(rotated_x * self.width / 2) + center_x
                y = int(spot.y * self.height / 2) + center_y
                
                spot_width = max(1, int(spot.size * self.width * 0.5))
                spot_height = max(1, int(spot.size * self.height * 0.3))
                pygame.draw.ellipse(self.surface, spot.color, 
                                    (x - spot_width//2, y - spot_height//2, 
                                     spot_width, spot_height))

        # Draw the pre-rendered surface onto the main surface
        surface.blit(self.surface, (self.screen_width // 2 - self.width // 2, 
                                    self.screen_height // 2 - self.height // 2 + self.height // 4))
                                    
# Initialize the egg creature
egg_creature = EggCreature(width, height)

class HatchedCreature:
    def __init__(self, traits, width, height):
        self.width = width
        self.height = height
        self.color = traits.get("color", [(255, 255, 255)])  # Default to white if no color is provided
        self.size = traits.get("size", 5)  # Default size
        self.body_parts = traits.get("body_parts", [])  # List of body parts like wings, tail, etc.
    
    def draw(self, screen):
        # Draw the body of the creature
        for i, color in enumerate(self.color):
            pygame.draw.circle(screen, color, (self.width // 2, self.height // 2), self.size * (i + 1))
        
        # Draw the body parts
        for body_part in self.body_parts:
            if body_part == "wings":
                pygame.draw.polygon(screen, (255, 255, 255), [
                    (self.width // 2 - 20, self.height // 2 - 20), 
                    (self.width // 2 + 20, self.height // 2 - 20), 
                    (self.width // 2, self.height // 2 - 40)
                ])
            elif body_part == "tail":
                pygame.draw.line(screen, (255, 255, 255), 
                    (self.width // 2, self.height // 2 + 20), 
                    (self.width // 2, self.height // 2 + 60), 5)

# Load assets
def load_image(file, fallback_color=(255, 255, 255)):
    try:
        image = pygame.image.load(file).convert_alpha()
    except pygame.error:
        image = pygame.Surface((100, 100), pygame.SRCALPHA)
        image.fill(fallback_color)
    return image

def load_sound(file):
    try:
        sound = pygame.mixer.Sound(file)
    except pygame.error:
        sound = None
    return sound

pick_sound = load_sound('./SOUNDS/play.mp3')
feed_sound = load_sound('./SOUNDS/feed.mp3')
evolve_sound = load_sound('./SOUNDS/evolve.mp3')
spin_sound = load_sound('./SOUNDS/spin.mp3')
win_sound = load_sound('./SOUNDS/win.mp3')

# Load JSON data
with open('./ASSETS/elements.json', 'r') as f:
    elements = json.load(f)

with open('./ASSETS/compounds.json', 'r') as f:
    compounds = json.load(f)

# Ensure each element has a color and atomic number
for i, element in enumerate(elements):
    if 'color' not in element:
        element['color'] = [random.randint(0, 255) for _ in range(3)]
    element['atomic_number'] = i + 1

# Global variables
current_game_name = None
selected_elements = []
element_quantities = {}
egg_level = 1
max_growth_per_level = 50
growth_level = 0
purchasing_elements = False
element_purchase_quantities = {element['symbol']: 0 for element in elements}
feeding_elements = False
feeding_quantities = {}
max_spin_frames = 120
enlarged_element = None
selected_lab_elements = []
combination_result = None
ore_chunks = 0
tokens = 0
lifetime_fed = {element['symbol']: 0 for element in elements}

# Game state
game_started = False
element_selection_confirmed = False
hatching = False
creature_displayed = False
egg_rect = pygame.Rect(0, 0, egg_creature.width, egg_creature.height)
egg_rect.center = (width // 2, height // 2)
creature_color = (0, 1, 0)  # Default creature color
confirming_delete = False
game_to_delete = None
last_autosave_time = time.time()
creature_traits = None

TILE_SIZE = 8
GRID_SIZE = 20
EMPTY, NUTRIENT, WATER, MINERAL, BLACK_HOLE = range(5)

# Initial element selection
max_elements = 3
elements_picked = 0
max_growth = 50

# Slot machine state
playing_slot_machine = False
spinning = False
spin_frames = 0
spin_slowdown = 1

reels = [['💎', '💰', '💵'] for _ in range(3)]
reel_results = [['', '', ''] for _ in range(3)]
reel_positions = [0, 0, 0]

payouts = {'💎': 100, '💰': 75, '💵': 50}

# UI elements
font_path = "C:/Windows/Fonts/seguiemj.ttf"
slot_font = pygame.font.Font(font_path, 48)

buttons = [
    {"label": "LAB", "rect": pygame.Rect(750, height // 2 - 120, 100, 50), "color": (0, 0, 255)},
    {"label": "SLOTS", "rect": pygame.Rect(750, height // 2 - 60, 100, 50), "color": (255, 255, 0)},
    {"label": "PICK", "rect": pygame.Rect(750, height // 2, 100, 50), "color": (0, 255, 0)},
    {"label": "FEED", "rect": pygame.Rect(750, height // 2 + 60, 100, 50), "color": (255, 0, 0)},
    {"label": "EAT", "rect": pygame.Rect(750, height // 2 + 120, 100, 50), "color": (255, 165, 0)},
]

# The EAT button will be added dynamically when needed
eat_button = {"label": "EAT", "rect": pygame.Rect(width // 2 - 50, height - 100, 100, 50), "color": (255, 165, 0)}
start_button = {"label": "Start Game", "rect": pygame.Rect(width // 2 - 75, height // 2, 150, 50), "color": (0, 255, 0)}
confirm_button = pygame.Rect(width - 200, height - 100, 150, 50)
spin_button = pygame.Rect(325, 675, 150, 60)
back_button = pygame.Rect(50, 675, 150, 60)

music_on, current_theme = load_music_preference()
start_theme_song()

class Landscape:
    def __init__(self, width, height, level=0):
        self.width = width
        self.height = height
        self.surface = pygame.Surface((self.width, self.height))
        self.resource_grid = [[EMPTY for _ in range(self.width // GRID_SIZE)] for _ in range(self.height // GRID_SIZE)]
        self.level = level
        self.black_hole_pos = None
        self.generate()
        self.node_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.generate_nodes()

    def draw(self, surface):
        surface.blit(self.surface, (0, 0))


    def generate_nodes(self):
        self.node_surface.fill((0, 0, 0, 0))  # Clear the node surface
        for y in range(self.height // GRID_SIZE):
            for x in range(self.width // GRID_SIZE):
                if random.random() < 0.3:  # Adjust this probability for node density
                    resource = random.choice([NUTRIENT, WATER, MINERAL])
                    self.resource_grid[y][x] = resource
                    color = NUTRIENT_COLOR if resource == NUTRIENT else WATER_COLOR if resource == WATER else MINERAL_COLOR
                    pygame.draw.circle(self.node_surface, color, 
                                       (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), 
                                       GRID_SIZE // 3)
                    pygame.draw.circle(self.node_surface, (255, 255, 255), 
                                       (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), 
                                       GRID_SIZE // 3, 1)
                                       
    def generate(self):
        color_schemes = [
            [(34, 139, 34), (65, 105, 225), (128, 128, 128)],  # Surface: Green, Blue, Gray
            [(101, 67, 33), (70, 130, 180), (169, 169, 169)],  # Underground: Brown, Steel Blue, Dark Gray
            [(165, 42, 42), (0, 191, 255), (105, 105, 105)],   # Deep: Brown, Deep Sky Blue, Dim Gray
            [(255, 69, 0), (30, 144, 255), (192, 192, 192)],   # Magma: Orange Red, Dodger Blue, Silver
            [(255, 0, 0), (0, 0, 139), (220, 220, 220)]        # Core: Red, Dark Blue, Gainsboro
        ]
        
        colors = color_schemes[min(self.level, len(color_schemes) - 1)]
        
        for y in range(0, HEIGHT, TILE_SIZE):
            for x in range(0, WIDTH, TILE_SIZE):
                nx, ny = x / WIDTH, y / HEIGHT
                value = noise.pnoise2(4 * nx, 4 * ny, octaves=6, persistence=0.5, lacunarity=2.0, repeatx=1024, repeaty=1024, base=self.level)
                
                if value < -0.1:
                    color = colors[1]  # Water-like
                elif value < 0.2:
                    color = colors[0]  # Main terrain
                elif value < 0.3:
                    color = colors[2]  # Rock-like
                else:
                    color = colors[0]  # Main terrain
                
                pygame.draw.rect(self.surface, color, (x, y, TILE_SIZE, TILE_SIZE))

        # Generate resources and black hole
        for y in range(self.height // GRID_SIZE):
            for x in range(self.width // GRID_SIZE):
                if random.random() < 0.3:
                    self.resource_grid[y][x] = random.choice([NUTRIENT, WATER, MINERAL])

        # Place black hole (not in the center 25% of the map)
        while True:
            x = random.randint(0, self.width // GRID_SIZE - 1)
            y = random.randint(0, self.height // GRID_SIZE - 1)
            if x < self.width // (4 * GRID_SIZE) or x >= 3 * self.width // (4 * GRID_SIZE) or \
               y < self.height // (4 * GRID_SIZE) or y >= 3 * self.height // (4 * GRID_SIZE):
                self.resource_grid[y][x] = BLACK_HOLE
                self.black_hole_pos = (x, y)
                break

    def draw(self, surface):
        surface.blit(self.surface, (0, 0))

    def draw_nodes(self, surface):
        surface.blit(self.node_surface, (0, 0))

    def consume_resource(self, x, y):
        grid_x, grid_y = x // GRID_SIZE, y // GRID_SIZE
        if 0 <= grid_x < self.width // GRID_SIZE and 0 <= grid_y < self.height // GRID_SIZE:
            resource = self.resource_grid[grid_y][grid_x]
            self.resource_grid[grid_y][grid_x] = EMPTY
            if resource != BLACK_HOLE:
                pygame.draw.rect(self.surface, DIRT_BROWN, (grid_x * GRID_SIZE, grid_y * GRID_SIZE, GRID_SIZE, GRID_SIZE))
                pygame.draw.circle(self.node_surface, (0, 0, 0, 0), 
                                   (grid_x * GRID_SIZE + GRID_SIZE // 2, grid_y * GRID_SIZE + GRID_SIZE // 2), 
                                   GRID_SIZE // 3)
            return resource
        return EMPTY

    def reveal_nodes(self):
        for y in range(self.height // GRID_SIZE):
            for x in range(self.width // GRID_SIZE):
                if self.resource_grid[y][x] != EMPTY:
                    color = NUTRIENT_COLOR if self.resource_grid[y][x] == NUTRIENT else WATER_COLOR if self.resource_grid[y][x] == WATER else MINERAL_COLOR if self.resource_grid[y][x] == MINERAL else BLACK_HOLE_COLOR
                    pygame.draw.circle(self.node_surface, color, 
                                       (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), 
                                       GRID_SIZE // 3)
                    pygame.draw.circle(self.node_surface, (255, 255, 255), 
                                       (x * GRID_SIZE + GRID_SIZE // 2, y * GRID_SIZE + GRID_SIZE // 2), 
                                       GRID_SIZE // 3, 1)
class EatCreature:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 5  # Start small
        self.max_size = 15
        self.growth_rate = 0.01  # Slow growth rate
        self.base_speed = 0.7
        self.health = 100
        self.energy = 100
        self.direction = [random.uniform(-1, 1), random.uniform(-1, 1)]
        self.target = None
        self.black_hole_found = False
        self.last_meal_time = pygame.time.get_ticks()
        self.swallowed = False
        self.swallow_progress = 0
        self.wander_count = 0
        self.last_consumed_color = WHITE
        self.skill_timers = {'reveal': 0, 'big_bite': 0}

    def consume(self, resource, landscape):
        self.last_meal_time = pygame.time.get_ticks()
        if resource == NUTRIENT:
            self.health = min(100, self.health + 5)
            self.last_consumed_color = NUTRIENT_COLOR
        elif resource == WATER:
            self.energy = min(100, self.energy + 10)
            self.last_consumed_color = WATER_COLOR
        elif resource == MINERAL:
            self.size = min(self.max_size, self.size + self.growth_rate)
            self.last_consumed_color = MINERAL_COLOR
        elif resource == BLACK_HOLE:
            self.black_hole_found = True
            self.last_consumed_color = BLACK_HOLE_COLOR
            self.teleport_to_next_level(landscape)

    def draw(self, surface):
        if self.swallowed:
            self.swallow_progress += 2
            radius = int(self.size + self.swallow_progress)
            if radius > 2 * self.size:
                self.size -= 1
                if self.size <= 0:
                    return False
            pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), radius)
        else:
            pygame.draw.circle(surface, self.last_consumed_color, (int(self.x), int(self.y)), int(self.size) + 2)
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), int(self.size))
        return True
    def get_speed(self):
        if self.energy <= 10:
            return self.base_speed * 0.25
        elif self.energy <= 25:
            return self.base_speed * 0.5
        elif self.energy <= 75:
            return self.base_speed
        else:
            return self.base_speed * 1.25

    def move(self, landscape):
        if self.swallowed:
            return False

        if self.black_hole_found:
            self.swallowed = True
            return True

        if self.target is None or random.random() < 0.05:
            self.find_new_target(landscape)

        if self.target:
            dx = self.target[0] - self.x
            dy = self.target[1] - self.y
            distance = (dx**2 + dy**2)**0.5
            speed = self.get_speed()
            if distance > speed:
                self.x += (dx / distance) * speed
                self.y += (dy / distance) * speed
            else:
                self.x, self.y = self.target
                self.target = None

        self.x = max(0, min(landscape.width - 1, self.x))
        self.y = max(0, min(landscape.height - 1, self.y))
        self.energy = max(0, self.energy - 0.05)  # Slower energy drain
        self.health = max(0, self.health - 0.005)  # Slower health drain

        # Manage active skills
        self.manage_skills(landscape)

        return True

    def find_new_target(self, landscape):
        if self.black_hole_found:
            return

        # Check for nearby resources in a small radius first
        search_radius = 2
        nearby_resources = []
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                grid_x = int(self.x // GRID_SIZE + dx)
                grid_y = int(self.y // GRID_SIZE + dy)
                if 0 <= grid_x < landscape.width // GRID_SIZE and 0 <= grid_y < landscape.height // GRID_SIZE:
                    if landscape.resource_grid[grid_y][grid_x] != EMPTY:
                        distance = math.hypot(grid_x * GRID_SIZE + GRID_SIZE // 2 - self.x,
                                              grid_y * GRID_SIZE + GRID_SIZE // 2 - self.y)
                        nearby_resources.append((distance, (grid_x * GRID_SIZE + GRID_SIZE // 2,
                                                            grid_y * GRID_SIZE + GRID_SIZE // 2)))

        if nearby_resources:
            nearby_resources.sort(key=lambda r: r[0])
            self.target = nearby_resources[0][1]
            self.wander_count = 0  # Reset wander count after finding a target
            print(f"New target found at ({self.target[0]}, {self.target[1]})")
        else:
            # Limit random wandering and force a search after a few failed attempts
            if self.wander_count < 5:
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(20, 60)
                self.target = ((self.x + math.cos(angle) * distance) % landscape.width,
                               (self.y + math.sin(angle) * distance) % landscape.height)
                self.wander_count += 1
                print(f"Random wandering to ({self.target[0]}, {self.target[1]})")
            else:
                print("Forcing a teleport after too much wandering")
                self.teleport(landscape)
                self.wander_count = 0  # Reset wander count after teleporting

    def update(self):
        if not self.creature.move(self.landscape):
            return False

        resource = self.landscape.consume_resource(int(self.creature.x), int(self.creature.y))
        if resource != EMPTY:
            self.creature.consume(resource, self.landscape)
            if resource == BLACK_HOLE:
                self.depth += 1
                self.score += 100 * self.depth
                self.landscape = Landscape(self.landscape.width, self.landscape.height, self.depth)
                self.creature.x, self.creature.y = self.landscape.width // 2, self.landscape.height // 2
            else:
                self.score += 1

        if time.time() - self.reveal_timer > self.reveal_duration:
            self.reveal_timer = 0

        return True

    def reveal_nodes(self):
        self.reveal_timer = time.time()

    def teleport(self, landscape):
        new_x = random.randint(0, landscape.width)
        new_y = random.randint(0, landscape.height)
        print(f"Random teleport to ({new_x}, {new_y})")
        self.x = new_x
        self.y = new_y
        self.target = None

    def teleport_to_next_level(self, landscape):
        print("Teleporting to the next level...")
        self.x = landscape.width // 2
        self.y = landscape.height // 2
        self.black_hole_found = False
        self.swallowed = False
        self.swallow_progress = 0

    def manage_skills(self, landscape):
        current_time = pygame.time.get_ticks()
        
        if current_time - self.skill_timers['reveal'] > 15000:  # Reveal every 15 seconds
            self.reveal_area(landscape)
            self.skill_timers['reveal'] = current_time
        
        if current_time - self.skill_timers['big_bite'] > 20000:  # Big bite every 20 seconds
            self.big_bite(landscape)
            self.skill_timers['big_bite'] = current_time

    def reveal_area(self, landscape):
        reveal_radius = 100  # Radius of reveal area
        grid_radius = reveal_radius // GRID_SIZE
        cx, cy = int(self.x // GRID_SIZE), int(self.y // GRID_SIZE)

        # Clear previous reveal effect
        landscape.generate()

        for dy in range(-grid_radius, grid_radius + 1):
            for dx in range(-grid_radius, grid_radius + 1):
                grid_x = cx + dx
                grid_y = cy + dy
                if 0 <= grid_x < WIDTH // GRID_SIZE and 0 <= grid_y < HEIGHT // GRID_SIZE:
                    if landscape.resource_grid[grid_y][grid_x] != EMPTY:
                        pygame.draw.circle(landscape.surface, landscape.resource_grid[grid_y][grid_x], (grid_x * GRID_SIZE + GRID_SIZE // 2, grid_y * GRID_SIZE + GRID_SIZE // 2), GRID_SIZE // 2)

    def big_bite(self, landscape):
        bite_radius = 3 * self.size
        grid_radius = int(bite_radius // GRID_SIZE)  # Convert to integer
        cx, cy = int(self.x // GRID_SIZE), int(self.y // GRID_SIZE)

        for dy in range(-grid_radius, grid_radius + 1):
            for dx in range(-grid_radius, grid_radius + 1):
                grid_x = cx + dx
                grid_y = cy + dy
                if 0 <= grid_x < landscape.width // GRID_SIZE and 0 <= grid_y < landscape.height // GRID_SIZE:
                    resource = landscape.resource_grid[grid_y][grid_x]
                    if resource != EMPTY and resource != BLACK_HOLE:
                        landscape.consume_resource(grid_x * GRID_SIZE, grid_y * GRID_SIZE)
                        self.consume(resource, landscape)  # Pass landscape here
                    if resource == BLACK_HOLE:
                        self.black_hole_found = True
                        self.teleport_to_next_level(landscape)  # Pass landscape here

class EatCreatureGame:
    def __init__(self, creature_stats):
        self.landscape = Landscape(WIDTH, HEIGHT)
        self.creature = EatCreature(creature_stats['x'], creature_stats['y'])
        self.score = 0
        self.depth = 0
        self.running_in_background = False
        self.initialize_creature(creature_stats)
        self.reveal_timer = 0
        self.reveal_duration = 3
        self.reveal_cooldown = 15

    def initialize_creature(self, stats):
        self.creature.size = stats['size']
        self.creature.health = stats['health']
        self.creature.energy = stats['energy']

    def update(self):
        current_time = time.time()

        if not self.creature.move(self.landscape):
            return False

        resource = self.landscape.consume_resource(int(self.creature.x), int(self.creature.y))
        if resource != EMPTY:
            self.creature.consume(resource, self.landscape)
            if resource == BLACK_HOLE:
                self.depth += 1
                self.score += 100 * self.depth
                self.landscape = Landscape(self.landscape.width, self.landscape.height, self.depth)
                self.creature.x, self.creature.y = self.landscape.width // 2, self.landscape.height // 2
            else:
                self.score += 1

        # Automatic reveal skill
        if current_time - self.reveal_timer > self.reveal_cooldown:
            self.reveal_timer = current_time
            self.landscape.reveal_nodes()

        return True

    def draw(self, surface):
        self.landscape.draw(surface)
        self.creature.draw(surface)

        font = pygame.font.Font(None, 24)
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        depth_text = font.render(f"Depth: {self.depth}", True, (255, 255, 255))
        surface.blit(score_text, (10, 10))
        surface.blit(depth_text, (10, 40))

        # Draw RECALL button
        recall_button = pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 50)
        pygame.draw.rect(surface, (255, 0, 0), recall_button)
        recall_font = pygame.font.Font(None, 24)
        recall_text = recall_font.render("RECALL", True, (255, 255, 255))
        text_rect = recall_text.get_rect(center=recall_button.center)
        surface.blit(recall_text, text_rect)

    def recall_creature(self):
        self.running_in_background = False
        print("Creature recalled from exploration.")

    def run(self):
        self.running_in_background = True
        while self.running_in_background:
            if not self.update():
                self.running_in_background = False
            time.sleep(0.1)  # Add a small delay to prevent excessive CPU usage
        return self.score, self.depth

    # def reveal_nodes(self):
        # self.reveal_timer = time.time()

    # def handle_input(self):
        # for event in pygame.event.get():
            # if event.type == pygame.QUIT:
                # return False
            # elif event.type == pygame.KEYDOWN:
                # if event.key == pygame.K_ESCAPE:
                    # return False
        # return True

def start_eat_creature_minigame():
    global eat_game
    if not eat_game:
        creature_stats = {
            'size': egg_creature.width // 2,
            'health': 100,
            'energy': 100,
        }
        eat_game = EatCreatureGame(creature_stats)
        eat_game.running_in_background = True
        threading.Thread(target=eat_game.run, daemon=True).start()
    print("Creature started exploring!")

def handle_minigame_results(self, score, depth):
    global ore_chunks, tokens
    ore_chunks += score
    tokens += depth
    print(f"Mini-game results: Score: {score}, Depth: {depth}")
    print(f"New totals: ORE: {ore_chunks}, Tokens: {tokens}")



def ensure_valid_color(color):
    """Ensure the color is a valid tuple of 3 integers between 0 and 255."""
    return tuple(max(0, min(255, int(c))) for c in color)

# Draw buttons
def draw_buttons():
    for button in buttons:
        pygame.draw.rect(screen, button["color"], button["rect"])
        pygame.draw.line(screen, (255, 255, 255), (button["rect"].x, button["rect"].y), (button["rect"].x + button["rect"].width, button["rect"].y), 2)
        pygame.draw.line(screen, (255, 255, 255), (button["rect"].x, button["rect"].y), (button["rect"].x, button["rect"].y + button["rect"].height), 2)
        text = debug_font.render(button["label"], True, (0, 0, 0))
        text_rect = text.get_rect(center=button["rect"].center)
        screen.blit(text, text_rect)
        # Draw button coordinates
        # coord_text = font.render(f"{button['rect'].x}, {button['rect'].y}", True, (255, 255, 255))
        # screen.blit(coord_text, (button["rect"].x, button["rect"].y - 20))

def draw_debug_overlay(fps):
    if debug_mode:
        fps_text = debug_font.render(f"FPS: {fps:.2f}", True, (255, 255, 255))
        screen.blit(fps_text, (width - 100, 10))

def draw_title_screen():
    screen.fill((0, 0, 0))
    
    egg_creature.draw(screen)
    
    font = pygame.font.Font(None, 72)
    title_text = font.render("ELEMENT EGG", True, (255, 255, 255))
    title_rect = title_text.get_rect(center=(width // 2, height // 4))
    screen.blit(title_text, title_rect)
    
    tagline_font = pygame.font.Font(None, 36)
    tagline_text = tagline_font.render("Hatch your ultimate power!", True, (255, 255, 255))
    tagline_rect = tagline_text.get_rect(center=(width // 2, height // 4 + 60))
    screen.blit(tagline_text, tagline_rect)
    
    button_height = start_button["rect"].height
    start_button["rect"].centery = height - 4 * button_height
    
    pygame.draw.rect(screen, start_button["color"], start_button["rect"])
    pygame.draw.line(screen, (255, 255, 255), (start_button["rect"].x, start_button["rect"].y), (start_button["rect"].x + start_button["rect"].width, start_button["rect"].y), 2)
    pygame.draw.line(screen, (255, 255, 255), (start_button["rect"].x, start_button["rect"].y), (start_button["rect"].x, start_button["rect"].y + start_button["rect"].height), 2)
    
    button_font = pygame.font.Font(None, 36)
    button_text = button_font.render(start_button["label"], True, (0, 0, 0))
    button_text_rect = button_text.get_rect(center=start_button["rect"].center)
    screen.blit(button_text, button_text_rect)

# Draw periodic table
def draw_periodic_table():
    global enlarged_element
    element_size = 40
    for i, element in enumerate(elements):
        x = 50 + (i % 18) * (element_size + 5)
        y = 50 + (i // 18) * (element_size + 5)  # Adjusted position
        rect_color = element["color"] if "color" in element else [100, 100, 100]
        pygame.draw.rect(screen, rect_color, (x, y, element_size, element_size))
        font = pygame.font.Font(None, 18)
        text = font.render(element["symbol"], True, (255, 255, 255) if rect_color == [0, 0, 0] else (0, 0, 0))
        screen.blit(text, (x + 5, y + 5))
        atomic_number_text = font.render(str(element["atomic_number"]), True, (255, 255, 255))
        screen.blit(atomic_number_text, (x + 5, y + 20))
        
        if enlarged_element and enlarged_element['symbol'] == element['symbol']:
            enlarged_rect = pygame.Rect(50, height - 350, 300, 300)  # Bottom-left corner
            pygame.draw.rect(screen, rect_color, enlarged_rect)
            large_font = pygame.font.Font(None, 72)
            large_text = large_font.render(element["symbol"], True, (255, 255, 255))
            large_text_rect = large_text.get_rect(center=(enlarged_rect.centerx, enlarged_rect.y + 80))
            screen.blit(large_text, large_text_rect)
            name_text = pygame.font.Font(None, 36).render(element["name"], True, (255, 255, 255))
            screen.blit(name_text, (enlarged_rect.x + 10, enlarged_rect.y + 120))
            atomic_text = pygame.font.Font(None, 36).render(f"Atomic Number: {element['atomic_number']}", True, (255, 255, 255))
            screen.blit(atomic_text, (enlarged_rect.x + 10, enlarged_rect.y + 160))
            weight_text = pygame.font.Font(None, 36).render(f"Atomic Weight: {element['atomic_weight']}", True, (255, 255, 255))
            screen.blit(weight_text, (enlarged_rect.x + 10, enlarged_rect.y + 200))

def create_new_game():
    global current_screen, ore_chunks, selected_elements, element_quantities, egg_level, growth_level, tokens, current_game_name
    ore_chunks = 0
    selected_elements = []
    element_quantities = {}
    egg_level = 1
    growth_level = 0
    tokens = 1  # Give the player 1 token to start
    current_screen = "element_selection"
    current_game_name = None
    save_game()  # Save immediately after creating a new game

# Draw selected elements
def draw_selected_elements():
    for i, element in enumerate(selected_elements):
        x = 370
        y = height - 350 + i * 100
        rect_color = element["color"] if "color" in element else [100, 100, 100]
        pygame.draw.rect(screen, rect_color, (x, y, 80, 80))
        font = pygame.font.Font(None, 24)
        text = font.render(element["symbol"], True, (255, 255, 255) if rect_color == [0, 0, 0] else (0, 0, 0))
        screen.blit(text, (x + 10, y + 10))
        text = font.render(element["name"], True, (255, 255, 255))
        screen.blit(text, (x + 90, y + 40))

# Draw growth meter
def draw_growth_meter():
    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(750, 450, 100, 30))
    fill_width = int(100 * (growth_level / max_growth))
    pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(750, 450, fill_width, 30))
    font = pygame.font.Font(None, 24)
    text = font.render(f"Growth: {growth_level}/{max_growth}", True, (0, 0, 0))
    screen.blit(text, (750, 420))

# Draw ORE meter
def draw_ore_meter():
    pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(750, 450, 100, 30))
    fill_width = int(100 * (ore_chunks / 9999))
    pygame.draw.rect(screen, (0, 255, 0), pygame.Rect(750, 450, fill_width, 30))
    font = pygame.font.Font(None, 24)
    text = font.render(f"ORE: {ore_chunks}/9999", True, (255, 255, 255))
    screen.blit(text, (750, 420))

# Updated draw_slot_machine function
def draw_slot_machine(first_time=False):
    screen.fill((0, 0, 0))
    
    # Draw slot machine frame
    pygame.draw.rect(screen, (150, 75, 0), (50, 50, 800, 500))
    pygame.draw.rect(screen, (100, 50, 0), (60, 60, 780, 480))
    
    # Draw reels with corrected spacing
    reel_width = 240
    reel_height = 400
    reel_spacing = (780 - 3 * reel_width) // 2  # Adjust spacing between reels
    for i in range(3):
        x = 60 + i * (reel_width + reel_spacing)
        pygame.draw.rect(screen, (200, 200, 200), (x, 100, reel_width, reel_height))
    
    if first_time:
        # Show a "loss" state for new games
        for i in range(3):
            for j in range(3):
                text = slot_font.render("X", True, (0, 0, 0))
                text_rect = text.get_rect(center=(60 + i * (reel_width + reel_spacing) + reel_width // 2, 150 + j * 150))
                screen.blit(text, text_rect)
    else:
        for i in range(3):
            for j in range(3):
                text = slot_font.render(reel_results[j][i], True, (0, 0, 0))
                text_rect = text.get_rect(center=(60 + i * (reel_width + reel_spacing) + reel_width // 2, 150 + j * 125))  # Adjust vertical positioning
                screen.blit(text, text_rect)
    
    # Draw SPIN button
    pygame.draw.rect(screen, (255, 0, 0), (325, 675, 150, 60))
    spin_text = slot_font.render("SPIN", True, (255, 255, 255))
    spin_rect = spin_text.get_rect(center=(400, 705))
    screen.blit(spin_text, spin_rect)
    
    # Draw Back button
    pygame.draw.rect(screen, (0, 0, 255), (50, 675, 150, 60))
    back_text = slot_font.render("BACK", True, (255, 255, 255))
    back_rect = back_text.get_rect(center=(125, 705))
    screen.blit(back_text, back_rect)

    # Draw token count
    token_text = slot_font.render(f"Tokens: {tokens}", True, (255, 255, 255))
    screen.blit(token_text, (600, 675))

    # Draw total ORE count
    ore_text = slot_font.render(f"ORE: {ore_chunks}", True, (255, 255, 255))
    screen.blit(ore_text, (600, 725))

def draw_selected_ores():
    for i, element in enumerate(selected_elements):
        x = width // 2 - 100 + i * 100  # Adjusted position to center the egg
        y = 50
        rect_color = element["color"] if "color" in element else [100, 100, 100]
        pygame.draw.rect(screen, rect_color, (x, y, 80, 80))
        font = pygame.font.Font(None, 36)
        text = font.render(element["symbol"], True, (255, 255, 255) if rect_color == [0, 0, 0] else (0, 0, 0))
        screen.blit(text, (x + 20, y + 20))
        quantity_text = font.render(f"{element_quantities[element['symbol']]}", True, (255, 255, 255))
        screen.blit(quantity_text, (x + 20, y + 100))  # Display quantity below the tile

def draw_lab_screen():
    global combination_result, screen, selected_lab_elements
    screen.fill((50, 50, 50))  # Dark gray background
    font = pygame.font.Font(None, 36)
    
    # Draw LABORATORY title
    title = font.render("LABORATORY", True, (255, 255, 255))
    screen.blit(title, (width // 2 - 100, 50))

    # Draw periodic table
    draw_lab_periodic_table(scale=0.9, y_offset=100)

    # Calculate the bottom of the periodic table
    table_bottom = 100 + (7 * (int(40 * 0.9) + int(5 * 0.9)))  # y_offset + (7 rows * (element_size + gap))

    # Draw element details area
    if selected_lab_elements:
        last_element = selected_lab_elements[-1]
        draw_element_details(last_element, width // 4 - 150, table_bottom + 20, 300, 150)  # Moved towards center

    # Draw selected elements
    slot_size = 60
    for i in range(6):
        slot_x = width // 2 - 180 + i * 70
        slot_y = height - 150
        pygame.draw.rect(screen, (100, 100, 100), (slot_x, slot_y, slot_size, slot_size))
        if i < len(selected_lab_elements):
            element = selected_lab_elements[i]
            pygame.draw.rect(screen, element["color"], (slot_x, slot_y, slot_size, slot_size))
            text = font.render(element['symbol'], True, (255, 255, 255))
            text_rect = text.get_rect(center=(slot_x + slot_size // 2, slot_y + slot_size // 2))
            screen.blit(text, text_rect)

    # Draw COMBINE button
    combine_button = pygame.Rect(50, height - 80, 120, 60)
    pygame.draw.rect(screen, (0, 255, 0), combine_button)
    combine_text = font.render("COMBINE", True, (0, 0, 0))
    combine_text_rect = combine_text.get_rect(center=combine_button.center)
    screen.blit(combine_text, combine_text_rect)

    # Draw BACK button
    back_button = pygame.Rect(180, height - 80, 100, 60)
    pygame.draw.rect(screen, (255, 0, 0), back_button)
    back_text = font.render("Back", True, (0, 0, 0))
    back_text_rect = back_text.get_rect(center=back_button.center)
    screen.blit(back_text, back_text_rect)

    # Draw token count
    token_text = font.render(f"Tokens: {tokens}", True, (255, 255, 255))
    screen.blit(token_text, (width - 200, 50))

    # Draw combination results
    if combination_result:
        draw_combination_result(combination_result, 3 * width // 4 - 150, table_bottom + 20)  # Moved towards center

    pygame.display.flip()
    
def draw_lab_periodic_table(scale=0.9, y_offset=100):
    element_size = int(40 * scale)
    font_size = int(18 * scale)
    table_width = 18 * element_size + 17 * 5 * scale  # 18 elements wide, 17 gaps
    x_start = (width - table_width) // 2  # Center the table

    for i, element in enumerate(elements):
        x = int(x_start + (i % 18) * (element_size + 5 * scale))
        y = int(y_offset + (i // 18) * (element_size + 5 * scale))
        rect_color = element["color"] if "color" in element else [100, 100, 100]
        pygame.draw.rect(screen, rect_color, (x, y, element_size, element_size))
        font = pygame.font.Font(None, font_size)
        text = font.render(element["symbol"], True, (255, 255, 255) if rect_color == [0, 0, 0] else (0, 0, 0))
        screen.blit(text, (x + 5, y + 5))
        atomic_number_text = font.render(str(element["atomic_number"]), True, (255, 255, 255))
        screen.blit(atomic_number_text, (x + 5, y + int(20 * scale)))

def draw_element_details(element, x, y, width=300, height=200):
    detail_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(screen, element["color"], detail_rect)
    
    font = pygame.font.Font(None, 36)
    symbol_text = font.render(element['symbol'], True, (255, 255, 255))
    screen.blit(symbol_text, (x + 10, y + 10))
    
    font = pygame.font.Font(None, 24)
    texts = [
        f"Name: {element['name']}",
        f"Atomic Number: {element['atomic_number']}",
        f"Atomic Weight: {element['atomic_weight']}"
    ]
    
    for i, text in enumerate(texts):
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (x + 10, y + 50 + i * 30))

def handle_lab_interaction(x, y, right_click=False):
    global selected_lab_elements, combination_result, tokens, current_screen, ore_chunks

    element = get_clicked_element(x, y)
    if element:
        if right_click:
            if element in selected_lab_elements:
                selected_lab_elements.remove(element)
        else:
            if len(selected_lab_elements) < 6:  # Remove the check for element not in selected_lab_elements
                selected_lab_elements.append(element)
        return

    # Check if a selected element was right-clicked
    for i, selected_element in enumerate(selected_lab_elements):
        slot_x = width // 2 - 180 + i * 70
        slot_y = height - 150
        slot_rect = pygame.Rect(slot_x, slot_y, 60, 60)
        if slot_rect.collidepoint(x, y) and right_click:
            selected_lab_elements.pop(i)
            return

    combine_button = pygame.Rect(50, height - 80, 120, 60)
    if combine_button.collidepoint(x, y) and not right_click:
        if len(selected_lab_elements) >= 2:
            combination_result = combine_elements(selected_lab_elements)
            if isinstance(combination_result, dict):
                tokens += 5  # Remove this line, as we're now adding tokens in combine_elements
                ore_chunks += 10  # Adjust as needed
            else:
                tokens += 1
                ore_chunks += 2
            print(f"After combination: Tokens: {tokens}, Ore: {ore_chunks}")  # Add this debug print
            selected_lab_elements = []
        else:
            combination_result = "Select at least 2 elements to combine."

    back_button = pygame.Rect(180, height - 80, 100, 60)
    if back_button.collidepoint(x, y) and not right_click:
        current_screen = "main_game"
        selected_lab_elements = []
        combination_result = None

def get_clicked_element(x, y):
    scale = 0.9
    element_size = int(40 * scale)
    table_width = 18 * element_size + 17 * 5 * scale
    x_start = (width - table_width) // 2
    y_start = 100  # This should match the y_offset in draw_lab_periodic_table

    for i, element in enumerate(elements):
        element_x = int(x_start + (i % 18) * (element_size + 5 * scale))
        element_y = int(y_start + (i // 18) * (element_size + 5 * scale))
        element_rect = pygame.Rect(element_x, element_y, element_size, element_size)
        if element_rect.collidepoint(x, y):
            return element
    return None

def draw_combination_result(result, x, y):
    font = pygame.font.Font(None, 24)
    title_font = pygame.font.Font(None, 30)
    result_rect = pygame.Rect(x, y, 300, 200)
    pygame.draw.rect(screen, (200, 200, 200), result_rect)

    # Function to render emoji
    def render_emoji(emoji, size):
        font = pygame.font.Font(font_path, size)
        return font.render(emoji, True, (0, 0, 0))

    # Draw token emoji
    token_emoji = render_emoji('🪙', 48)
    screen.blit(token_emoji, (x + 10, y + 10))
    
    # Superimpose token count
    token_count = result.get('tokens', 1) if isinstance(result, dict) else 1
    count_text = title_font.render(str(token_count), True, (255, 255, 255))
    
    # Center the text, then shift right by half its width
    count_rect = count_text.get_rect(center=(x + 34, y + 34))
    count_rect.x += count_rect.width // 4

    screen.blit(count_text, count_rect)

    if isinstance(result, dict):  # Known compound
        compound_name = result.get('name', 'Unknown')
        formula = result.get('formula', '')
        description = result.get('description', 'Missing description')
        trivia = result.get('trivia', 'Missing trivia')

        name_text = title_font.render(compound_name, True, (0, 0, 0))
        formula_text = font.render(formula, True, (0, 0, 0))
        screen.blit(name_text, (x + 70, y + 10))
        screen.blit(formula_text, (x + 70, y + 40))

        # Display description with text wrapping
        desc_lines = wrap_text(description, font, 280)
        for i, line in enumerate(desc_lines[:3]):
            desc_text = font.render(line, True, (0, 0, 0))
            screen.blit(desc_text, (x + 10, y + 70 + i * 20))

        # Display trivia with text wrapping
        trivia_lines = wrap_text("Trivia: " + trivia, font, 280)
        for i, line in enumerate(trivia_lines[:2]):
            trivia_text = font.render(line, True, (0, 0, 0))
            screen.blit(trivia_text, (x + 10, y + 140 + i * 20))

    else:  # Unknown combination
        unknown_text = title_font.render("UNKNOWN ORE", True, (0, 0, 0))
        screen.blit(unknown_text, (x + 70, y + 10))
        
        value_text = font.render("VALUE: 1 TOKEN", True, (0, 0, 0))
        screen.blit(value_text, (x + 70, y + 40))
        
        description = "You've discovered an UNKNOWN combination! Keep experimenting to earn more tokens."
        desc_lines = wrap_text(description, font, 280)
        for i, line in enumerate(desc_lines):
            desc_text = font.render(line, True, (0, 0, 0))
            screen.blit(desc_text, (x + 10, y + 70 + i * 20))
        
        trivia = "Tip: Play the slot machine to earn more tokens!"
        trivia_lines = wrap_text("Trivia: " + trivia, font, 280)
        for i, line in enumerate(trivia_lines):
            trivia_text = font.render(line, True, (0, 0, 0))
            screen.blit(trivia_text, (x + 10, y + 140 + i * 20))

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        if font.size(test_line)[0] <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    lines.append(' '.join(current_line))
    return lines
    
def combine_elements(selected_elements):
    global compounds, tokens
    
    selected_symbols = [e['symbol'] for e in selected_elements]
    element_counts = {symbol: selected_symbols.count(symbol) for symbol in set(selected_symbols)}
    
    possible_compounds = []
    for compound in compounds:
        if set(compound['elements']) == set(selected_symbols):
            compound_element_counts = {element: compound['formula'].count(element) for element in set(compound['elements'])}
            if all(element_counts[element] >= count for element, count in compound_element_counts.items()):
                possible_compounds.append(compound)
    
    if possible_compounds:
        # Weight the compounds based on how closely they match the selected elements
        weights = []
        for compound in possible_compounds:
            compound_element_counts = {element: compound['formula'].count(element) for element in set(compound['elements'])}
            weight = sum(min(element_counts[element], compound_element_counts.get(element, 0)) for element in set(selected_symbols))
            weights.append(weight)
        
        result = random.choices(possible_compounds, weights=weights, k=1)[0]
        result['tokens'] = len(selected_elements) * 2  # 2x tokens for every element used
        tokens += result['tokens']  # Add this line to update the global token count
        print(f"Gained {result['tokens']} tokens. New total: {tokens}")  # Add this debug print
        return result
    
    # If no matching compound is found, create an unknown compound
    total_atomic_number = sum(element['atomic_number'] for element in selected_elements)
    return {
        'name': 'UNKNOWN ORE',
        'formula': f'ATOMIC NUMBER: {total_atomic_number}',
        'description': "You've discovered an UNKNOWN combination! Keep experimenting to earn more tokens.",
        'trivia': "Tip: Use TOKENS at the SLOT MACHINE to earn ORE!",
        'tokens': 1
    }
    
def handle_lab_element_selection(x, y):
    global selected_lab_elements
    scale = 0.8
    element_size = int(40 * scale)
    for i, element in enumerate(elements):
        element_rect = pygame.Rect(
            int(50 * scale + (i % 18) * (element_size + 5 * scale)),
            int(100 + (50 * scale) + (i // 18) * (element_size + 5 * scale)),
            element_size,
            element_size
        )
        if element_rect.collidepoint(x, y) and element_quantities.get(element['symbol'], 0) > 0:
            if element not in selected_lab_elements:
                if len(selected_lab_elements) < 6:
                    selected_lab_elements.append(element)
                    element_quantities[element['symbol']] -= 1
            else:
                selected_lab_elements.remove(element)
                element_quantities[element['symbol']] += 1

def spin_reels():
    global spinning, spin_frames, reel_positions, reel_results, spin_slowdown
    
    if spin_sound:
        spin_sound.play()
    
    spinning = True
    spin_frames = 0
    spin_slowdown = 1
    
    for i in range(3):
        reel_positions[i] = random.randint(0, len(reels[i]) - 1)
        for j in range(3):
            reel_results[j][i] = reels[i][(reel_positions[i] + j) % len(reels[i])]
            
def update_spinning_reels():
    global spinning, spin_frames, reel_positions, reel_results, spin_slowdown
    
    if spinning:
        spin_frames += 1
        if spin_frames >= max_spin_frames:
            spinning = False
            spin_slowdown = 1
            evaluate_spin()
        else:
            for i in range(3):  # Ensure all three reels are updated
                if spin_frames < max_spin_frames - i * 20:
                    reel_positions[i] = (reel_positions[i] + spin_slowdown) % len(reels[i])
                    for j in range(3):
                        reel_results[j][i] = reels[i][(reel_positions[i] + j) % len(reels[i])]
            
            if spin_frames > max_spin_frames // 2:
                spin_slowdown = max(1, spin_slowdown - 0.05)

def handle_button_click(label):
    global playing_slot_machine, tokens, current_screen, eat_game
    if label == "LAB":
        current_screen = "lab"
    elif label == "SLOTS":
        if tokens > 0:
            playing_slot_machine = True
            current_screen = "slot_machine"
        else:
            print("Not enough tokens to play slots!")
    elif label == "PICK":
        current_screen = "element_purchase"
    elif label == "FEED":
        current_screen = "feeding"
    elif label == "EAT":
        if creature_displayed and egg_level >= 10:
            if eat_game and eat_game.running_in_background:
                current_screen = "eat_creature"  # Switch to EatCreature view
            else:
                start_eat_creature_minigame()
                current_screen = "eat_creature"
    elif label == "SPIN":
        if not spinning and tokens > 0:
            tokens -= 1
            spin_reels()
    elif label == "BACK":
        current_screen = "main_game"
    elif label == "CONFIRM":
        if elements_picked >= max_elements:
            element_selection_confirmed = True
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_game(f"autosave_{timestamp}")

def start_eat_creature_minigame():
    global eat_game
    if not eat_game:
        creature_stats = {
            'size': 5,  # Start small in the mini-game
            'health': 100,
            'energy': 100,
            'x': WIDTH // 2,  # Position in the middle of the screen
            'y': HEIGHT // 2
        }
        eat_game = EatCreatureGame(creature_stats)
        eat_game.running_in_background = True
        threading.Thread(target=eat_game.run, daemon=True).start()
    print("Creature started exploring!")

def handle_element_selection(x, y):
    global selected_elements, elements_picked, element_quantities, element_purchase_quantities, enlarged_element, feeding_quantities
    element_size = 40
    for i, element in enumerate(elements):
        element_rect = pygame.Rect(50 + (i % 18) * (element_size + 5), 50 + (i // 18) * (element_size + 5), element_size, element_size)
        if element_rect.collidepoint(x, y):
            if element not in selected_elements:
                if len(selected_elements) >= max_elements:
                    removed_element = selected_elements.pop(0)
                    element_quantities.pop(removed_element['symbol'], None)
                    element_purchase_quantities.pop(removed_element['symbol'], None)
                    feeding_quantities.pop(removed_element['symbol'], None)
                selected_elements.append(element)
                element_quantities[element['symbol']] = 0
                element_purchase_quantities[element['symbol']] = 0
                feeding_quantities[element['symbol']] = 0
                enlarged_element = element
            else:
                selected_elements.remove(element)
                element_quantities.pop(element['symbol'], None)
                element_purchase_quantities.pop(element['symbol'], None)
                feeding_quantities.pop(element['symbol'], None)
                if enlarged_element == element:
                    enlarged_element = None
            elements_picked = len(selected_elements)
            if pick_sound:
                pick_sound.play()
            return True
    return False

def draw_element_selection_screen():
    screen.fill((0, 0, 0))
    draw_periodic_table()
    
    # Draw selected elements (moved 20px to the right)
    for i, element in enumerate(selected_elements):
        x = width // 2 - 80 + i * 100  # Changed from -100 to -80
        y = height - 170
        pygame.draw.rect(screen, element["color"], (x, y, 80, 80))
        font = pygame.font.Font(None, 36)
        text = font.render(element["symbol"], True, (255, 255, 255))
        screen.blit(text, (x + 20, y + 20))
    
    # Draw CONFIRM button
    button_color = (0, 255, 0) if len(selected_elements) == max_elements else (100, 100, 100)
    confirm_button = pygame.Rect(width - 200, height - 100, 150, 50)
    pygame.draw.rect(screen, button_color, confirm_button)
    font = pygame.font.Font(None, 36)
    text = font.render("CONFIRM", True, (0, 0, 0))
    text_rect = text.get_rect(center=confirm_button.center)
    screen.blit(text, text_rect)

    # Draw instructions
    instruction_font = pygame.font.Font(None, 24)
    instruction_text = f"Select {max_elements} elements. Left click to select. Confirm when done."
    instruction_surface = instruction_font.render(instruction_text, True, (255, 255, 255))
    screen.blit(instruction_surface, (10, 10))

def draw_element_purchase_screen():
    global ore_chunks, element_purchase_quantities, element_quantities
    screen.fill((0, 0, 0))
    font = pygame.font.Font(None, 36)
    y_offset = 50
    
    ore_text = font.render(f"Available ORE: {ore_chunks}", True, (255, 255, 255))
    screen.blit(ore_text, (20, y_offset))
    y_offset += 50

    for element in selected_elements:
        symbol = element['symbol']
        on_hand_quantity = element_quantities.get(symbol, 0)
        purchase_quantity = element_purchase_quantities.get(symbol, 0)
        text = font.render(f"{symbol}: {purchase_quantity}", True, element['color'])
        screen.blit(text, (20, y_offset))
        
        plus_rect = pygame.Rect(200, y_offset, 30, 30)
        minus_rect = pygame.Rect(240, y_offset, 30, 30)
        pygame.draw.rect(screen, (0, 255, 0), plus_rect)
        pygame.draw.rect(screen, (255, 0, 0), minus_rect)
        
        plus_text = font.render("+", True, (0, 0, 0))
        minus_text = font.render("-", True, (0, 0, 0))
        screen.blit(plus_text, (205, y_offset))
        screen.blit(minus_text, (250, y_offset))
        
        # Add slider for quantity selection
        slider_rect = pygame.Rect(300, y_offset, 100, 30)
        pygame.draw.rect(screen, (200, 200, 200), slider_rect)
        slider_fill_rect = pygame.Rect(300, y_offset, purchase_quantity, 30)
        pygame.draw.rect(screen, (0, 255, 0), slider_fill_rect)
        
        # Display current quantity
        quantity_text = font.render(f"{purchase_quantity}", True, (255, 255, 255))
        screen.blit(quantity_text, (410, y_offset))
        
        # Display on-hand quantity
        on_hand_text = font.render(f"On Hand: {on_hand_quantity}", True, (255, 255, 255))
        screen.blit(on_hand_text, (500, y_offset))
        
        y_offset += 50

    confirm_rect = pygame.Rect(width // 2 - 75, height - 100, 150, 50)
    pygame.draw.rect(screen, (0, 255, 0), confirm_rect)
    confirm_text = font.render("Confirm", True, (0, 0, 0))
    screen.blit(confirm_text, (width // 2 - 40, height - 90))

def handle_element_purchase(x, y, button_down):
    global ore_chunks, element_purchase_quantities, purchasing_elements, current_screen, element_quantities
    y_offset = 100
    for element in selected_elements:
        symbol = element['symbol']
        plus_rect = pygame.Rect(200, y_offset, 30, 30)
        minus_rect = pygame.Rect(240, y_offset, 30, 30)
        slider_rect = pygame.Rect(300, y_offset, 100, 30)
        
        if plus_rect.collidepoint(x, y) and ore_chunks > 0:
            if button_down:
                element_purchase_quantities[symbol] += 1
                ore_chunks -= 1
        elif minus_rect.collidepoint(x, y) and element_purchase_quantities[symbol] > 0:
            if button_down:
                element_purchase_quantities[symbol] -= 1
                ore_chunks += 1
        
        if slider_rect.collidepoint(x, y):
            new_quantity = int((x - slider_rect.x) / slider_rect.width * ore_chunks)
            element_purchase_quantities[symbol] = min(new_quantity, ore_chunks)
        
        y_offset += 50
    
    confirm_rect = pygame.Rect(width // 2 - 75, height - 100, 150, 50)
    if confirm_rect.collidepoint(x, y):
        for symbol, quantity in element_purchase_quantities.items():
            if symbol not in element_quantities:
                element_quantities[symbol] = 0
            element_quantities[symbol] += quantity
            element_purchase_quantities[symbol] = 0
        purchasing_elements = False
        current_screen = "main_game"
        save_game()  # This will create a new timestamped save

def handle_feeding_selection(x, y, button_down):
    global feeding_quantities, element_quantities, feeding_elements, current_screen, growth_level, egg_level, lifetime_fed
    y_offset = 50
    for element in selected_elements:
        symbol = element['symbol']
        on_hand_quantity = element_quantities.get(symbol, 0)
        plus_rect = pygame.Rect(200, y_offset, 30, 30)
        minus_rect = pygame.Rect(240, y_offset, 30, 30)
        slider_rect = pygame.Rect(300, y_offset, 100, 30)

        if plus_rect.collidepoint(x, y) and on_hand_quantity > 0:
            if button_down:
                feeding_quantities[symbol] = min(feeding_quantities[symbol] + 1, on_hand_quantity)
        elif minus_rect.collidepoint(x, y) and feeding_quantities[symbol] > 0:
            if button_down:
                feeding_quantities[symbol] -= 1
        elif slider_rect.collidepoint(x, y):
            new_quantity = int((x - slider_rect.x) / slider_rect.width * on_hand_quantity)
            feeding_quantities[symbol] = min(new_quantity, on_hand_quantity)

        y_offset += 50

    confirm_rect = pygame.Rect(width // 2 - 75, height - 100, 150, 50)
    if confirm_rect.collidepoint(x, y):
        total_feed = sum(feeding_quantities.values())
        for symbol, quantity in feeding_quantities.items():
            if quantity > 0:
                element_quantities[symbol] = max(0, element_quantities[symbol] - quantity)
                lifetime_fed[symbol] += quantity
                growth_level += quantity

        while growth_level >= max_growth_per_level:
            egg_level += 1
            growth_level -= max_growth_per_level
            print(f"Egg leveled up to {egg_level}!")  # Add this for debugging

        feeding_elements = False
        current_screen = "main_game"
        save_game()
        print(f"Total feed: {total_feed}, New growth level: {growth_level}")  # Add this for debugging

def draw_feeding_screen():
    global feeding_quantities, element_quantities
    screen.fill((0, 0, 0))
    font = pygame.font.Font(None, 36)
    y_offset = 50

    for element in selected_elements:
        symbol = element['symbol']
        on_hand_quantity = element_quantities.get(symbol, 0)
        if symbol not in feeding_quantities:
            feeding_quantities[symbol] = 0
        
        text = font.render(f"{symbol}: {feeding_quantities[symbol]}", True, element['color'])
        screen.blit(text, (20, y_offset))

        plus_rect = pygame.Rect(200, y_offset, 30, 30)
        minus_rect = pygame.Rect(240, y_offset, 30, 30)
        pygame.draw.rect(screen, (0, 255, 0), plus_rect)
        pygame.draw.rect(screen, (255, 0, 0), minus_rect)

        plus_text = font.render("+", True, (0, 0, 0))
        minus_text = font.render("-", True, (0, 0, 0))
        screen.blit(plus_text, (205, y_offset))
        screen.blit(minus_text, (250, y_offset))

        # Add slider for quantity selection
        slider_rect = pygame.Rect(300, y_offset, 100, 30)
        pygame.draw.rect(screen, (200, 200, 200), slider_rect)
        slider_fill_rect = pygame.Rect(300, y_offset, int(feeding_quantities[symbol] / max(1, on_hand_quantity) * 100), 30)
        pygame.draw.rect(screen, (0, 255, 0), slider_fill_rect)

        # Display current feeding quantity
        quantity_text = font.render(f"{feeding_quantities[symbol]}", True, (255, 255, 255))
        screen.blit(quantity_text, (410, y_offset))

        # Display on-hand quantity
        on_hand_text = font.render(f"On Hand: {on_hand_quantity}", True, (255, 255, 255))
        screen.blit(on_hand_text, (500, y_offset))

        y_offset += 50

    confirm_rect = pygame.Rect(width // 2 - 75, height - 100, 150, 50)
    pygame.draw.rect(screen, (0, 255, 0), confirm_rect)
    confirm_text = font.render("Confirm", True, (0, 0, 0))
    screen.blit(confirm_text, (width // 2 - 40, height - 90))

def redeem_ore_for_elements():
    global ore_chunks, element_quantities
    if not selected_elements:
        print("No elements selected for redemption.")
        return
    
    ore_per_element = ore_chunks // len(selected_elements)
    for element in selected_elements:
        symbol = element['symbol']
        if symbol not in element_quantities:
            element_quantities[symbol] = 0
        element_quantities[symbol] += ore_per_element
    
    ore_chunks -= ore_per_element * len(selected_elements)
    print(f"Redeemed {ore_per_element * len(selected_elements)} ORE for elements.")

def feed_egg():
    global growth_level, element_quantities
    total_feed = sum(element_quantities.values())
    if total_feed > 0:
        growth_level = min(growth_level + total_feed, max_growth_per_level)
        for symbol in element_quantities:
            element_quantities[symbol] = 0
        print(f"Fed egg with {total_feed} elements. New growth level: {growth_level}")
    else:
        print("No elements available to feed the egg.")

def evolve_egg():
    global egg_level, growth_level
    if growth_level >= max_growth_per_level:
        egg_level += 1
        growth_level = 0
        print(f"Egg evolved to level {egg_level}!")
    else:
        print("Not enough growth to evolve!")

def draw_creature():
    global creature_traits
    
    if not creature_displayed or not creature_traits:
        return

    x_center = width // 2
    y_center = height // 2
    
    body_color = creature_traits["color"][0] if creature_traits["color"] else (255, 255, 255)
    body_size = min(creature_traits["size"], 100)  # Cap the size to prevent it from being too large
    pygame.draw.circle(screen, body_color, (x_center, y_center), body_size)
    
    for part in set(creature_traits["body_parts"]):  # Use set to avoid duplicates
        if part == "wings":
            wing_color = creature_traits["color"][1] if len(creature_traits["color"]) > 1 else (200, 200, 200)
            pygame.draw.polygon(screen, wing_color, [(x_center - body_size, y_center - body_size), (x_center, y_center - body_size * 2), (x_center + body_size, y_center - body_size)])
            pygame.draw.polygon(screen, wing_color, [(x_center - body_size, y_center + body_size), (x_center, y_center + body_size * 2), (x_center + body_size, y_center + body_size)])
        if part == "tail":
            tail_color = creature_traits["color"][2] if len(creature_traits["color"]) > 2 else (100, 100, 100)
            pygame.draw.rect(screen, tail_color, (x_center - body_size // 4, y_center + body_size, body_size // 2, body_size))

def draw_main_game_screen():
    screen.fill((0, 0, 0))
    
    if creature_displayed:
        egg_creature.draw(screen)  # This will now use the HatchedCreature class
    else:
        egg_creature.draw(screen)  # Only draw the egg if the creature isn't hatched
    
    # Draw selected elements
    element_width = 80
    element_spacing = 100
    total_elements_width = (len(selected_elements) - 1) * element_spacing + element_width
    start_x = (width - total_elements_width) // 2

    for i, element in enumerate(selected_elements):
        if element is None:
            print(f"Warning: Element with symbol {game_data['selected_elements'][i]} could not be found.")
            continue  # Skip this element if it's invalid

        x = start_x + i * element_spacing
        y = 50
        pygame.draw.rect(screen, element["color"], (x, y, element_width, element_width))
        font = pygame.font.Font(None, 36)
        text = font.render(element["symbol"], True, (255, 255, 255))
        text_rect = text.get_rect(center=(x + element_width // 2, y + element_width // 2))
        screen.blit(text, text_rect)
        quantity_text = font.render(f"{lifetime_fed[element['symbol']]}", True, (255, 255, 255))
        quantity_rect = quantity_text.get_rect(center=(x + element_width // 2, y + element_width + 20))
        screen.blit(quantity_text, quantity_rect)
    
    # Draw buttons
    draw_buttons()
    
    # Draw game info
    font = pygame.font.Font(None, 24)
    emoji_font = pygame.font.Font(font_path, 24)

    texts = [
        f"Egg Level: {egg_level}",
        f"Growth: {growth_level}/{max_growth_per_level}",
        f"Total ORE: {ore_chunks}",
        f"Tokens: {tokens}",
        f"Music: {'ON' if music_on else 'OFF'}",
        f"Theme: {'1' if current_theme == THEME_SONG_1 else '2'}",
        f"Depth: {eat_game.depth if eat_game else '0'}"
    ]
    for i, text in enumerate(texts):
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, (10, 10 + i * 30))

    depth_text = f"Depth: {eat_game.depth if eat_game and eat_game.running_in_background else ''}"
    depth_surface = font.render(depth_text, True, (255, 255, 255))
    screen.blit(depth_surface, (10, 10 + len(texts) * 30))

    if not eat_game or not eat_game.running_in_background:
        no_entry_emoji = emoji_font.render('🚫', True, (255, 255, 255))
        screen.blit(no_entry_emoji, (10 + depth_surface.get_width(), 10 + len(texts) * 30))
    
    pygame.display.flip()

def save_game(game_name=None):
    global current_game_name
    
    if game_name is None:
        if current_game_name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            current_game_name = f"game_{timestamp}"
        game_name = current_game_name
    
    game_data = {
        "ore_chunks": ore_chunks,
        "selected_elements": [e['symbol'] for e in selected_elements],
        "element_quantities": element_quantities,
        "egg_level": egg_level,
        "growth_level": growth_level,
        "tokens": tokens,
        "lifetime_fed": lifetime_fed,
        "music_on": music_on,
        "current_theme": current_theme
    }
    
    if eat_game:
        game_data["eat_game_state"] = {
            "depth": eat_game.depth,
            "score": eat_game.score,
            "creature_stats": {
                "x": eat_game.creature.x,
                "y": eat_game.creature.y,
                "health": eat_game.creature.health,
                "energy": eat_game.creature.energy,
                "size": eat_game.creature.size,
            }
        }
    
    # Load existing saves
    all_saves = load_all_saves()
    
    # Add or update the current save
    all_saves[game_name] = game_data
    
    # Save all games to a single JSON file
    with open("all_saves.json", "w") as f:
        json.dump(all_saves, f)
    
    print(f"Game saved as {game_name}")
    return game_name

def load_game(game_name):
    global ore_chunks, selected_elements, element_quantities, egg_level, growth_level, tokens, lifetime_fed, current_game_name, music_on, current_theme, eat_game, creature_displayed, egg_creature
    
    all_saves = load_all_saves()
    
    if game_name not in all_saves:
        print(f"Save file {game_name} not found.")
        return False
    
    game_data = all_saves[game_name]
    
    ore_chunks = game_data["ore_chunks"]
    selected_elements = [next((e for e in elements if e['symbol'] == symbol), None) for symbol in game_data["selected_elements"]]
    element_quantities = game_data["element_quantities"]
    egg_level = game_data["egg_level"]
    growth_level = game_data["growth_level"]
    tokens = game_data.get("tokens", 0)
    lifetime_fed = game_data.get("lifetime_fed", {element['symbol']: 0 for element in elements})
    music_on = game_data.get("music_on", music_on)
    current_theme = game_data.get("current_theme", current_theme)
    current_game_name = game_name

    # Check if the creature should be displayed
    if egg_level >= 10 and growth_level >= required_growth_level_for_hatching:
        creature_displayed = True
        egg_creature = HatchedCreature(width, height)  # Make sure you have the hatched creature class properly defined
    else:
        creature_displayed = False
        egg_creature = EggCreature(width, height)

    if "eat_game_state" in game_data:
        eat_game_state = game_data["eat_game_state"]
        creature_stats = eat_game_state["creature_stats"]
        eat_game = EatCreatureGame(creature_stats)
        eat_game.depth = eat_game_state["depth"]
        eat_game.score = eat_game_state["score"]
        threading.Thread(target=eat_game.run, daemon=True).start()
    
    start_theme_song()
    check_and_evolve_on_startup()
    return True

def handle_button_click(label):
    global current_screen, eat_game
    if label == "LAB":
        current_screen = "lab"
    elif label == "SLOTS":
        if tokens > 0:
            playing_slot_machine = True
            current_screen = "slot_machine"
        else:
            print("Not enough tokens to play slots!")
    elif label == "PICK":
        current_screen = "element_purchase"
    elif label == "FEED":
        current_screen = "feeding"
    elif label == "EAT":
        if creature_displayed and egg_level >= 10:
            if not eat_game:
                start_eat_creature_minigame()
            current_screen = "eat_creature"
    elif label == "SPIN":
        if not spinning and tokens > 0:
            tokens -= 1
            spin_reels()
    elif label == "BACK":
        current_screen = "main_game"
    elif label == "CONFIRM":
        if elements_picked >= max_elements:
            element_selection_confirmed = True
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            save_game(f"autosave_{timestamp}")

def draw_eat_creature_screen():
    screen.fill((0, 0, 0))
    if eat_game:
        eat_game.draw(screen)
        font = pygame.font.Font(None, 36)
        depth_text = font.render(f"Depth: {eat_game.depth}", True, (255, 255, 255))
        score_text = font.render(f"Score: {eat_game.score}", True, (255, 255, 255))
        screen.blit(depth_text, (10, 10))
        screen.blit(score_text, (10, 50))
    else:
        font = pygame.font.Font(None, 36)
        text = font.render("Creature is not currently exploring", True, (255, 255, 255))
        screen.blit(text, (width // 2 - text.get_width() // 2, height // 2))
    
    back_button = pygame.Rect(width - 110, 10, 100, 50)
    pygame.draw.rect(screen, (255, 0, 0), back_button)
    back_text = font.render("Back", True, (255, 255, 255))
    back_text_rect = back_text.get_rect(center=back_button.center)
    screen.blit(back_text, back_text_rect)

def draw_egg_info():
    font = pygame.font.Font(None, 24)
    texts = [
        f"Egg Level: {egg_level}",
        f"Growth: {growth_level}/{max_growth_per_level}",
    ]
    
    for i, text in enumerate(texts):
        surface = font.render(text, True, (255, 255, 255))
        screen.blit(surface, (10, 10 + i * 30))

def check_egg_evolution():
    global egg_level, growth_level, max_growth_per_level, creature_displayed
    while growth_level >= max_growth_per_level:
        egg_level += 1
        growth_level -= max_growth_per_level
        print(f"Egg evolved to level {egg_level}!")  # Debugging statement
    if egg_level >= 10 and not creature_displayed:
        hatch_creature()

def hatch_creature():
    global selected_elements, lifetime_fed, creature_displayed, creature_traits, egg_creature

    if creature_displayed:
        return  # Prevent repeated hatching

    print("Hatching creature!")
    
    creature_traits = {
        "color": [],
        "size": 5,  # Start with a small size
        "body_parts": []
    }
    
    for element in selected_elements:
        symbol = element["symbol"]
        quantity = lifetime_fed[symbol]
        
        if symbol in ["O", "H", "C"]:
            creature_traits["color"].append((255, 0, 0))
        elif symbol in ["N", "P", "S"]:
            creature_traits["color"].append((0, 255, 0))
        else:
            creature_traits["color"].append((0, 0, 255))
        
        if quantity > 10:
            creature_traits["body_parts"].append("wings")
        if quantity > 5:
            creature_traits["body_parts"].append("tail")

    creature_displayed = True
    egg_creature = HatchedCreature(traits=creature_traits, width=width, height=height)  # Use the new HatchedCreature class
    
    print(f"Creature hatched with traits: {creature_traits}")

def evaluate_spin():
    global ore_chunks
    payout = 0
    
    # Check for other combinations
    for i in range(3):
        symbol = reel_results[i][0]
        if reel_results[i][1] == symbol and reel_results[i][2] == symbol:
            multiplier = 2 if i == 1 else 1  # Double for center line
            payout += payouts.get(symbol, 0) * multiplier
    
    if payout > 0:
        if win_sound:
            win_sound.play()
        ore_chunks += payout
        show_win_message(payout)

def show_win_message(payout):
    font = pygame.font.Font(None, 72)
    text = font.render(f"WINNER! +{payout} ORE", True, (255, 255, 0))
    text_rect = text.get_rect(center=(width // 2, height // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    pygame.time.wait(2000)  # Display the message for 2 seconds

def autosave_game():
    global last_autosave_time
    current_time = time.time()
    if current_time - last_autosave_time >= 60:  # Autosave every 60 seconds
        save_game()
        last_autosave_time = current_time

def save_game(game_name=None):
    global current_game_name, eat_game
    
    if game_name is None:
        if current_game_name is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            current_game_name = f"game_{timestamp}"
        game_name = current_game_name

    if eat_game:
        game_data["eat_game_state"] = {
            "depth": eat_game.depth,
            "score": eat_game.score,
            "creature_stats": {
                "x": eat_game.creature.x,
                "y": eat_game.creature.y,
                "size": eat_game.creature.size,
                "health": eat_game.creature.health,
                "energy": eat_game.creature.energy,
            }
        }
        
    game_data = {
        "ore_chunks": ore_chunks,
        "selected_elements": [e['symbol'] for e in selected_elements],
        "element_quantities": element_quantities,
        "egg_level": egg_level,
        "growth_level": growth_level,
        "tokens": tokens,
        "lifetime_fed": lifetime_fed,
        "music_on": music_on,
        "current_theme": current_theme
    }
    
    # Load existing saves
    all_saves = load_all_saves()
    
    # Add or update the current save
    all_saves[game_name] = game_data
    
    # Save all games to a single JSON file
    with open("all_saves.json", "w") as f:
        json.dump(all_saves, f)
    
    print(f"Game saved as {game_name}")
    return game_name

def load_game(game_name):
    global ore_chunks, selected_elements, element_quantities, egg_level, growth_level, tokens, lifetime_fed, current_game_name, music_on, current_theme, eat_game
    
    all_saves = load_all_saves()
    
    if game_name not in all_saves:
        print(f"Save file {game_name} not found.")
        return False
    
    game_data = all_saves[game_name]
    
    ore_chunks = game_data["ore_chunks"]
    selected_elements = [next((e for e in elements if e['symbol'] == symbol), None) for symbol in game_data["selected_elements"]]
    element_quantities = game_data["element_quantities"]
    egg_level = game_data["egg_level"]
    growth_level = game_data["growth_level"]
    tokens = game_data.get("tokens", 0)
    lifetime_fed = game_data.get("lifetime_fed", {element['symbol']: 0 for element in elements})
    music_on = game_data.get("music_on", music_on)
    current_theme = game_data.get("current_theme", current_theme)
    current_game_name = game_name
    
    if "eat_game_state" in game_data:
        eat_game_state = game_data["eat_game_state"]
        creature_stats = eat_game_state["creature_stats"]
        eat_game = EatCreatureGame(creature_stats)
        eat_game.depth = eat_game_state["depth"]
        eat_game.score = eat_game_state["score"]
        threading.Thread(target=eat_game.run, daemon=True).start()
    
    # Update music state based on loaded preferences
    start_theme_song()
    
    check_and_evolve_on_startup()
    return True

def apply_music_state():
    global music_on
    if music_on:
        pygame.mixer.music.unpause()
    else:
        pygame.mixer.music.pause()

def load_all_saves():
    if not os.path.exists("all_saves.json"):
        return {}
    
    with open("all_saves.json", "r") as f:
        return json.load(f)

def get_saved_games():
    all_saves = load_all_saves()
    return sorted(all_saves.keys(), reverse=True)

def delete_game(game_name):
    all_saves = load_all_saves()
    
    if game_name in all_saves:
        del all_saves[game_name]
        with open("all_saves.json", "w") as f:
            json.dump(all_saves, f)
        print(f"Deleted save: {game_name}")
        return True
    else:
        print(f"Save {game_name} not found.")
        return False

def draw_saved_games_screen():
    screen.fill((0, 0, 0))
    font = pygame.font.Font(None, 36)
    saved_games = get_saved_games()
    
    title_text = font.render("Select a Saved Game or Start a New Game", True, (255, 255, 255))
    screen.blit(title_text, (width // 2 - 200, 50))
    
    for i, game in enumerate(saved_games):
        if i >= 5:  # Limit to displaying only the 5 most recent saves
            break
        display_text = game[:20] + "..." if len(game) > 20 else game  # Truncate long names
        game_rect = pygame.Rect(width // 2 - 150, 150 + i * 60, 250, 50)
        pygame.draw.rect(screen, (0, 255, 0), game_rect)
        game_text = font.render(display_text, True, (0, 0, 0))
        screen.blit(game_text, (width // 2 - 140, 160 + i * 60))

        # Add delete button
        delete_rect = pygame.Rect(width // 2 + 110, 150 + i * 60, 50, 50)
        pygame.draw.rect(screen, (255, 0, 0), delete_rect)
        delete_text = font.render("X", True, (0, 0, 0))
        screen.blit(delete_text, (width // 2 + 130, 160 + i * 60))
    
    new_game_rect = pygame.Rect(width // 2 - 100, height - 100, 200, 50)
    pygame.draw.rect(screen, (0, 255, 0), new_game_rect)
    new_game_text = font.render("New Game", True, (0, 0, 0))
    screen.blit(new_game_text, (width // 2 - 60, height - 90))
    
def create_new_game():
    global current_screen, ore_chunks, selected_elements, element_quantities, egg_level, growth_level, tokens
    ore_chunks = 0
    selected_elements = []
    element_quantities = {}
    egg_level = 1
    growth_level = 0
    tokens = 1  # Give the player 1 token to start
    current_screen = "element_selection"
    save_game()  # Save immediately after creating a new game

def draw_confirmation_dialog(message):
    dialog_rect = pygame.Rect(width // 2 - 150, height // 2 - 75, 300, 150)
    pygame.draw.rect(screen, (200, 200, 200), dialog_rect)
    
    font = pygame.font.Font(None, 24)
    text_surface = font.render(message, True, (0, 0, 0))
    text_rect = text_surface.get_rect(center=(width // 2, height // 2 - 25))
    screen.blit(text_surface, text_rect)
    
    yes_button = pygame.Rect(width // 2 - 110, height // 2 + 25, 100, 40)
    no_button = pygame.Rect(width // 2 + 10, height // 2 + 25, 100, 40)
    
    pygame.draw.rect(screen, (0, 255, 0), yes_button)
    pygame.draw.rect(screen, (255, 0, 0), no_button)
    
    yes_text = font.render("Yes", True, (0, 0, 0))
    no_text = font.render("No", True, (0, 0, 0))
    
    screen.blit(yes_text, (width // 2 - 80, height // 2 + 35))
    screen.blit(no_text, (width // 2 + 40, height // 2 + 35))
    
    return yes_button, no_button

def handle_confirmation_dialog(x, y, message, yes_action):
    yes_button, no_button = draw_confirmation_dialog(message)
    
    if yes_button.collidepoint(x, y):
        yes_action()
        return True
    elif no_button.collidepoint(x, y):
        return True
    
    return False

# Initialize variables
eat_game = None
background_exploration_timer = 0
BACKGROUND_EXPLORATION_INTERVAL = 5000  # Check every 5 seconds

# Define the required growth level for hatching
required_growth_level_for_hatching = 5  # Example value, adjust as needed

# Main game loop
running = True
current_screen = "title"
game_states = ["title", "element_selection", "main_game", "slot_machine", "element_purchase", "feeding", "saved_games", "lab", "eat_creature"]
creature_displayed = False

# Function to check and evolve egg on startup
def check_and_evolve_on_startup():
    global creature_displayed, egg_creature

    # Determine if the egg should hatch based on egg level and growth level
    if egg_level >= 10 and growth_level >= required_growth_level_for_hatching:
        hatch_creature()  # Call the hatch_creature function to perform the hatching process
    else:
        creature_displayed = False
        egg_creature = EggCreature(width, height)  # Continue displaying the egg if not hatched

# Run this check at the start of the game
check_and_evolve_on_startup()

# Initialize music
music_on, current_theme = load_music_preference()
start_theme_song()

running = True
clock = pygame.time.Clock()
fps = 30  # Set to 30 FPS

# Main game loop
while running:
    dt = clock.tick(fps) / 1000.0  # Get time since last frame in seconds
    current_fps = clock.get_fps()

    # Only apply rotation if the creature is still an egg
    if isinstance(egg_creature, EggCreature):
        egg_creature.rotation += egg_creature.rotation_speed * dt * 60  # Multiply by 60 to maintain similar speed at lower FPS
        egg_creature.update()  # Only update the egg creature

    # Global music and theme toggling
    keys = pygame.key.get_pressed()
    if keys[pygame.K_m]:
        toggle_music()
    if keys[pygame.K_t]:
        switch_theme()

    button_down = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if current_screen == "title":
                    running = False
                elif current_screen == "eat_creature":
                    current_screen = "main_game"
                else:
                    current_screen = "title"
            elif event.key == pygame.K_F3:  # Toggle debug mode with F3 key
                debug_mode = not debug_mode
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            print(f"Mouse clicked at: ({x}, {y})")
            if current_screen == "main_game":
                for button in buttons:
                    if button["rect"].collidepoint(x, y):
                        handle_button_click(button["label"])
            elif current_screen == "title":
                if start_button["rect"].collidepoint(x, y):
                    current_screen = "saved_games"
            elif current_screen == "saved_games":
                if confirming_delete:
                    if handle_confirmation_dialog(x, y, f"Delete save {game_to_delete}?", lambda: delete_game(game_to_delete)):
                        confirming_delete = False
                        game_to_delete = None
                else:
                    saved_games = get_saved_games()
                    for i, game in enumerate(saved_games):
                        if i >= 5:  # Limit to checking only the 5 most recent saves
                            break
                        game_rect = pygame.Rect(width // 2 - 150, 150 + i * 60, 250, 50)
                        delete_rect = pygame.Rect(width // 2 + 110, 150 + i * 60, 50, 50)
                        if game_rect.collidepoint(x, y):
                            if load_game(game):
                                current_screen = "main_game"
                                apply_music_state()  # Apply music state after loading game
                        elif delete_rect.collidepoint(x, y):
                            confirming_delete = True
                            game_to_delete = game
                    new_game_rect = pygame.Rect(width // 2 - 100, height - 100, 200, 50)
                    if new_game_rect.collidepoint(x, y):
                        create_new_game()
            elif current_screen == "element_selection":
                if handle_element_selection(x, y):
                    continue
                if confirm_button.collidepoint(x, y) and len(selected_elements) == max_elements:
                    current_screen = "main_game"
            elif current_screen == "lab":
                if event.button == 1:  # Left click
                    handle_lab_interaction(event.pos[0], event.pos[1])
                elif event.button == 3:  # Right click
                    handle_lab_interaction(event.pos[0], event.pos[1], right_click=True)
            elif current_screen == "slot_machine":
                if spin_button.collidepoint(x, y) and not spinning and tokens > 0:
                    tokens -= 1
                    spin_reels()
                elif back_button.collidepoint(x, y):
                    current_screen = "main_game"
            elif current_screen == "element_purchase":
                handle_element_purchase(x, y, button_down)
            elif current_screen == "feeding":
                handle_feeding_selection(x, y, button_down)
                check_egg_evolution()  # Ensure this is called after feeding
            elif current_screen == "eat_creature":
                back_button = pygame.Rect(width - 110, 10, 100, 50)
                if back_button.collidepoint(x, y):
                    current_screen = "main_game"
        elif event.type == pygame.MOUSEBUTTONUP:
            button_down = False
        elif event.type == pygame.MOUSEWHEEL:
            x, y = pygame.mouse.get_pos()
            if current_screen == "element_purchase":
                if event.y > 0:
                    handle_element_purchase(x, y, True)
                else:
                    handle_element_purchase(x, y, False)
            elif current_screen == "feeding":
                if event.y > 0:
                    handle_feeding_selection(x, y, True)
                else:
                    handle_feeding_selection(x, y, False)
                
    screen.fill((0, 0, 0))  # Clear screen with black background

    # Check on background exploration
    if eat_game and eat_game.running_in_background:
        ore_chunks += eat_game.score
        tokens += eat_game.depth
        eat_game.score = 0  # Reset score after collecting

    if current_screen == "title":
        draw_title_screen()
    elif current_screen == "saved_games":
        draw_saved_games_screen()
        if confirming_delete:
            draw_confirmation_dialog(f"Delete save {game_to_delete}?")
    elif current_screen == "element_selection":
        draw_element_selection_screen()
    elif current_screen == "slot_machine":
        draw_slot_machine()
        if spinning:
            update_spinning_reels()
    elif current_screen == "element_purchase":
        draw_element_purchase_screen()
    elif current_screen == "feeding":
        draw_feeding_screen()
    elif current_screen == "lab":
        draw_lab_screen()
    elif current_screen == "main_game":
        apply_music_state()  # Ensure music state is applied when entering main game screen
        draw_main_game_screen()
    elif current_screen == "eat_creature":
        if eat_game:
            eat_game.draw(screen)
            back_button = pygame.Rect(width - 110, 10, 100, 50)
            pygame.draw.rect(screen, (255, 0, 0), back_button)
            font = pygame.font.Font(None, 36)
            back_text = font.render("Back", True, (255, 255, 255))
            back_text_rect = back_text.get_rect(center=back_button.center)
            screen.blit(back_text, back_text_rect)

            # Handle RECALL button click
            recall_button = pygame.Rect(WIDTH - 120, HEIGHT - 60, 100, 50)
            if event.type == pygame.MOUSEBUTTONDOWN and recall_button.collidepoint(event.pos):
                eat_game.recall_creature()
                current_screen = "main_game"
        else:
            font = pygame.font.Font(None, 36)
            text = font.render("Creature is not currently exploring", True, (255, 255, 255))
            screen.blit(text, (width // 2 - text.get_width() // 2, height // 2))

    draw_debug_overlay(current_fps)  # Draw debug information
    
    autosave_game()
    
    pygame.display.flip()

pygame.quit()
sys.exit()
