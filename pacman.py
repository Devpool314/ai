import pygame
from settings import *
import random
import time

class Pacman:
    def __init__(self, game, pos):
        self.game = game
        self.grid_pos = pygame.Vector2(pos)
        self.pix_pos = pygame.Vector2(self.grid_pos.x * TILE_SIZE, self.grid_pos.y * TILE_SIZE)
        self.direction = pygame.Vector2(0, 0)
        self.stored_direction = None
        self.speed = 4
        self.power_up_timer = 0
        self.last_teleport_time = 0
        self.teleport_flash_duration = 0.1  # giây
        self.step_count = 0 
        self.just_powered_up = False
        

    def update(self):
        if self.can_change_direction():
            if self.stored_direction and self.can_move_in_direction(self.stored_direction):
                self.direction = self.stored_direction
                self.stored_direction = None
            elif not self.can_move_in_direction(self.direction):
                self.direction = pygame.Vector2(0, 0)

        self.pix_pos += self.direction * self.speed
        
        if self.pix_pos.x > self.game.maze.width:
            self.pix_pos.x = -TILE_SIZE
        elif self.pix_pos.x < -TILE_SIZE:
            self.pix_pos.x = self.game.maze.width
            
        new_grid_pos = pygame.Vector2(
            round(self.pix_pos.x / TILE_SIZE),
            round(self.pix_pos.y / TILE_SIZE)
        )

        if new_grid_pos != self.grid_pos:
            last_grid_pos = self.grid_pos
            self.grid_pos = new_grid_pos

            y, x = int(self.grid_pos.y), int(self.grid_pos.x)
            if 0 <= y < len(self.game.maze.map_data):
                row = self.game.maze.map_data[y]
                if 0 <= x < len(row):
                    current_tile_char = row[x]
                    if current_tile_char == '.':
                        self.game.maze.remove_food(self.grid_pos)
                    elif current_tile_char == 'O':
                        self.game.maze.remove_food(self.grid_pos)
                        self.power_up_timer = 5

            if self.power_up_timer > 0 and self.grid_pos != last_grid_pos:
                self.power_up_timer -= 1

            self.step_count += 1
            if not hasattr(self.game, "real_path"):
                self.game.real_path = []

            if self.direction.x == 1:
                self.game.real_path.append("East")
            elif self.direction.x == -1:
                self.game.real_path.append("West")
            elif self.direction.y == -1:
                self.game.real_path.append("North")
            elif self.direction.y == 1:
                self.game.real_path.append("South")

            if self.step_count % 30 == 0:
                try:
                    self.game.maze.rotate_maze_90_right(
                        pacman=self,
                        ghosts=getattr(self.game, "ghosts", None)
                    )

                    self.game.screen = pygame.display.set_mode(
                        (self.game.maze.width, self.game.maze.height)
                    )

                    self.pix_pos = self.grid_pos * TILE_SIZE

                    if not self.can_move_in_direction(self.direction):
                        reverse_dir = self.direction * -1
                        if self.can_move_in_direction(reverse_dir):
                            self.direction = reverse_dir
                        else:
                            self.direction = pygame.Vector2(0, 0)

                except Exception as e:
                    print(f"[WARN] Maze rotation failed safely: {e}")

            # === TELEPORT GÓC ===
            def find_corner(start_x, start_y, dx, dy):
                height = len(self.game.maze.map_data)
                width = max(len(r) for r in self.game.maze.map_data)

                for offset_y in range(0, height):
                    for offset_x in range(0, width):
                        x = start_x + dx * offset_x
                        y = start_y + dy * offset_y
                        if not (0 <= int(y) < height):
                            continue
                        row = self.game.maze.map_data[int(y)]
                        if not (0 <= int(x) < len(row)):
                            continue
                        if row[int(x)] != '%':
                            return pygame.Vector2(x, y)
                return pygame.Vector2(start_x, start_y)

            top_left = find_corner(0, 0, +1, +1)
            top_right = find_corner(self.game.maze.tile_width - 1, 0, -1, +1)
            bottom_left = find_corner(0, self.game.maze.tile_height - 1, +1, -1)
            bottom_right = find_corner(self.game.maze.tile_width - 1, self.game.maze.tile_height - 1, -1, -1)
            corners = [top_left, top_right, bottom_left, bottom_right]

            for corner in corners:
                if self.grid_pos == corner:
                    possible_targets = [c for c in corners if c != corner]
                    target = random.choice(possible_targets)

                    move_dir = self.direction if self.direction.length() > 0 else pygame.Vector2(0, 0)

                    self.grid_pos = target
                    self.pix_pos = pygame.Vector2(target.x * TILE_SIZE, target.y * TILE_SIZE)
                    self.last_teleport_time = time.time()

                    if not self.can_move_in_direction(move_dir):
                        move_dir *= -1
                        if not self.can_move_in_direction(move_dir):
                            move_dir = pygame.Vector2(0, 0)

                    is_auto = getattr(self.game, "auto_mode", False) or getattr(self.game, "game_state", "") in ["auto", "playing_auto"]
                    if is_auto:
                        self.direction = pygame.Vector2(0, 0)
                    else:
                        self.direction = move_dir
                    break

    def draw(self):
        now = time.time()
        is_flashing = (now - self.last_teleport_time) < self.teleport_flash_duration

        if is_flashing:
            color = (255, 255, 180)
        elif self.power_up_timer > 0:
            color = (255, 0, 0)
        else:
            color = YELLOW

        pygame.draw.circle(
            self.game.screen,
            color,
            (int(self.pix_pos.x) + TILE_SIZE // 2, int(self.pix_pos.y) + TILE_SIZE // 2),
            TILE_SIZE // 2 - 2
        )

    def move(self, direction):
        self.stored_direction = direction

    def can_change_direction(self):
        if abs(self.pix_pos.x % TILE_SIZE - 0) < self.speed or abs(self.pix_pos.x % TILE_SIZE - TILE_SIZE) < self.speed:
            if abs(self.pix_pos.y % TILE_SIZE - 0) < self.speed or abs(self.pix_pos.y % TILE_SIZE - TILE_SIZE) < self.speed:
                self.pix_pos.x = round(self.pix_pos.x / TILE_SIZE) * TILE_SIZE
                self.pix_pos.y = round(self.pix_pos.y / TILE_SIZE) * TILE_SIZE
                return True
        return False

    def can_move_in_direction(self, direction):
        if direction is None or (direction.x == 0 and direction.y == 0):
            return False
        next_grid_pos = self.grid_pos + direction
        y, x = int(next_grid_pos.y), int(next_grid_pos.x)
        if not (0 <= y < len(self.game.maze.map_data)):
            return False
        row = self.game.maze.map_data[y]
        if not (0 <= x < len(row)):
            return False
        if self.power_up_timer > 0:
            return True
        return row[x] != '%'
    def at_center_of_tile(self):
        TILE = TILE_SIZE if 'TILE_SIZE' in globals() else 24
        cx = self.grid_pos.x * TILE + TILE / 2
        cy = self.grid_pos.y * TILE + TILE / 2
        return abs(self.pix_pos.x - cx) < 2 and abs(self.pix_pos.y - cy) < 2
