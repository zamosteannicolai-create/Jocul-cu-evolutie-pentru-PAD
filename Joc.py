import tkinter as tk
from tkinter import messagebox, colorchooser
import math
import random
import json
import os
import time

WIDTH = 1200
HEIGHT = 700
TARGET_FPS = 60
DT = 1.0 / TARGET_FPS

NUM_SLOTS = 3
PROGRESS_FILE_TEMPLATE = "progress_slot_{}.json"
CONTROLS_FILE = "controls.json"
SETTINGS_FILE = "settings.json"

DEFAULT_CONTROLS = {
    "move_up": "w",
    "move_down": "s",
    "move_left": "a",
    "move_right": "d",
    "shoot": "space",
    "pause": "Escape",
    "dash": "Shift_L",
}

ACTIONS_INFO = {
    "move_up": "Mișcare sus",
    "move_down": "Mișcare jos",
    "move_left": "Mișcare stânga",
    "move_right": "Mișcare dreapta",
    "shoot": "Trage (spre mouse)",
    "pause": "Pauză / Meniu pauză",
    "dash": "Dash spre mouse",
}

# Dificultăți – multiplicatori
DIFFICULTIES = {
    "Easy": {"hp": 0.8, "dmg": 0.8, "spd": 0.9, "xp": 1.2},
    "Normal": {"hp": 1.0, "dmg": 1.0, "spd": 1.0, "xp": 1.0},
    "Hard": {"hp": 1.3, "dmg": 1.2, "spd": 1.05, "xp": 1.3},
    "Insane": {"hp": 1.7, "dmg": 1.6, "spd": 1.1, "xp": 1.6},
    "Nightmare": {"hp": 2.2, "dmg": 2.0, "spd": 1.15, "xp": 2.0},
}

DEFAULT_SETTINGS = {
    "full_screen": True,
    "radar_enabled": True,
    "tutorial_enabled": True,
    "player_color_main": "#65E572",
    "player_color_glow": "#282C55",
}

BOSS_NAMES = {
    "boss_ice": "ICE BOSS",
    "boss_fire": "FIRE BOSS",
    "boss_jump": "JUMPING BOSS",
    "boss_poison": "POISON BOSS",
    "boss_storm": "STORM BOSS",
    "boss_shadow": "SHADOW BOSS",
    "boss_crystal": "CRYSTAL BOSS",
    "boss_demon": "DEMON BOSS",
    "boss_mech": "MECH BOSS",
    "boss_ancient": "ANCIENT BOSS",
}


# ==================== PROGRES PERMANENT ====================


