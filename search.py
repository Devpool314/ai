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

        # ---  AI "NHÌN" XEM PACMAN CÓ ĐANG POWER-UP HAY KHÔNG ---
        is_powered_up = False
        try:
            # AI sẽ đọc trực tiếp trạng thái của Pacman trong game
            if self.maze.game.pacman.power_up_timer > 0:
                is_powered_up = True
        except Exception:
            pass # An toàn nếu pacman chưa được tạo

        # Lấy vị trí và vùng nguy hiểm của ghost (giữ nguyên)
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
                    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nx, ny = gx + dx, gy + dy
                        if 0 <= ny < len(self.maze.map_data) and 0 <= nx < len(self.maze.map_data[ny]):
                            if self.maze.map_data[ny][nx] != '%':
                                danger_zones.add((nx, ny))
        except Exception:
            pass

        # Logic teleport 4 góc (giữ nguyên)
        corners = [
                (0, 0), (self.maze.tile_width - 1, 0),
                (0, self.maze.tile_height - 1), (self.maze.tile_width - 1, self.maze.tile_height - 1)
        ]
        if pacman_pos_tuple in corners:
            for target in corners:
                if target == pacman_pos_tuple: continue
                if target in ghost_positions: continue
                cost = 1
                if target in danger_zones or target[1] in dangerous_rows:
                    cost += 50
                successors.append(((target, food_set), 'Teleport', cost))

        # Di chuyển 4 hướng
        actions = [(-1,0,'West'), (1,0,'East'), (0,-1,'North'), (0,1,'South')]
        x, y = int(pacman_pos.x), int(pacman_pos.y)

        for dx, dy, action in actions:
            nx, ny = x + dx, y + dy
            
            # Xử lý đi xuyên cạnh màn hình
            if nx < 0: nx = self.maze.tile_width - 1
            elif nx >= self.maze.tile_width: nx = 0

            # Kiểm tra biên trên/dưới
            if not (0 <= ny < len(self.maze.map_data)):
                continue
                
            is_wall = self.maze.map_data[ny][nx] == '%'
            
            if is_wall and not is_powered_up:
                continue 

            next_pos = (nx, ny)
            cost = 1
            if next_pos in ghost_positions: cost = 9999
            elif next_pos in danger_zones: cost = 100
            elif ny in dangerous_rows: cost = 100
            
            next_food_set = set(food_set)
            if next_pos in next_food_set:
                next_food_set.remove(next_pos)
                cost = max(1, cost - 10)

            successors.append(((next_pos, frozenset(next_food_set)), action, cost))

        return successors
        
    # === BFS cache ===
    def get_maze_distance(self, start, goal):
        if start == goal:
            return 0

        # Cache kết quả nếu có
        if (start, goal) in self._distance_cache:
            return self._distance_cache[(start, goal)]

        def is_walkable(x, y):
            return (
                0 <= y < len(self.maze.map_data)
                and 0 <= x < len(self.maze.map_data[y])
                and self.maze.map_data[y][x] != '%'
            )

        def jump(x, y, dx, dy):

            next_x, next_y = x + dx, y + dy
            if not is_walkable(next_x, next_y):
                return None
            if (next_x, next_y) == goal:
                return (next_x, next_y)

            # Forced neighbor check (phát hiện ngã rẽ)
            if dx != 0 and dy == 0:  # ngang
                if (is_walkable(next_x, next_y - 1) and not is_walkable(x, y - 1)) \
                   or (is_walkable(next_x, next_y + 1) and not is_walkable(x, y + 1)):
                    return (next_x, next_y)
            elif dy != 0 and dx == 0:  # dọc
                if (is_walkable(next_x - 1, next_y) and not is_walkable(x - 1, y)) \
                   or (is_walkable(next_x + 1, next_y) and not is_walkable(x + 1, y)):
                    return (next_x, next_y)

            return jump(next_x, next_y, dx, dy)

        def get_neighbors(x, y):
            """Lấy 4 hướng di chuyển hợp lệ."""
            dirs = []
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if is_walkable(nx, ny):
                    dirs.append((dx, dy))
            return dirs

        import heapq
        open_list = [(0, start)]
        g_cost = {start: 0}
        heapq.heapify(open_list)

        while open_list:
            _, current = heapq.heappop(open_list)
            if current == goal:
                self._distance_cache[(start, goal)] = g_cost[current]
                self._distance_cache[(goal, start)] = g_cost[current]
                return g_cost[current]

            x, y = current
            for dx, dy in get_neighbors(x, y):
                jump_point = jump(x, y, dx, dy)
                if jump_point:
                    new_g = g_cost[current] + 1  # mỗi bước nhảy = 1 cạnh hợp lệ
                    if jump_point not in g_cost or new_g < g_cost[jump_point]:
                        g_cost[jump_point] = new_g
                        heapq.heappush(open_list, (new_g, jump_point))

        return 9999  

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
    if not food_set:
        exit_pos = getattr(problem, "exit_pos", None)
        if exit_pos:
            return problem.get_maze_distance(pacman_pos, exit_pos)
        return 0

    food_list = list(food_set)

    min_dist_to_food = float('inf')
    for food in food_list:
        dist = problem.get_maze_distance(pacman_pos, food)
        if dist < min_dist_to_food:
            min_dist_to_food = dist

    mst_cost = 0
    if len(food_list) > 1:
        # Sử dụng thuật toán Prim để tính MST
        visited = {food_list[0]}
        edges = []
        
        # Thêm các cạnh từ đỉnh bắt đầu
        for i in range(1, len(food_list)):
            cost = problem.get_maze_distance(food_list[0], food_list[i])
            heapq.heappush(edges, (cost, food_list[0], food_list[i]))

        while edges and len(visited) < len(food_list):
            cost, u, v = heapq.heappop(edges)

            if v in visited:
                continue
            
            visited.add(v)
            mst_cost += cost

            # Thêm các cạnh mới từ đỉnh vừa thăm
            for food_neighbor in food_list:
                if food_neighbor not in visited:
                    new_cost = problem.get_maze_distance(v, food_neighbor)
                    heapq.heappush(edges, (new_cost, v, food_neighbor))

    # Heuristic chính là tổng của khoảng cách đến mạng lưới và chi phí của mạng lưới
    food_heuristic = min_dist_to_food + mst_cost

    danger_penalty = 0
    try:
        if hasattr(problem.maze, "game") and hasattr(problem.maze.game, "ghosts"):
            for ghost in problem.maze.game.ghosts:
                ghost_pos = (int(round(ghost.grid_pos.x)), int(round(ghost.grid_pos.y)))
                grid_dist = abs(ghost_pos[0] - pacman_pos[0]) + abs(ghost_pos[1] - pacman_pos[1])
                if grid_dist <= 1: danger_penalty += 1500 # Tăng hình phạt
                elif grid_dist <= 3: danger_penalty += 500
    except Exception:
        pass
    return food_heuristic + danger_penalty
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
                return full_path, total_cost
            return full_path

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
