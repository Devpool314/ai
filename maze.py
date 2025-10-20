import pygame
from settings import *

class Maze:
    def __init__(self, filepath):
        self.map_data = []
        with open(filepath, 'r') as f:
            for line in f:
                self.map_data.append(line.strip())

        self.tile_width = len(self.map_data[0])
        self.tile_height = len(self.map_data)
        self.width = self.tile_width * TILE_SIZE
        self.height = self.tile_height * TILE_SIZE

    def draw(self, surface):
        for row_idx, row in enumerate(self.map_data):
            for col_idx, tile in enumerate(row):
                x = col_idx * TILE_SIZE
                y = row_idx * TILE_SIZE
                if tile == '%':  # Tường
                    pygame.draw.rect(surface, BLUE, (x, y, TILE_SIZE, TILE_SIZE))
                elif tile == '.':  
                    pygame.draw.circle(surface, WHITE, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), 4)
                elif tile == 'O': 
                    pygame.draw.circle(surface, WHITE, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), 8)
                elif tile == 'E':  
                    GREEN = (0, 200, 0)
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(surface, GREEN, rect) 

    def remove_food(self, pos):
        x, y = int(pos[0]), int(pos[1])
        if 0 <= y < len(self.map_data) and 0 <= x < len(self.map_data[y]):
            row = list(self.map_data[y])
            row[x] = ' '  
            self.map_data[y] = "".join(row)

    def rotate_maze_90_right(self, pacman=None, ghosts=None):

        if not self.map_data:
            print("[WARN] Maze empty, cannot rotate.")
            return

        max_len = max(len(row) for row in self.map_data)
        normalized = [row.ljust(max_len, '%') for row in self.map_data]

        old_height = len(normalized)

        rotated = ["".join(row) for row in zip(*normalized[::-1])]
        self.map_data = rotated

        for i,row in enumerate(self.map_data):
            self.map_data[i] = row.replace('P',' ').replace('G',' ')

        self.tile_width, self.tile_height = self.tile_height, self.tile_width
        self.width = self.tile_width * TILE_SIZE
        self.height = self.tile_height * TILE_SIZE

        if pacman is not None:
            x, y = int(pacman.grid_pos.x), int(pacman.grid_pos.y)
            new_x = old_height - 1 - y
            new_y = x
            # Kẹp để tránh vượt giới hạn
            new_x = max(0, min(new_x, self.tile_width - 1))
            new_y = max(0, min(new_y, self.tile_height - 1))
            pacman.grid_pos = pygame.Vector2(new_x, new_y)
            pacman.pix_pos = pacman.grid_pos * TILE_SIZE

            if pacman.direction.length() > 0:
                old_dir = pacman.direction
                pacman.direction = pygame.Vector2(-old_dir.y, old_dir.x)

        if ghosts is not None:
            for g in ghosts:
                x, y = int(g.grid_pos.x), int(g.grid_pos.y)
                new_x = old_height - 1 - y
                new_y = x
                new_x = max(0, min(new_x, self.tile_width - 1))
                new_y = max(0, min(new_y, self.tile_height - 1))
                g.grid_pos = pygame.Vector2(new_x, new_y)
                g.pix_pos = g.grid_pos * TILE_SIZE

                if hasattr(g, "direction"):
                    old_dir = g.direction
                    g.direction = pygame.Vector2(-old_dir.y, old_dir.x)