class PermanentProgress:
    def __init__(self, slot_index: int):
        self.slot_index = slot_index
        self.file_path = PROGRESS_FILE_TEMPLATE.format(slot_index)

        self.player_level = 1
        self.total_xp = 0
        self.xp_to_next_level = 100

        self.unlocked_classes = ["warrior"]
        self.selected_class = "warrior"

        self.permanent_upgrades = {
            "health": 0,
            "damage": 0,
            "speed": 0,
            "energy": 0,
            "regen": 0,
            "bullet_speed": 0,
            "bullet_size": 0,
            "critical_chance": 0,
            "dodge_chance": 0,
        }

        self.skills_unlocked = {
            "double_shot": False,
            "poison_bullets": False,
            "freeze_bullets": False,
            "explosive_bullets": False,
            "life_steal": False,
        }

        self.total_play_time = 0
        self.total_kills = 0
        self.total_damage = 0
        self.highest_wave = 0
        self.games_played = 0

        # dificultate salvată pe slot
        self.difficulty_name = "Normal"

        # pentru tutorial simplu
        self.tutorial_seen = False

        # mid-run save simplu (wave și level)
        self.last_run = None

        self.load()

    def add_run_stats(self, play_time, kills, damage, wave):
        self.total_play_time += play_time
        self.total_kills += kills
        self.total_damage += damage
        self.highest_wave = max(self.highest_wave, wave)
        self.games_played += 1

    def add_xp(self, amount):
        self.total_xp += amount
        leveled_up = False
        while self.total_xp >= self.xp_to_next_level:
            self.total_xp -= self.xp_to_next_level
            self.player_level += 1
            # fallback calcul xp_to_next_level
            self.xp_to_next_level = int(self.x_to_next_level() * 1.4)
            leveled_up = True
            self._unlock_classes()
        return leveled_up

    # mic fix: metodă de fallback
    def x_to_next_level(self):
        return self.xp_to_next_level

    def _unlock_classes(self):
        if self.player_level >= 3 and "archer" not in self.unlocked_classes:
            self.unlocked_classes.append("archer")
        if self.player_level >= 5 and "mage" not in self.unlocked_classes:
            self.unlocked_classes.append("mage")
        if self.player_level >= 8 and "tank" not in self.unlocked_classes:
            self.unlocked_classes.append("tank")
        if self.player_level >= 12 and "assassin" not in self.unlocked_classes:
            self.unlocked_classes.append("assassin")

    def buy_upgrade(self, key, cost):
        if self.total_xp >= cost:
            self.total_xp -= cost
            self.permanent_upgrades[key] += 1
            return True
        return False

    def buy_skill(self, key, cost, required_level):
        if self.skills_unlocked.get(key, False):
            return False, "Abilitatea este deja deblocată!"
        if self.player_level < required_level:
            return False, f"Ai nevoie de nivel {required_level}!"
        if self.total_xp < cost:
            return False, "Nu ai suficient XP!"
        self.total_xp -= cost
        self.skills_unlocked[key] = True
        return True, "Abilitate deblocată!"

    def save_mid_run(self, wave, player_level, player_xp, player_hp_ratio):
        self.last_run = {
            "wave": wave,
            "player_level": player_level,
            "player_xp": player_xp,
            "player_hp_ratio": player_hp_ratio,
        }
        self.save()

    def clear_last_run(self):
        self.last_run = None
        self.save()

    def save(self):
        data = {
            "player_level": self.player_level,
            "total_xp": self.total_xp,
            "xp_to_next_level": self.xp_to_next_level,
            "unlocked_classes": self.unlocked_classes,
            "selected_class": self.selected_class,
            "permanent_upgrades": self.permanent_upgrades,
            "skills_unlocked": self.skills_unlocked,
            "total_play_time": self.total_play_time,
            "total_kills": self.total_kills,
            "total_damage": self.total_damage,
            "highest_wave": self.highest_wave,
            "games_played": self.games_played,
            "difficulty_name": self.difficulty_name,
            "tutorial_seen": self.tutorial_seen,
            "last_run": self.last_run,
        }
        try:
            with open(self.file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Error saving progress:", e)

    def load(self):
        if not os.path.exists(self.file_path):
            return
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
            self.player_level = data.get("player_level", 1)
            self.total_xp = data.get("total_xp", 0)
            self.xp_to_next_level = data.get("xp_to_next_level", 100)
            self.unlocked_classes = data.get("unlocked_classes", ["warrior"])
            self.selected_class = data.get("selected_class", "warrior")
            self.permanent_upgrades = data.get(
                "permanent_upgrades", self.permanent_upgrades
            )
            self.skills_unlocked = data.get("skills_unlocked", self.skills_unlocked)
            self.total_play_time = data.get("total_play_time", 0)
            self.total_kills = data.get("total_kills", 0)
            self.total_damage = data.get("total_damage", 0)
            self.highest_wave = data.get("highest_wave", 0)
            self.games_played = data.get("games_played", 0)
            self.difficulty_name = data.get("difficulty_name", "Normal")
            self.tutorial_seen = data.get("tutorial_seen", False)
            self.last_run = data.get("last_run", None)
        except Exception as e:
            print("Error loading progress:", e)


# ==================== CLASE DE JUCĂTOR ====================


class PlayerClass:
    def __init__(self, class_type, perm: PermanentProgress):
        self.type = class_type
        p = perm.permanent_upgrades

        if class_type == "warrior":
            self.base_health = 120 + p["health"] * 15
            self.base_speed = 220 + p["speed"] * 6
            self.base_damage = 15 + p["damage"] * 3
            self.base_energy = 80 + p["energy"] * 8
            self.color = "#FF6B81"
            self.bullet_speed = 520 + p["bullet_speed"] * 16
            self.bullet_size = 8 + p["bullet_size"] * 0.6
            self.crit = 0.10 + p["critical_chance"] * 0.02
            self.dodge = 0.05 + p["dodge_chance"] * 0.02
        elif class_type == "archer":
            self.base_health = 90 + p["health"] * 10
            self.base_speed = 260 + p["speed"] * 7
            self.base_damage = 12 + p["damage"] * 2
            self.base_energy = 110 + p["energy"] * 9
            self.color = "#65E572"
            self.bullet_speed = 640 + p["bullet_speed"] * 20
            self.bullet_size = 6 + p["bullet_size"] * 0.4
            self.crit = 0.16 + p["critical_chance"] * 0.03
            self.dodge = 0.10 + p["dodge_chance"] * 0.03
        elif class_type == "mage":
            self.base_health = 75 + p["health"] * 8
            self.base_speed = 210 + p["speed"] * 5
            self.base_damage = 20 + p["damage"] * 4
            self.base_energy = 140 + p["energy"] * 10
            self.color = "#AA7FF7"
            self.bullet_speed = 500 + p["bullet_speed"] * 16
            self.bullet_size = 10 + p["bullet_size"] * 0.7
            self.crit = 0.20 + p["critical_chance"] * 0.04
            self.dodge = 0.08 + p["dodge_chance"] * 0.025
        elif class_type == "tank":
            self.base_health = 180 + p["health"] * 18
            self.base_speed = 180 + p["speed"] * 4
            self.base_damage = 12 + p["damage"] * 2
            self.base_energy = 70 + p["energy"] * 7
            self.color = "#9E9E9E"
            self.bullet_speed = 460 + p["bullet_speed"] * 14
            self.bullet_size = 11 + p["bullet_size"] * 0.8
            self.crit = 0.08 + p["critical_chance"] * 0.02
            self.dodge = 0.03 + p["dodge_chance"] * 0.015
        else:  # assassin
            self.base_health = 65 + p["health"] * 7
            self.base_speed = 280 + p["speed"] * 8
            self.base_damage = 18 + p["damage"] * 3
            self.base_energy = 100 + p["energy"] * 8
            self.color = "#FF9E43"
            self.bullet_speed = 680 + p["bullet_speed"] * 22
            self.bullet_size = 5 + p["bullet_size"] * 0.3
            self.crit = 0.25 + p["critical_chance"] * 0.05
            self.dodge = 0.16 + p["dodge_chance"] * 0.04


# ==================== SISTEM DE PARTICULE SIMPLU ====================


class ParticleSystem:
    def __init__(self, canvas, max_particles=250):
        self.canvas = canvas
        self.max = max_particles
        self.particles = []

    def spawn_explosion(self, x, y, color, count=10, speed=120, life=0.7):
        for _ in range(min(count, self.max)):
            angle = random.uniform(0, 2 * math.pi)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(2, 5)
            self.particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": vx,
                    "vy": vy,
                    "size": size,
                    "color": color,
                    "life": life,
                    "age": 0,
                }
            )

    def update(self, dt):
        alive = []
        for p in self.particles:
            p["age"] += dt
            if p["age"] >= p["life"]:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            alive.append(p)
        self.particles = alive

    def draw(self):
        c = self.canvas
        for p in self.particles:
            s = p["size"] * max(0.3, 1 - p["age"] / p["life"])
            c.create_oval(
                p["x"] - s,
                p["y"] - s,
                p["x"] + s,
                p["y"] + s,
                fill=p["color"],
                outline="",
                tags="particle",
            )


# ==================== ENEMY & WAVE SYSTEM ====================


def get_boss_type_for_wave(wave):
    idx = wave // 10
    types = [
        "boss_ice",
        "boss_fire",
        "boss_jump",
        "boss_poison",
        "boss_storm",
        "boss_shadow",
        "boss_crystal",
        "boss_demon",
        "boss_mech",
        "boss_ancient",
    ]
    if idx - 1 < len(types):
        return types[idx - 1]
    return "boss_mech"


