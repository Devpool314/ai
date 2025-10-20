import pygame
from settings import *

class Ghost:
    def __init__(self, game, pos, color):
        self.game = game
        self.grid_pos = pygame.Vector2(pos)
        self.pix_pos = pygame.Vector2(self.grid_pos.x * TILE_SIZE, self.grid_pos.y * TILE_SIZE)
        self.direction = pygame.Vector2(1, 0) 
        self.speed = 1
        self.color = color
        

    def update(self):
        next_grid_pos = self.grid_pos + self.direction
        current_maze_width = self.game.maze.tile_width
        current_maze_height = self.game.maze.tile_height

        if not (0 <= next_grid_pos.x < current_maze_width and \
                0 <= next_grid_pos.y < current_maze_height and \
                self.game.maze.map_data[int(next_grid_pos.y)][int(next_grid_pos.x)] != '%'):
            self.direction *= -1

        self.pix_pos += self.direction * self.speed
        if self.time_to_move():
            self.pix_pos.x = round(self.pix_pos.x / TILE_SIZE) * TILE_SIZE
            self.pix_pos.y = round(self.pix_pos.y / TILE_SIZE) * TILE_SIZE
            self.grid_pos[0] = self.pix_pos[0] // TILE_SIZE
            self.grid_pos[1] = self.pix_pos[1] // TILE_SIZE

    def draw(self):
        pygame.draw.circle(self.game.screen, self.color, 
                           (int(self.pix_pos.x) + TILE_SIZE // 2, int(self.pix_pos.y) + TILE_SIZE // 2), 
                           TILE_SIZE // 2 - 2)
    
    def time_to_move(self):
        margin = self.speed / 2
        if self.pix_pos.x % TILE_SIZE < margin and self.pix_pos.y % TILE_SIZE < margin:
            return True
        return False
