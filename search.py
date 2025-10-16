import heapq
import pygame

class PacmanSearchProblem:
    def __init__(self, game_maze):
        self.maze = game_maze
        self.start_state = self._get_start_state()
        self.exit_pos = self._find_char_in_maze('E')
        self._distance_cache = {}

    def get_start_state(self):
        return self.start_state

    def is_goal_state(self, state):
        pacman_pos, food_set = state
        return len(food_set) == 0

    def get_successors(self, state):

        successors = []
        pacman_pos_tuple, food_set = state
        pacman_pos = pygame.Vector2(pacman_pos_tuple)

        # lấy ghost positions & dangerous rows/zones (dùng int(round()) để an toàn)
        ghost_positions = set()
        danger_zones = set()
        dangerous_rows = set()

        try:
            if hasattr(self.maze, "game") and hasattr(self.maze.game, "ghosts"):
                for ghost in self.maze.game.ghosts:
                    gx = int(round(ghost.grid_pos.x))
                    gy = int(round(ghost.grid_pos.y))
                    ghost_positions.add((gx, gy))
                    dangerous_rows.add(gy)
                    # lân cận 1 ô
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx, ny = gx + dx, gy + dy
                        if 0 <= ny < len(self.maze.map_data) and 0 <= nx < len(self.maze.map_data[ny]):
                            if self.maze.map_data[ny][nx] != '%':
                                danger_zones.add((nx, ny))
        except Exception:
            pass

        # teleport 4 góc (tránh teleport tới góc có ghost/hàng ghost nếu có lựa chọn)
        corners = [
            (0, 0),
            (self.maze.tile_width - 1, 0),
            (0, self.maze.tile_height - 1),
            (self.maze.tile_width - 1, self.maze.tile_height - 1)
        ]
        if pacman_pos_tuple in corners:
            for target in corners:
                if target == pacman_pos_tuple:
                    continue
                if target in ghost_positions:
                    continue
                cost = 1
                if target in danger_zones or target[1] in dangerous_rows:
                    cost += 50
                successors.append(((target, food_set), 'Teleport', cost))

        # di chuyển 4 hướng
        actions = [(-1,0,'West'), (1,0,'East'), (0,-1,'North'), (0,1,'South')]
        x, y = int(pacman_pos.x), int(pacman_pos.y)

        for dx, dy, action in actions:
            nx, ny = x + dx, y + dy
            # bounds & wall
            if not (0 <= ny < len(self.maze.map_data)): continue
            if not (0 <= nx < len(self.maze.map_data[ny])): continue
            if self.maze.map_data[ny][nx] == '%': continue

            next_pos = (nx, ny)
            cost = 1

            # tránh ghost trực tiếp
            if next_pos in ghost_positions:
                cost = 9999
            # tránh vùng lân cận
            elif next_pos in danger_zones:
                cost = 200
            # tránh toàn hàng ghost
            elif ny in dangerous_rows:
                cost = 600

            # update food
            next_food_set = set(food_set)
            if next_pos in next_food_set:
                next_food_set.remove(next_pos)
                # khuyến khích ăn food (giảm 1-10 tuỳ penalty)
                cost = max(1, cost - 10)

            successors.append(((next_pos, frozenset(next_food_set)), action, cost))

        return successors

    # === BFS cache ===
    def get_maze_distance(self, pos1, pos2):
        if (pos1, pos2) in self._distance_cache:
            return self._distance_cache[(pos1, pos2)]

        queue = [(pos1, 0)]
        visited = {pos1}
        while queue:
            current_pos, dist = queue.pop(0)
            if current_pos == pos2:
                self._distance_cache[(pos1, pos2)] = dist
                self._distance_cache[(pos2, pos1)] = dist
                return dist
            x, y = current_pos
            for dx, dy, _ in [(-1, 0, ''), (1, 0, ''), (0, -1, ''), (0, 1, '')]:
                next_x, next_y = x + dx, y + dy
                if (0 <= next_y < len(self.maze.map_data)
                    and 0 <= next_x < len(self.maze.map_data[next_y])
                    and self.maze.map_data[next_y][next_x] != '%'
                    and (next_x, next_y) not in visited):
                    visited.add((next_x, next_y))
                    queue.append(((next_x, next_y), dist + 1))
        return 0

    def _get_start_state(self):
        pacman_pos = self._find_char_in_maze('P')
        food_list = self._find_all_chars_in_maze('.')
        return (pacman_pos, frozenset(food_list))

    def _find_char_in_maze(self, char):
        for y, row in enumerate(self.maze.map_data):
            for x, cell in enumerate(row):
                if cell == char:
                    return (x, y)
        return None

    def _find_all_chars_in_maze(self, char):
        positions = []
        for y, row in enumerate(self.maze.map_data):
            for x, cell in enumerate(row):
                if cell == char:
                    positions.append((x, y))
        return positions