class Enemy:
    def __init__(self, x, y, etype, wave_scale, diff_cfg):
        self.x = x
        self.y = y
        self.type = etype

        base_hp = 40
        base_speed = 90
        base_dmg = 8
        color = "#FF6B6B"
        r = 16

        if etype == "normal":
            base_hp = 40
            base_speed = 90
            base_dmg = 8
            color = "#FF6B6B"
            r = 16
        elif etype == "fast":
            base_hp = 25
            base_speed = 145
            base_dmg = 6
            color = "#FFC061"
            r = 13
        elif etype == "strong":
            base_hp = 80
            base_speed = 70
            base_dmg = 12
            color = "#E84141"
            r = 20
        elif etype == "runner":
            base_hp = 35
            base_speed = 170
            base_dmg = 7
            color = "#FF9E43"
            r = 14
        elif etype == "spinner":
            base_hp = 50
            base_speed = 110
            base_dmg = 9
            color = "#66D9FF"
            r = 18
        elif etype == "exploder":
            base_hp = 30
            base_speed = 100
            base_dmg = 16
            color = "#FF4F91"
            r = 16
        elif etype == "mini_boss":
            base_hp = 350
            base_speed = 80
            base_dmg = 20
            color = "#B025FF"
            r = 42
        elif etype.startswith("boss_"):
            r = 58
            base_speed = 70
            base_dmg = 28
            if etype == "boss_ice":
                base_hp = 650
                color = "#6DD5FF"
            elif etype == "boss_fire":
                base_hp = 700
                color = "#FF5E3A"
            elif etype == "boss_jump":
                base_hp = 720
                color = "#FFD93A"
            elif etype == "boss_poison":
                base_hp = 750
                color = "#9BFF6D"
            elif etype == "boss_storm":
                base_hp = 780
                color = "#83AFFF"
            elif etype == "boss_shadow":
                base_hp = 820
                color = "#2B2B3C"
            elif etype == "boss_crystal":
                base_hp = 850
                color = "#D7B9FF"
            elif etype == "boss_demon":
                base_hp = 900
                color = "#D72638"
            elif etype == "boss_mech":
                base_hp = 950
                color = "#A5A5A5"
            elif etype == "boss_ancient":
                base_hp = 1300
                color = "#000000"
                r = 70

        hp_scale = (1 + (wave_scale - 1) * 0.5) * diff_cfg["hp"]
        dmg_scale = (1 + (wave_scale - 1) * 0.4) * diff_cfg["dmg"]
        spd_scale = (1 + (wave_scale - 1) * 0.1) * diff_cfg["spd"]

        self.radius = r
        self.speed = base_speed * spd_scale
        self.max_health = base_hp * hp_scale
        self.damage = base_dmg * dmg_scale
        self.color = color
        self.health = self.max_health

        if etype.startswith("boss_") or etype == "mini_boss":
            self.special_timer = random.uniform(2.0, 4.0)
        else:
            self.special_timer = None

        self.jump_cooldown = random.uniform(3.0, 5.0) if etype == "boss_jump" else None

        if etype.startswith("boss_"):
            self.xp_value = 300
        elif etype == "mini_boss":
            self.xp_value = 120
        else:
            self.xp_value = 10 + wave_scale * 2

    def move_towards(self, px, py, dt):
        dx = px - self.x
        dy = py - self.y
        dist = math.hypot(dx, dy) or 1
        nx, ny = dx / dist, dy / dist
        self.x += nx * self.speed * dt
        self.y += ny * self.speed * dt

    def hit(self, dmg):
        self.health -= dmg
        return self.health <= 0


