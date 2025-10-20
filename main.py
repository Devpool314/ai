import pygame
import sys
from settings import *
from maze import Maze
from pacman import Pacman
from ghost import Ghost
from search import PacmanSearchProblem, a_star_search
import random

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pacman AI Project")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("comicsansms", 50)
        self.font_small = pygame.font.SysFont("comicsansms", 24)
        
        self.game_state = 'menu'
        self.maze = None
        self.pacman = None
        self.problem = None
        self.ghosts = []
        self.step_counter = 0
        self.score = 0
        
        try:
            self.load_initial_data()
        except Exception as e:
            print(f"ERR: {e}")
            pygame.quit(); sys.exit()
        
        try:
            temp_maze = Maze('maps/task02_pacman_example_map.txt') 
            
            self.screen = pygame.display.set_mode((temp_maze.width, temp_maze.height))
            
            self.load_initial_data() 
            
        except Exception as e:
            print(f"ERR: {e}")
            pygame.quit(); sys.exit()

        pygame.display.set_caption("Pacman AI Project")

    def load_initial_data(self):
        self.maze = Maze('maps/task02_pacman_example_map.txt')
        self.maze.game = self 
        self.problem = PacmanSearchProblem(self.maze)
        self.ghosts = []
        ghost_positions = self.problem._find_all_chars_in_maze('G')
        ghost_colors = [(255,184,222), (255,0,0), (0,255,255), (255,184,82)]
        for i, pos in enumerate(ghost_positions):
            color = ghost_colors[i % len(ghost_colors)]
            self.ghosts.append(Ghost(self, pos, color))

    def reset_pacman(self):
        self.step_counter = 0
        self.load_initial_data()
        start_pos = self.problem.get_start_state()[0]
        if not start_pos: raise ValueError("ERR: Not found Pacman 'P'.")
        self.pacman = Pacman(self, start_pos)

    def run(self):
        while True:
            if self.game_state == 'menu': self.run_menu()
            elif self.game_state == 'playing_manual': self.run_manual_mode()
            elif self.game_state == 'playing_auto': self.run_auto_mode()
            elif self.game_state == 'game_over': self.run_game_over()

    def run_menu(self):
        manual_text = self.font_big.render("MANUAL MODE", True, WHITE)
        manual_rect = manual_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 50))
        auto_text = self.font_big.render("AUTO MODE (A*)", True, WHITE)
        auto_rect = auto_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50))
        
        current_width = self.screen.get_width()
        current_height = self.screen.get_height()

        manual_text = self.font_big.render("MANUAL MODE", True, WHITE)
        manual_rect = manual_text.get_rect(center=(current_width/2, current_height/2 - 50)) 
        
        auto_text = self.font_big.render("AUTO MODE (A*)", True, WHITE)
        auto_rect = auto_text.get_rect(center=(current_width/2, current_height/2 + 50))
        
        while self.game_state == 'menu':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if manual_rect.collidepoint(mouse_pos): self.reset_pacman(); self.game_state = 'playing_manual'
                    elif auto_rect.collidepoint(mouse_pos): self.reset_pacman(); self.game_state = 'playing_auto'
            self.screen.fill(BLACK); self.screen.blit(manual_text, manual_rect); self.screen.blit(auto_text, auto_rect)
            pygame.display.flip(); self.clock.tick(15)

    def run_manual_mode(self):
        while self.game_state == 'playing_manual':
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.game_state = 'menu'
                    if event.key == pygame.K_LEFT: self.pacman.move(pygame.Vector2(-1, 0))
                    if event.key == pygame.K_RIGHT: self.pacman.move(pygame.Vector2(1, 0))
                    if event.key == pygame.K_UP: self.pacman.move(pygame.Vector2(0, -1))
                    if event.key == pygame.K_DOWN: self.pacman.move(pygame.Vector2(0, 1))

            self.pacman.update()
            for ghost in self.ghosts: ghost.update()
            
            if self.check_victory_condition():
                return

            if self.pacman.power_up_timer == 0:
                for ghost in self.ghosts:
                    if ghost.grid_pos == self.pacman.grid_pos:
                        self.game_state = 'game_over'
                        break
            
            self.draw("Mode: Manual | Press ESC for Menu")
            self.clock.tick(60)
            
    def run_auto_mode(self):
        self.draw("Calculating (replanning realtime)...")
        if not self.pacman:
            self.reset_pacman()
        max_iterations = 10000
        iters = 0
        
        direction_stats = {'North': 0, 'South': 0, 'East': 0, 'West': 0, 'Stop': 0}
        total_steps = 0
        total_cost = 0

        while self.game_state == 'playing_auto' and iters < max_iterations:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.game_state = 'menu'
                    return

            ghost_near = any(
                abs(int(self.pacman.grid_pos.x) - int(g.grid_pos.x)) +
                abs(int(self.pacman.grid_pos.y) - int(g.grid_pos.y)) <= 3
                for g in self.ghosts
            )

            if self.pacman.can_change_direction() or ghost_near:
                if self.pacman.just_powered_up:
                    self.pacman.just_powered_up = False
                cur_pos = (int(self.pacman.grid_pos.x), int(self.pacman.grid_pos.y))
                food_list = []
                for y, row in enumerate(self.maze.map_data):
                    for x, ch in enumerate(row):
                        if ch == '.':
                            food_list.append((x, y))

                if len(food_list) == 0:
                    exit_pos = getattr(self.maze, "exit_pos", None)
                    if exit_pos is None:
                        found = None
                        for y, row in enumerate(self.maze.map_data):
                            for x, ch in enumerate(row):
                                if ch in ('E', 'X', '>', 'e', 'x'):
                                    found = (x, y)
                                    break
                            if found: break
                        exit_pos = found

                    if exit_pos is None:
                        self.draw("No exit found; ending auto mode."); pygame.time.wait(300)
                        self.game_state = 'menu'
                        return
                    else:
                        food_list = [exit_pos]

                problem_state = (cur_pos, frozenset(food_list))
                saved_start = self.problem.start_state
                self.problem.start_state = problem_state

                solution, cost = a_star_search(self.problem, return_cost=True)
                self.problem.start_state = saved_start

                if not solution or len(solution) == 0:
                    self.draw("No path found (replanning...)"); pygame.time.wait(200)
                    self.game_state = 'menu'
                    return

                next_action = solution[0]
                total_cost += cost
                total_steps += 1
                if next_action in direction_stats:
                    direction_stats[next_action] += 1

                dir_vec = pygame.Vector2(0, 0)
                if next_action == 'North': dir_vec = pygame.Vector2(0, -1)
                elif next_action == 'South': dir_vec = pygame.Vector2(0, 1)
                elif next_action == 'East': dir_vec = pygame.Vector2(1, 0)
                elif next_action == 'West': dir_vec = pygame.Vector2(-1, 0)
                elif next_action == 'Teleport' or next_action == 'Stop':
                    dir_vec = pygame.Vector2(0, 0)
                    direction_stats['Stop'] += 1

                if dir_vec.length() > 0:
                    self.pacman.move(dir_vec)

            self.pacman.update()
            for ghost in self.ghosts:
                ghost.update()

            if self.check_victory_condition():
                break

            if self.pacman.power_up_timer == 0:
                for ghost in self.ghosts:
                    if ghost.grid_pos == self.pacman.grid_pos:
                        self.game_state = 'game_over'
                        break

            self.draw("Auto (replanning dynamic)")
            self.clock.tick(60)
            iters += 1

        for ghost in self.ghosts:
            distance = self.pacman.pix_pos.distance_to(ghost.pix_pos)
            if distance < TILE_SIZE / 2:
                self.game_state = 'game_over'
                break

        if iters >= max_iterations:
            print("[WARN] Auto mode reached iteration limit.")
            self.game_state = 'menu'



    def draw(self, status_text=""):
        self.screen.fill(BLACK)
        self.maze.draw(self.screen)
        if self.pacman: self.pacman.draw()
        for ghost in self.ghosts: ghost.draw()
        text_surface = self.font_small.render(status_text, True, WHITE)
        self.screen.blit(text_surface, (10, 10))
        pygame.display.flip()

    def run_game_over(self):
        start_time = pygame.time.get_ticks()
        while pygame.time.get_ticks() - start_time < 3000:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            self.draw("GAME OVER")
            current_width = self.screen.get_width()
            current_height = self.screen.get_height()
            game_over_text = self.font_big.render("GAME OVER", True, (255, 0, 0))
            rect = game_over_text.get_rect(center=(current_width / 2, current_height / 2))
            self.screen.blit(game_over_text, rect)
            pygame.display.flip()
        self.game_state = 'menu'
        
    def check_victory_condition(self):
        remaining_food = any('.' in row for row in self.maze.map_data)
        gates = self.problem._find_all_chars_in_maze('E')
        if not gates:
            return False  

        pacman_pos = pygame.Vector2(int(self.pacman.grid_pos.x), int(self.pacman.grid_pos.y))
        if not remaining_food:
            for gx, gy in gates:
                if abs(pacman_pos.x - gx) + abs(pacman_pos.y - gy) <= 1:
                    start_time = pygame.time.get_ticks()
                    while pygame.time.get_ticks() - start_time < 3000:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()

                        self.draw("YOU WIN!")

                        current_width = self.screen.get_width()
                        current_height = self.screen.get_height()

                        # Dòng code cũ: Hiển thị chữ "YOU WIN!"
                        win_text = self.font_big.render("YOU WIN!", True, (0, 255, 0))
                        win_rect = win_text.get_rect(center=(current_width / 2, current_height / 2 - 20))
                        self.screen.blit(win_text, win_rect)
                        total_steps = self.pacman.step_count
                        
                        steps_text = self.font_small.render(f"Total Steps: {total_steps}", True, WHITE)
                        steps_rect = steps_text.get_rect(center=(current_width / 2, current_height / 2 + 30))
                        
                        self.screen.blit(steps_text, steps_rect)
                        
                        # --- In ra đường đi thật của Pacman ---
                        if not hasattr(self, "win_message_printed"):
                            self.win_message_printed = True  # đánh dấu đã in
                            if hasattr(self, "real_path") and len(self.real_path) > 0:
                                print(f"Total Steps: {self.pacman.step_count} | Path: {' -> '.join(self.real_path)}")


                        pygame.display.flip()
                        
                    self.game_state = 'menu'
                    return True
        return False


if __name__ == '__main__':
    game = Game()
    game.run()
