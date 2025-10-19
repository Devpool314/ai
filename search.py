import heapq
import pygame

class PacmanSearchProblem:
    def __init__(self, game_maze):
        self.maze = game_maze
        # Sửa lỗi typo _get_start_state -> get_start_state nếu có
        self.start_state = self._get_start_state() 
        self.exit_pos = self._find_char_in_maze('E')
        self._distance_cache = {}

    def get_start_state(self):
        return self.start_state

    def is_goal_state(self, state):
        pacman_pos, food_set = state
        return len(food_set) == 0

    # =========================================================================
    # HÀM GET_SUCCESSORS ĐÃ ĐƯỢC CẬP NHẬT HOÀN CHỈNH
    # =========================================================================
    def get_successors(self, state):
        successors = []
        pacman_pos_tuple, food_set = state
        pacman_pos = pygame.Vector2(pacman_pos_tuple)

        # --- BƯỚC 1: AI "NHÌN" XEM PACMAN CÓ ĐANG POWER-UP HAY KHÔNG ---
        is_powered_up = False
        try:
            # AI sẽ đọc trực tiếp trạng thái của Pacman trong game
            if self.maze.game.pacman.power_up_timer > 0:
                is_powered_up = True
        except Exception:
            pass # An toàn nếu pacman chưa được tạo
        # ----------------------------------------------------------------

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
                
            # --- BƯỚC 2: AI ÁP DỤNG QUY TẮC MỚI KHI XÉT TƯỜNG ---
            # AI kiểm tra xem ô tiếp theo có phải là tường không
            is_wall = self.maze.map_data[ny][nx] == '%'
            
            # Nếu đó là tường VÀ Pacman KHÔNG có power-up, thì AI mới coi đó là vật cản
            if is_wall and not is_powered_up:
                continue 
            # --------------------------------------------------------

            # Phần còn lại của logic (tính cost, né ghost, ăn food) giữ nguyên
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

    # Trường hợp cơ bản: đã ăn hết thức ăn
    if not food_set:
        exit_pos = getattr(problem, "exit_pos", None)
        if exit_pos:
            return problem.get_maze_distance(pacman_pos, exit_pos)
        return 0

    food_list = list(food_set)

    # --- BƯỚC 1: TÍNH KHOẢNG CÁCH TỪ PACMAN TỚI MẠNG LƯỚI THỨC ĂN ---
    # Tìm khoảng cách mê cung ngắn nhất từ Pacman đến bất kỳ viên thức ăn nào.
    min_dist_to_food = float('inf')
    for food in food_list:
        dist = problem.get_maze_distance(pacman_pos, food)
        if dist < min_dist_to_food:
            min_dist_to_food = dist

    # --- BƯỚC 2: TÍNH CHI PHÍ MẠNG LƯỚI THỨC ĂN BẰNG MST (THUẬT TOÁN PRIM) ---
    # Đây là phần tính toán chi phí tối thiểu để "kết nối" tất cả các viên thức ăn lại.
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

    # --- BƯỚC 3: KẾT HỢP VỚI CÁC YẾU TỐ KHÁC (NÉ MA) ---
    # Yếu tố né ma vẫn cực kỳ quan trọng để sinh tồn
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
    
    # Heuristic cuối cùng
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
                print(f"\n A* Completed — Total cost: {total_cost}")
                print(f"Path: {full_path}\n")
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