class WaveManager:
    def __init__(self):
        self.current_wave = 1
        self.spawn_queue = []
        self.time_between_spawns = 0.4
        self.spawn_timer = 0

    def start_wave(self, wave_number):
        self.current_wave = wave_number
        self.spawn_queue = []

        base = 5 + (wave_number - 1) * 2
        fast = max(0, wave_number - 2)
        strong = max(0, wave_number - 4)
        runner = max(0, wave_number - 6)
        spinner = max(0, wave_number - 8)
        exploder = max(0, wave_number - 10)

        for _ in range(base):
            self.spawn_queue.append("normal")
        for _ in range(min(fast, 5 + wave_number)):
            self.spawn_queue.append("fast")
        for _ in range(min(strong, 3 + wave_number // 2)):
            self.spawn_queue.append("strong")
        for _ in range(min(runner, 3 + wave_number // 2)):
            self.spawn_queue.append("runner")
        for _ in range(min(spinner, 2 + wave_number // 3)):
            self.spawn_queue.append("spinner")
        for _ in range(min(exploder, 2 + wave_number // 3)):
            self.spawn_queue.append("exploder")

        if wave_number % 5 == 0:
            self.spawn_queue.append("mini_boss")
        if wave_number % 10 == 0:
            self.spawn_queue.append(get_boss_type_for_wave(wave_number))

        random.shuffle(self.spawn_queue)
        self.spawn_timer = 1.0

    def update(self, dt, game):
        self.spawn_timer -= dt
        spawned = []
        while self.spawn_timer <= 0 and self.spawn_queue:
            etype = self.spawn_queue.pop(0)
            x, y = game.random_spawn_point()
            wave_scale = self.current_wave
            enemy = Enemy(x, y, etype, wave_scale, game.difficulty_cfg)
            spawned.append(enemy)
            self.spawn_timer += self.time_between_spawns
        return spawned

    def is_wave_cleared(self, enemies):
        return not enemies and not self.spawn_queue


# ==================== PLAYER ====================


class Player:
    def __init__(self, x, y, pclass: PlayerClass, perm: PermanentProgress, skills):
        self.x = x
        self.y = y
        self.radius = 25
        self.class_data = pclass
        self.color = pclass.color

        self.max_health = pclass.base_health
        self.health = self.max_health
        self.base_speed = pclass.base_speed
        self.speed = pclass.base_speed
        self.base_damage = pclass.base_damage
        self.energy = pclass.base_energy
        self.max_energy = pclass.base_energy

        self.bullet_speed = pclass.bullet_speed
        self.bullet_size = pclass.bullet_size
        self.critical_chance = pclass.crit
        self.dodge_chance = pclass.dodge

        self.skills = skills
        self.life_steal = 0.10 if skills.get("life_steal") else 0.0

        self.bullets = []
        self.shoot_cooldown = 0.0
        self.shoot_delay = 0.18

        self.xp = 0
        self.level = 1
        self.xp_to_next = 40

        self.kill_count = 0
        self.total_damage = 0

        self.dash_cooldown = 0.0

    def move(self, dx, dy, dt, speed_factor=1.0):
        if dx != 0 and dy != 0:
            l = math.hypot(dx, dy)
            dx /= l
            dy /= l
        self.x += dx * self.speed * speed_factor * dt
        self.y += dy * self.speed * speed_factor * dt

        self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(HEIGHT - self.radius, self.y))

    def shoot(self, tx, ty):
        if self.shoot_cooldown > 0:
            return

        angle = math.atan2(ty - self.y, tx - self.x)
        bx = self.x + math.cos(angle) * (self.radius + 4)
        by = self.y + math.sin(angle) * (self.radius + 4)

        is_crit = random.random() < self.critical_chance
        damage = self.base_damage * (2.0 if is_crit else 1.0)

        bullet = {
            "x": bx,
            "y": by,
            "vx": math.cos(angle) * self.bullet_speed,
            "vy": math.sin(angle) * self.bullet_speed,
            "r": self.bullet_size,
            "damage": damage,
            "crit": is_crit,
        }

        self.bullets.append(bullet)

        if self.skills.get("double_shot") and random.random() < 0.3:
            angle2 = angle + random.uniform(-0.18, 0.18)
            bx2 = self.x + math.cos(angle2) * (self.radius + 4)
            by2 = self.y + math.sin(angle2) * (self.radius + 4)
            b2 = bullet.copy()
            b2["x"] = bx2
            b2["y"] = by2
            b2["vx"] = math.cos(angle2) * self.bullet_speed
            b2["vy"] = math.sin(angle2) * self.bullet_speed
            self.bullets.append(b2)

        self.shoot_cooldown = self.shoot_delay

    def update(self, dt):
        self.shoot_cooldown = max(0.0, self.shoot_cooldown - dt)
        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + 10 * dt)
        if self.health < self.max_health:
            self.health = min(self.max_health, self.health + 1.5 * dt)

        if self.dash_cooldown > 0:
            self.dash_cooldown = max(0.0, self.dash_cooldown - dt)

        alive = []
        for b in self.bullets:
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            if -50 < b["x"] < WIDTH + 50 and -50 < b["y"] < HEIGHT + 50:
                alive.append(b)
        self.bullets = alive

    def gain_xp(self, amt):
        self.xp += amt
        leveled = False
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self.level += 1
            self.xp_to_next = int(self.xp_to_next * 1.5)
            leveled = True
        return leveled


# ==================== GAME COMPLET ====================


class CellEvolutionGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cell Evolution - Cartoon Edition")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.resizable(True, True)

        self.canvas = tk.Canvas(
            self.root,
            width=WIDTH,
            height=HEIGHT,
            bg="#1a1a2e",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.settings = {}
        self.load_settings()

        if self.settings.get("full_screen", True):
            self.root.attributes("-fullscreen", True)

        self.state = "main_menu"
        self.current_slot = 1

        self.controls = {}
        self.load_controls()
        self.waiting_for_control = None

        self.progress = PermanentProgress(self.current_slot)
        self.current_difficulty_name = self.progress.difficulty_name
        self.difficulty_cfg = DIFFICULTIES.get(
            self.current_difficulty_name, DIFFICULTIES["Normal"]
        )

        self.player = None
        self.wave_manager = WaveManager()
        self.enemies = []
        self.particles = ParticleSystem(self.canvas)
        self.hazards = []
        self.loot = []

        self.powerups_active = {
            "speed": 0.0,
            "rapid_fire": 0.0,
            "shield": 0.0,
        }

        self.keys = set()
        self.mouse_pos = (WIDTH // 2, HEIGHT // 2)
        self.mouse_down = False

        self.last_time = time.perf_counter()
        self.fps = 0
        self._fps_counter = 0
        self._fps_time = time.perf_counter()

        self.run_start_time = 0
        self.run_wave = 1
        self.campaign_won = False
        self.endless_mode = False
        self.resumed_this_session = False

        self.level_up_choices = []
        self.level_up_open = False

        self.show_tutorial_overlay = False

        self.background_blobs = []
        self.randomize_background()

        # timer wave + rage mode
        self.wave_time_elapsed = 0.0
        self.wave_time_limit = 30.0
        self.wave_announce_timer = 0.0
        self.rage_triggered = False
        self.rage_text_timer = 0.0

        # știm dacă am intrat în setări din joc
        self.settings_from_game = False

        self.setup_bindings()
        self.show_main_menu()
        self.game_loop()

        self.root.mainloop()

    # -------- BACKGROUND --------
    def randomize_background(self):
        self.background_blobs = [
            (
                random.randint(-100, WIDTH + 100),
                random.randint(-100, HEIGHT + 100),
                random.randint(80, 160),
            )
            for _ in range(20)
        ]

    # -------- SETTINGS SAVE/LOAD --------
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = DEFAULT_SETTINGS.copy()
        else:
            self.settings = DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, "w") as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print("Error saving settings:", e)

    # -------- CONTROLS SAVE/LOAD --------
    def load_controls(self):
        if os.path.exists(CONTROLS_FILE):
            try:
                with open(CONTROLS_FILE, "r") as f:
                    self.controls = json.load(f)
            except Exception:
                self.controls = DEFAULT_CONTROLS.copy()
        else:
            self.controls = DEFAULT_CONTROLS.copy()
        for k, v in DEFAULT_CONTROLS.items():
            if k not in self.controls:
                self.controls[k] = v

    def save_controls(self):
        try:
            with open(CONTROLS_FILE, "w") as f:
                json.dump(self.controls, f, indent=2)
        except Exception as e:
            print("Error saving controls:", e)

    def is_action_down(self, action):
        key = self.controls.get(action)
        return key in self.keys

    # ------------- BINDINGS ------------->
def setup_bindings(self):
        self.root.bind("<KeyPress>", self.on_key_down)
        self.root.bind("<KeyRelease>", self.on_key_up)
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)

    def toggle_fullscreen(self):
        current = bool(self.root.attributes("-fullscreen"))
        self.root.attributes("-fullscreen", not current)
        self.settings["full_screen"] = not current
        self.save_settings()

    def on_key_down(self, e):
        k = e.keysym

        # F11 toggle fullscreen
        if k == "F11":
            self.toggle_fullscreen()
            return

        # dacă alegem o tastă pentru un control
        if self.waiting_for_control is not None:
            if k == "Escape":
                self.waiting_for_control = None
                self.draw_settings_menu()
                return
            self.controls[self.waiting_for_control] = k
            self.save_controls()
            self.waiting_for_control = None
            self.draw_settings_menu()
            return

        # logica pe state
        if self.state == "main_menu":
            if k == "Return":
                self.state = "class_select"
                self.draw_class_select()
            elif k == "Escape" or k == self.controls.get("pause", "Escape"):
                self.exit_game()

        elif self.state in (
            "class_select",
            "upgrades",
            "stats",
            "slot_select",
            "difficulty_select",
        ):
            if k == "Escape":
                self.show_main_menu()

        elif self.state == "settings":
            if k == "Escape":
                if self.settings_from_game:
                    # revenim în pauză, nu în meniu
                    self.state = "paused"
                    self.draw_game(paused=True)
                else:
                    self.show_main_menu()
                self.settings_from_game = False

        elif self.state == "playing":
            if k == self.controls.get("pause", "Escape"):
                self.state = "paused"
            if k == self.controls.get("shoot", "space") and self.player:
                self.player.shoot(*self.mouse_pos)
            if k == self.controls.get("dash", "Shift_L"):
                self.perform_dash()

        elif self.state == "paused":
            if k == self.controls.get("pause", "Escape"):
                self.state = "playing"
            elif k.lower() == "m":
                self.show_main_menu()
            elif k.lower() == "s":
                # deschide setările din joc
                self.settings_from_game = True
                self.state = "settings"
                self.draw_settings_menu()

        elif self.state in ("game_over", "campaign_won"):
            if k in ("Return", "space"):
                self.show_main_menu()

        self.keys.add(k)

    def on_key_up(self, e):
        k = e.keysym
        if k in self.keys:
            self.keys.remove(k)

    def on_mouse_down(self, e):
        self.mouse_down = True
        self.mouse_pos = (e.x, e.y)
        if self.state == "playing" and self.player:
            self.player.shoot(e.x, e.y)
        if self.state in ("game_over", "campaign_won"):
            self.show_main_menu()

    def on_mouse_up(self, e):
        self.mouse_down = False

    def on_mouse_move(self, e):
        self.mouse_pos = (e.x, e.y)

    # ------------- MAIN MENU -------------
    def show_main_menu(self):
        self.state = "main_menu"

        self.canvas.delete("all")
        self.draw_main_menu()

    def draw_main_menu(self):
        self.canvas.delete("all")

        self.canvas.create_rectangle(
            0, 0, WIDTH, HEIGHT, fill="#1B1F3B", outline=""
        )
        for (bx, by, r) in self.background_blobs:
            self.canvas.create_oval(
                bx - r,
                by - r,
                bx + r,
                by + r,
                fill="#262B4D",
                outline="",
            )

        self.canvas.create_text(
            WIDTH // 2,
            90,
            text="CELL EVOLUTION",
            fill="#FFCC66",
            font=("Arial", 56, "bold"),
        )
        self.canvas.create_text(
            WIDTH // 2,
            135,
            text="Supraviețuiește • Evoluează • Domină",
            fill="#FFFFFF",
            font=("Arial", 18, "italic"),
        )

        p = self.progress
        self.canvas.create_text(
            WIDTH // 2,
            180,
            text=(
                f"Slot {self.current_slot} | Dif: {self.current_difficulty_name} | "
                f"Nivel cont: {p.player_level}   XP: {p.total_xp}/{p.xp_to_next_level}"
            ),
            fill="#FFD700",
            font=("Arial", 18, "bold"),
        )

        self.draw_main_menu_buttons()

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 30,
            text="ENTER - Start | ESC - Iesire | F11 - Fullscreen",
            fill="#bbbbbb",
            font=("Arial", 12),
        )

    def draw_main_menu_buttons(self):
        btn_data = [
            ("START JOC", self.go_to_class_select),
            ("SCHIMBĂ SLOT + DIFICULTATE", self.go_to_slot_select),
            ("UPGRADE-URI PERMANENTE", self.go_to_upgrades),
            ("STATISTICI", self.go_to_stats),
            ("SETĂRI", self.go_to_settings),
            ("IESIRE", self.exit_game),
        ]
        w, h = 420, 60
        start_y = 220
        self.menu_buttons = []

        for i, (text, cmd) in enumerate(btn_data):
            y = start_y + i * 70
            x1 = WIDTH // 2 - w // 2
            y1 = y
            x2 = WIDTH // 2 + w // 2
            y2 = y + h
            rect = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#373B69",
                outline="#FFCC66",
                width=3,
                tags=("menu_button",),
            )
            self.canvas.create_text(
                (x1 + x2) // 2,
                (y1 + y2) // 2,
                text=text,
                fill="#ffffff",
                font=("Arial", 20, "bold"),
                tags=("menu_button",),
            )
            self.menu_buttons.append((rect, cmd))

        self.canvas.tag_bind("menu_button", "<Button-1>", self.on_main_menu_click)

    def on_main_menu_click(self, event):
        x, y = event.x, event.y
        for rect, cmd in self.menu_buttons:
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= x <= x2 and y1 <= y <= y2:
                cmd()
                break

    def go_to_class_select(self):
        self.state = "class_select"
        self.draw_class_select()

    def go_to_upgrades(self):
        self.state = "upgrades"
        self.draw_upgrade_menu()

    def go_to_stats(self):
        self.state = "stats"
        self.draw_stats_menu()

    def go_to_settings(self):
        self.state = "settings"
        self.draw_settings_menu()

    def go_to_slot_select(self):
        self.state = "slot_select"
        self.draw_slot_select()

    def exit_game(self):
        self.progress.save()
        self.root.destroy()

    # -------- SLOT & DIFFICULTY SELECT --------
    def read_slot_summary(self, idx):
        path = PROGRESS_FILE_TEMPLATE.format(idx)
        if not os.path.exists(path):
            return {"exists": False}
        try:
            with open(path, "r") as f:
                d = json.load(f)
            return {
                "exists": True,
                "level": d.get("player_level", 1),
                "xp": d.get("total_xp", 0),
                "xp_next": d.get("xp_to_next_level", 100),
                "games": d.get("games_played", 0),
                "wave": d.get("highest_wave", 0),
                "diff": d.get("difficulty_name", "Normal"),
            }
        except Exception:
            return {"exists": False}

    def draw_slot_select(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            WIDTH // 2,
            70,
            text="ALEGE SLOTUL DE SALVARE",
            fill="#FFCC66",
            font=("Arial", 32, "bold"),
        )

        self.slot_buttons = []
        w = 320
        h = 120
        start_y = 160
        gap = 40

        for i in range(1, NUM_SLOTS + 1):
            summary = self.read_slot_summary(i)
            y = start_y + (i - 1) * (h + gap)
            x1 = WIDTH // 2 - w // 2
            y1 = y
            x2 = WIDTH // 2 + w // 2
            y2 = y + h
            rect = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#373B69",
                outline="#FFCC66",
                width=3,
                tags=("slot_button",),
            )
            if summary["exists"]:

                text1 = f"SLOT {i} - Nivel {summary['level']} | Wave max {summary['wave']}"
                text2 = (
                    f"Jocuri: {summary['games']}  XP: {summary['xp']}/{summary['xp_next']} | "
                    f"Dif: {summary['diff']}"
                )
            else:
                text1 = f"SLOT {i} - GOL"
                text2 = "Se va crea când începi un joc pe acest slot."
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 35,
                text=text1,
                fill="#ffffff",
                font=("Arial", 14, "bold"),
                tags=("slot_button",),
            )
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 75,
                text=text2,
                fill="#cccccc",
                font=("Arial", 11),
                tags=("slot_button",),
            )
            self.slot_buttons.append((rect, i))

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 40,
            text="ESC - Înapoi la meniu",
            fill="#888888",
            font=("Arial", 12),
        )

        self.canvas.tag_bind("slot_button", "<Button-1>", self.on_slot_click)

    def on_slot_click(self, event):
        x, y = event.x, event.y
        for rect, idx in self.slot_buttons:
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.current_slot = idx
                self.progress = PermanentProgress(self.current_slot)
                self.current_difficulty_name = self.progress.difficulty_name
                self.difficulty_cfg = DIFFICULTIES.get(
                    self.current_difficulty_name, DIFFICULTIES["Normal"]
                )
                self.state = "difficulty_select"
                self.draw_difficulty_select()
                break

    def draw_difficulty_select(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            WIDTH // 2,
            80,
            text=f"SLOT {self.current_slot}: ALEGE DIFICULTATEA",
            fill="#FFCC66",
            font=("Arial", 26, "bold"),
        )
        line = "Easy  |  Normal  |  Hard  |  Insane  |  Nightmare"
        self.canvas.create_text(
            WIDTH // 2,
            120,
            text=line,
            fill="#ffffff",
            font=("Arial", 12),
        )

        self.diff_buttons = []
        names = list(DIFFICULTIES.keys())
        w = 180
        h = 70
        start_x = 140
        y = 220
        gap = 40
        for i, name in enumerate(names):
            x1 = start_x + i * (w + gap)
            y1 = y
            x2 = x1 + w
            y2 = y1 + h
            col = "#64ff64" if name == self.current_difficulty_name else "#FFCC66"
            rect = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#373B69",
                outline=col,
                width=3,
                tags=("diff_button",),
            )
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 22,
                text=name,
                fill="#ffffff",
                font=("Arial", 14, "bold"),
                tags=("diff_button",),
            )
            desc = ""
            if name == "Easy":
                desc = "Inamici mai slabi, XP bonus."
            elif name == "Normal":
                desc = "Experiență standard."
            elif name == "Hard":
                desc = "Inamici mai tari, XP extra."
            elif name == "Insane":
                desc = "Foarte greu, XP mare."
            elif name == "Nightmare":
                desc = "Pentru nebuni. Succes."
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 45,
                text=desc,
                fill="#dddddd",
                font=("Arial", 8),
                tags=("diff_button",),
            )
            self.diff_buttons.append((rect, name))

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 60,
            text="CLICK pe dificultate pentru a o salva pentru acest slot.",
            fill="#bbbbbb",
            font=("Arial", 11),
        )
        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 30,
            text="ESC - Înapoi la meniu principal",
            fill="#888888",
            font=("Arial", 12),
        )

        self.canvas.tag_bind("diff_button", "<Button-1>", self.on_diff_click)

    def on_diff_click(self, event):
        x, y = event.x, event.y
        for rect, name in self.diff_buttons:
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.current_difficulty_name = name
                self.progress.difficulty_name = name
                self.progress.save()
                self.difficulty_cfg = DIFFICULTIES.get(
                    name, DIFFICULTIES["Normal"]
                )
                self.show_main_menu()
                break

    # ------------- CLASS SELECT -------------
    def draw_class_select(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            WIDTH // 2,
            70,
            text="SELECTEAZĂ CLASA",
            fill="#FFCC66",
            font=("Arial", 36, "bold"),
        )
        p = self.progress

        classes = [
            (
                "Războinic",
                "warrior",
                "#FF6B81",
                "Clasă de bază, echilibrată.\nBun la început, rezistent.",
                "Deblocare: disponibil din start.",
            ),
            (
                "Arcaș",
                "archer",
                "#65E572",
                "Rapid, proiectile rapide, crit mare.",
                "Deblocare: atinge nivel de cont 3.",
            ),
            (
                "Vrăjitor",
                "mage",
                "#AA7FF7",
                "Damage mare, energie multă.",
                "Deblocare: atinge nivel de cont 5.",
            ),
            (
                "Tank",
                "tank",
                "#9E9E9E",
                "Viață uriașă, merge încet.",
                "Deblocare: supraviețuiește până la wave 10.",
            ),
            (
                "Asasin",
                "assassin",
                "#FF9E43",
                "Super rapid, crit imens, dar fragil.",
                "Deblocare: atinge nivel de cont 12.",
            ),
        ]

        start_x = 80
        start_y = 140
        w = 210
        h = 200
        gap = 20
        self.class_buttons = []

        for i, (name, ctype, col, desc, unlock_info) in enumerate(classes):
            x1 = start_x + i * (w + gap)
            y1 = start_y
            x2 = x1 + w
            y2 = y1 + h
            locked = ctype not in p.unlocked_classes
            outline = "#aaaaaa" if locked else col

            rect = self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill="#373B69",
                outline=outline,
                width=3,
                tags=("class_button",),
            )
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 24,
                text=name,
                fill=col if not locked else "#888888",
                font=("Arial", 14, "bold"),
                tags=("class_button",),
            )
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 68,
                text=desc,
                fill="#ffffff",
                font=("Arial", 9),
                width=w - 10,
                tags=("class_button",),
            )
            self.canvas.create_text(
                (x1 + x2) // 2,
                y1 + 122,
                text=unlock_info,
                fill="#FFD700" if locked else "#64ff64",
                font=("Arial", 9),
                width=w - 10,
                tags=("class_button",),
            )
            info_text = "BLOCAȚI" if locked else "CLICK pentru a juca"
            col2 = "#ff5555" if locked else "#64ff64"
            self.canvas.create_text(
                (x1 + x2) // 2,
                y2 - 16,
                text=info_text,
                fill=col2,
                font=("Arial", 10, "bold"),
                tags=("class_button",),
            )

            self.class_buttons.append((rect, ctype, locked, unlock_info))

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 40,
            text="ESC - Înapoi la meniu",
            fill="#888888",
            font=("Arial", 12),
        )

        self.canvas.tag_bind("class_button", "<Button-1>", self.on_class_click)

    def on_class_click(self, event):
        x, y = event.x, event.y
        for rect, ctype, locked, unlock_info in self.class_buttons:
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= x <= x2 and y1 <= y <= y2:
                if locked:
                    messagebox.showinfo("Clasă blocată", unlock_info)
                else:
                    self.progress.selected_class = ctype
                    self.progress.save()
                    self.start_game()
                break

    # ------------- UPGRADE MENU -------------
    def draw_upgrade_menu(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            WIDTH // 2,
            60,
            text="UPGRADE-URI PERMANENTE",
            fill="#FFCC66",
            font=("Arial", 32, "bold"),
        )
        p = self.progress
        self.canvas.create_text(
            WIDTH // 2,
            100,
            text=f"XP disponibil: {p.total_xp}",
            fill="#64ff64",
            font=("Arial", 18, "bold"),
        )
        bar_w = 400
        progress_ratio = p.total_xp / max(1, p.xp_to_next_level)
        self.canvas.create_rectangle(
            WIDTH // 2 - bar_w // 2,
            130,
            WIDTH // 2 + bar_w // 2,
            145,
            fill="#333333",
            outline="",
        )
        self.canvas.create_rectangle(
            WIDTH // 2 - bar_w // 2,
            130,
            WIDTH // 2 - bar_w // 2 + bar_w * progress_ratio,
            145,
            fill="#6495ED",
            outline="",
        )

        upgrades = [
            ("Viață+", "health", 50, "+15 viață maximă"),
            ("Damage+", "damage", 50, "+3 daune"),
            ("Viteză+", "speed", 50, "+6 viteză"),
            ("Energie+", "energy", 50, "+8 energie"),
            ("Regen+", "regen", 80, "+regenerare mică/sec"),
            ("Viteză glonț", "bullet_speed", 60, "+viteză proiectile"),
            ("Mărime glonț", "bullet_size", 70, "+mărime proiectile"),
            ("Șansă Critic", "critical_chance", 100, "+crit"),
            ("Șansă Dodge", "dodge_chance", 120, "+evitare damage"),
        ]

        start_y = 180
        self.upgrade_buttons = []
        for i, (name, key, cost, desc) in enumerate(upgrades):
            y = start_y + i * 45
            lvl = p.permanent_upgrades.get(key, 0)
            can = p.total_xp >= cost
            col = "#64ff64" if can else "#777777"
            rect = self.canvas.create_rectangle(
                120,
                y - 18,
                WIDTH - 120,
                y + 18,
                fill="#373B69",
                outline=col,
                width=2,
                tags=("upgrade_button",),
            )
            self.canvas.create_text(
                140,
                y,
                text=f"{name} (lvl {lvl})",
                fill="#ffffff",
                font=("Arial", 12),
                anchor="w",
                tags=("upgrade_button",),
            )
            self.canvas.create_text(
                WIDTH - 140,
                y,
                text=f"Cost: {cost} XP",
                fill=col,
                font=("Arial", 12),
                anchor="e",
                tags=("upgrade_button",),
            )
            self.canvas.create_text(
                WIDTH // 2,
                y + 16,
                text=desc,
                fill="#bbbbbb",
                font=("Arial", 9),
                tags=("upgrade_button",),
            )
            self.upgrade_buttons.append((rect, key, cost))

        self.canvas.create_text(
            WIDTH // 2,
            600,
            text="ABILITĂȚI SPECIALE (se deblochează cu XP)",
            fill="#FFD700",
            font=("Arial", 16, "bold"),
        )

        skills = [
            ("DOUBLE SHOT", "double_shot", 200, "30% șansă de 2 proiectile", 3),
            ("POISON", "poison_bullets", 300, "Damage peste timp (viitor)", 7),
            ("FREEZE", "freeze_bullets", 400, "Încetinește inamicii (viitor)", 10),
            ("EXPLOSIVE", "explosive_bullets", 500, "Explozie la impact (viitor)", 13),
            ("LIFE STEAL", "life_steal", 600, "10% din damage -> viață", 15),
        ]
        self.skill_buttons = []
        sx = 60
        sy = 630
        for i, (name, key, cost, desc, req_lvl) in enumerate(skills):
            x = sx + i * 220
            rect = self.canvas.create_rectangle(
                x,
                sy,
                x + 200,
                sy + 60,
                fill="#373B69",
                outline="#9370DB",
                width=2,
                tags=("skill_button",),
            )
            unlocked = p.skills_unlocked.get(key, False)
            if unlocked:
                status = "DEBLOCAT"
                col = "#64ff64"
            else:
                status = f"Lvl {req_lvl} | {cost}XP"
                col = "#FFCC00" if p.player_level >= req_lvl else "#777777"

            self.canvas.create_text(
                x + 100,
                sy + 16,
                text=name,
                fill="#ffffff",
                font=("Arial", 11, "bold"),
                tags=("skill_button",),
            )
            self.canvas.create_text(
                x + 100,
                sy + 32,
                text=status,
                fill=col,
                font=("Arial", 9),
                tags=("skill_button",),
            )
            self.canvas.create_text(
                x + 100,
                sy + 48,
                text=desc,
                fill="#bbbbbb",
                font=("Arial", 8),
                tags=("skill_button",),
            )
            self.skill_buttons.append((rect, key, cost, req_lvl))

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 20,
            text="ESC - Înapoi la meniu",
            fill="#888888",
            font=("Arial", 12),
        )

        self.canvas.tag_bind("upgrade_button", "<Button-1>", self.on_upgrade_click)
        self.canvas.tag_bind("skill_button", "<Button-1>", self.on_skill_click)

    def on_upgrade_click(self, event):
        x, y = event.x, event.y
        p = self.progress
        for rect, key, cost in self.upgrade_buttons:
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= x <= x2 and y1 <= y <= y2:
                if p.buy_upgrade(key, cost):
                    p.save()
                    self.draw_upgrade_menu()
                else:
                    messagebox.showwarning("Nu ai destul XP", "Mai trebuie XP!")
                break

    def on_skill_click(self, event):
        x, y = event.x, event.y
        p = self.progress
        for rect, key, cost, req_lvl in self.skill_buttons:
            x1, y1, x2, y2 = self.canvas.coords(rect)
            if x1 <= x <= x2 and y1 <= y <= y2:
                ok, msg = p.buy_skill(key, cost, req_lvl)
                if ok:
                    p.save()
                    self.draw_upgrade_menu()
                else:
                    messagebox.showwarning("Nu poți cumpăra", msg)
                break

    # ------------- STATS & SETTINGS -------------
    def draw_stats_menu(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            WIDTH // 2,
            60,
            text="STATISTICI",
            fill="#FFCC66",
            font=("Arial", 32, "bold"),
        )
        p = self.progress

        lines = [
            f"Slot curent: {self.current_slot}",
            f"Dificultate: {self.current_difficulty_name}",
            f"Nivel cont: {p.player_level}",
            f"XP total: {p.total_xp} / {p.xp_to_next_level}",
            f"Jocuri jucate: {p.games_played}",
            f"Timp total jucat: {int(p.total_play_time)} sec",
            f"Ucideri totale: {p.total_kills}",
            f"Damage total dat: {int(p.total_damage)}",
            f"Wave maxim atins: {p.highest_wave}",
        ]

        for i, line in enumerate(lines):
            self.canvas.create_text(
                WIDTH // 2,
                130 + i * 40,
                text=line,
                fill="#ffffff",
                font=("Arial", 16),
            )

        self.canvas.create_text(
            WIDTH // 2,
            HEIGHT - 40,
            text="ESC - Înapoi la meniu",
            fill="#888888",
            font=("Arial", 12),
        )

    def draw_settings_menu(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            WIDTH // 2,
            60,
            text="SETĂRI",
            fill="#FFCC66",
            font=("Arial", 32, "bold"),
        )

        # CONTROALE
        self.canvas.create_text(
            WIDTH // 2,
            110,
            text="CONTROALE",
            fill="#FFD700",
            font=("Arial", 20, "bold"),
        )

        self.control_buttons = []
        start_y = 150
        for i, (action, label) in enumerate(ACTIONS_INFO.items()):
            y = start_y + i * 40
            x1 = 40
            x2 = WIDTH // 2 - 20
            rect = self.canvas.create_rectangle(
                x1,
                y - 14,
                x2,
                y + 14,
                fill="#373B69",
                outline="#FFCC66",
                width=2,
                tags=("control_button",),
            )
            key = self.controls.get(action, "?")
            self.canvas.create_text(
                x1 + 10,
                y,
                text=label,
                fill="#ffffff",
                font=("Arial", 10),
                anchor="w",
                tags=("control_button",),
            )
            self.canvas.create_text(
                x2 - 10,
                y,
                text=f"Tastă: {key}",
                fill="#64ff64",
                font=("Arial", 10),
                anchor="e",
                tags=("control_button",),
            )
            self.control_buttons.append((rect, action))

        self.canvas.tag_bind("control_button", "<Button-1>", self.on_control_click)

        # GRAFICĂ & GAMEPLAY
        self.canvas.create_text(
            3 * WIDTH // 4,
            110,
            text="GRAFICĂ & GAMEPLAY",
            fill="#FFD700",
            font=("Arial", 20, "bold"),
        )

        self.setting_buttons = []

        gfx_y = 150
        items = [
            ("Fullscreen", "full_screen"),
            ("Radar mini-map", "radar_enabled"),
            ("Tutorial la început", "tutorial_enabled"),
        ]
        for i, (label, key) in enumerate(items):
            y = gfx_y + i * 40
            x1 = WIDTH // 2 + 20
            x2 = WIDTH - 40
            rect = self.canvas.create_rectangle(
                x1,
                y - 14,
                x2,
                y + 14,
                fill="#373B69",
                outline="#FFCC66",
                width=2,
                tags=("setting_toggle",),
            )
            val = self.settings.get(key, DEFAULT_SETTINGS.get(key, False))
            txt = "ON" if val else "OFF"
            col = "#64ff64" if val else "#ff6666"
            self.canvas.create_text(
                x1 + 10,
                y,
                text=label,
                fill="#ffffff",
                font=("Arial", 10),
                anchor="w",
                tags=("setting_toggle",),
            )
            self.canvas.create_text(
                x2 - 10,
                y,
                text=txt,
                fill=col,
                font=("Arial", 10, "bold"),
                anchor="e",
                tags=("setting_toggle",),
            )
            self.setting_buttons.append((rect, key))

        self.canvas.tag_bind("setting_toggle", "<Button-1>", self.on_setting_toggle)