# ==============================
#  Heuristic A*
# ==============================
def heuristic(state, problem):
    
    pacman_pos, food_set = state
    maze = problem.maze

    # lấy ghost positions
    ghosts = []
    try:
        if hasattr(maze, "game") and hasattr(maze.game, "ghosts"):
            for ghost in maze.game.ghosts:
                gx, gy = int(round(ghost.grid_pos.x)), int(round(ghost.grid_pos.y))
                ghosts.append((gx, gy))
    except Exception:
        pass

    # teleport dictionary (4 góc)
    teleports = {
        (0, 0): (maze.tile_width - 1, 0),
        (maze.tile_width - 1, 0): (0, 0),
        (0, maze.tile_height - 1): (maze.tile_width - 1, maze.tile_height - 1),
        (maze.tile_width - 1, maze.tile_height - 1): (0, maze.tile_height - 1)
    }

    # ===  Ước lượng food cost (dựa vào chênh lệch grid)
    food_cost = 0
    if food_set:
        # tìm food xa nhất dựa trên chênh lệch lưới
        max_gap = 0
        for fx, fy in food_set:
            dx = abs(fx - pacman_pos[0])
            dy = abs(fy - pacman_pos[1])
            approx = (dx + dy + abs(dx - dy)) // 2  # grid rough distance
            if approx > max_gap:
                max_gap = approx
        food_cost = max_gap * 2  # ăn food xa nhất

    # ===  Né ghost — phạt nếu ở gần
    danger_penalty = 0
    for gx, gy in ghosts:
        dx = abs(gx - pacman_pos[0])
        dy = abs(gy - pacman_pos[1])
        grid_dist = dx + dy
        if grid_dist <= 1:
            danger_penalty += 2000
        elif grid_dist == 2:
            danger_penalty += 800
        elif grid_dist <= 4:
            danger_penalty += 300
        elif grid_dist <= 6:
            danger_penalty += 100

    # ===  Teleport bonus (nếu gần góc)
    tele_bonus = 0
    for entry, exitp in teleports.items():
        dx = abs(entry[0] - pacman_pos[0])
        dy = abs(entry[1] - pacman_pos[1])
        if dx + dy <= 2:  # gần teleport
            tele_bonus = -100  # khuyến khích sử dụng

    # ===  Exit cost (sau khi ăn hết food)
    exit_pos = getattr(problem, "exit_pos", None)
    exit_cost = 0
    if not food_set and exit_pos:
        dx = abs(exit_pos[0] - pacman_pos[0])
        dy = abs(exit_pos[1] - pacman_pos[1])
        exit_cost = (dx + dy + abs(dx - dy))  # ước lượng khoảng cách grid

    # ===  Tổng hợp heuristic ===
    h_value = food_cost + danger_penalty + exit_cost + tele_bonus
    return h_value

# ==============================
#  A* Search
# ==============================
def a_star_search(problem, return_cost=False):
    frontier = []
    start_state = problem.get_start_state()
    heapq.heappush(frontier, (0, 0, [], start_state))
    explored = set()

    while frontier:
        f_cost, g_cost, path, current_state = heapq.heappop(frontier)

        pacman_pos, food_set = current_state
        hashable_state = (pacman_pos, tuple(sorted(food_set)))
        if hashable_state in explored:
            continue
        explored.add(hashable_state)

        if problem.is_goal_state(current_state):
            last_pos = current_state[0]
            exit_pos = problem.exit_pos
            total_cost = g_cost

            # Nếu có cổng 'E', thêm đường đến đó
            if exit_pos:
                queue = [(last_pos, [])]
                visited_exit_path = {last_pos}
                path_to_exit = []
                while queue:
                    curr, p = queue.pop(0)
                    if curr == exit_pos:
                        path_to_exit = p
                        break
                    x, y = curr
                    for dx, dy, action in [(-1, 0, 'West'), (1, 0, 'East'),
                                           (0, -1, 'North'), (0, 1, 'South')]:
                        next_x, next_y = x + dx, y + dy
                        next_pos = (next_x, next_y)
                        if (0 <= next_y < len(problem.maze.map_data)
                            and 0 <= next_x < len(problem.maze.map_data[next_y])
                            and problem.maze.map_data[next_y][next_x] != '%'
                            and next_pos not in visited_exit_path):
                            visited_exit_path.add(next_pos)
                            queue.append((next_pos, p + [action]))
                full_path = path + path_to_exit
                total_cost += len(path_to_exit)
            else:
                full_path = path

            full_path = full_path + ['Stop']

            if return_cost:
                print(f"\n A* Completed — Total cost: {total_cost}")
                print(f"Path: {full_path}\n")
                return full_path, total_cost
            return full_path

        # Mở rộng
        for next_state, action, cost in problem.get_successors(current_state):
            pac_next, food_next = next_state
            hashable_next = (pac_next, tuple(sorted(food_next)))
            if hashable_next not in explored:
                new_g = g_cost + cost
                h = heuristic(next_state, problem)
                new_f = new_g + h
                new_path = path + [action]
                heapq.heappush(frontier, (new_f, new_g, new_path, next_state))

    if return_cost:
        return [], 0
    return []
