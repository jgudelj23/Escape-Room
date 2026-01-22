import random
import pygame
from pathlib import Path
from collections import deque

from razine import (
    Pos, GameMap, build_walkable, build_level,
    Feature, Door, Key, Axe, Paper, Tree, Exit, Terminal, Bars
)

pygame.init()

CELL = 40
W, H = 11, 17
SECRET_CODE = "2004"

COLOR_WALK = (255, 255, 255)
COLOR_WALL = (55, 55, 55)
GRID_COLOR = (0, 0, 0)

MODE_PLAY, MODE_PAPER, MODE_CODE, MODE_EXIT = "play", "paper", "code", "exit"
AUTO_STEP_MS = 70
AUTO_CODE_STEP_MS = 260
DIRS4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]
INF = 10**9

screen = pygame.display.set_mode((W * CELL, H * CELL))
pygame.display.set_caption("Escape Room")
clock = pygame.time.Clock()

class Popup:
    def __init__(self):
        self.text = ""
        self.until = 0
        self.font = pygame.font.SysFont(None, 26)

    def show(self, text: str, ms: int = 1700):
        self.text = text
        self.until = pygame.time.get_ticks() + ms

    def draw(self, surf: pygame.Surface):
        if not (self.text and pygame.time.get_ticks() < self.until):
            return
        pad = 12
        txt = self.font.render(self.text, True, (255, 255, 255))
        w, h = txt.get_width() + pad * 2, txt.get_height() + pad * 2
        x, y = (surf.get_width() - w) // 2, 10
        r = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, (20, 20, 20), r, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 255), r, 2, border_radius=10)
        surf.blit(txt, (x + pad, y + pad))

popup = Popup()

_fonts = {}
def F(size: int):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]

asset_dir = Path(__file__).parent / "slike"

def load_sprite(name: str):
    fp = asset_dir / f"{name}.png"
    if not fp.exists():
        return None
    img = pygame.image.load(str(fp)).convert_alpha()
    return pygame.transform.smoothscale(img, (CELL, CELL))

def scale_sprite(surf, wc, hc):
    return None if surf is None else pygame.transform.smoothscale(surf, (CELL * wc, CELL * hc))

sprites = {k: load_sprite(k) for k in (
    "igrac", "vrata", "kljuc", "sjekira", "terminal", "resetke",
    "papir", "papirus", "zastava", "drvo", "voda", "most"
)}

paper_original = None
pp = asset_dir / "papir.png"
if pp.exists():
    paper_original = pygame.image.load(str(pp)).convert_alpha()

def blit_cell(key: str, p: Pos):
    spr = sprites.get(key)
    if spr:
        screen.blit(spr, (p.x * CELL, p.y * CELL))

walkable = build_walkable()
game_map = GameMap(W, H, walkable)
player, features, sea, start_pos = build_level()

sea_big = scale_sprite(sprites.get("voda"), sea.width_cells, sea.height_cells)
bridge_big = scale_sprite(sprites.get("most"), sea.width_cells, sea.height_cells)

feat_at = {f.pos: f for f in features}
def remove_feature(f: Feature):
    if f in features:
        features.remove(f)
        feat_at.pop(f.pos, None)

has_key = has_axe = has_wood = has_paper = False
bridge_built = terminal_unlocked = False
mode = MODE_PLAY
code_input = ""

exit_start_ms = 0
confetti = []
game_finished = False

graf = {}
for p in walkable:
    graf[p] = [Pos(p.x + dx, p.y + dy) for dx, dy in DIRS4 if Pos(p.x + dx, p.y + dy) in walkable]

def bfs_tree(start: Pos):
    q = deque([start])
    vis = {start}
    parent = {start: None}
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in graf.get(u, []):
            if v not in vis:
                vis.add(v)
                parent[v] = u
                q.append(v)
    return order, parent

def dfs_tree(start: Pos):
    st = [start]
    vis = set()
    parent = {start: None}
    order = []
    while st:
        u = st.pop()
        if u in vis:
            continue
        vis.add(u)
        order.append(u)
        for v in reversed(graf.get(u, [])):
            if v not in vis:
                parent.setdefault(v, u)
                st.append(v)
    return order, parent

def tree_path_between(a: Pos, b: Pos, parent):
    if a == b:
        return []
    anc = set()
    x = a
    while x is not None:
        anc.add(x)
        x = parent.get(x)

    path_b = []
    y = b
    while y not in anc and y is not None:
        path_b.append(y)
        y = parent.get(y)

    lca = y
    if lca is None:
        return []

    up = []
    x = a
    while x != lca and x is not None:
        x = parent.get(x)
        if x is None:
            return []
        up.append(x)

    return up + list(reversed(path_b))

def is_sea(p: Pos):
    return sea.contains(p)

def manhattan(a: Pos, b: Pos):
    return abs(a.x - b.x) + abs(a.y - b.y)

def find_positions(cls):
    return [f.pos for f in features if isinstance(f, cls)]

def find_first(cls):
    for f in features:
        if isinstance(f, cls):
            return f.pos
    return None

def nearest(cls):
    pts = find_positions(cls)
    return min(pts, key=lambda p: manhattan(player.pos, p)) if pts else None

def nearest_sea_entry():
    entries = []
    for sc in sea.cells():
        for dx, dy in DIRS4:
            if Pos(sc.x + dx, sc.y + dy) in walkable:
                entries.append(sc)
                break
    return min(entries, key=lambda p: manhattan(player.pos, p)) if entries else None

def start_exit_animation():
    global mode, exit_start_ms, confetti
    mode = MODE_EXIT
    exit_start_ms = pygame.time.get_ticks()
    confetti = []
    cx = player.pos.x * CELL + CELL // 2
    cy = player.pos.y * CELL + CELL // 2
    for _ in range(160):
        confetti.append([cx, cy, random.uniform(-3.2, 3.2), random.uniform(-5.0, -1.2), random.uniform(0.5, 1.2)])

def finish_game():
    global game_finished
    game_finished = True
    stop_auto()
    popup.show("Kraj", 4000)

def can_enter(p: Pos):
    global bridge_built
    if game_finished:
        return False

    f = feat_at.get(p)

    if isinstance(f, Door):
        if not has_key:
            popup.show("Vrata su zaključana")
            return False
        remove_feature(f)
        popup.show("Vrata su otključana")
        return True

    if isinstance(f, Bars):
        if terminal_unlocked:
            remove_feature(f)
            return True
        popup.show("Rešetka je spuštena. Upiši šifru")
        return False

    if is_sea(p) and not bridge_built:
        if has_axe and has_wood:
            bridge_built = True
            popup.show("Most je izgrađen")
            return True
        popup.show("Treba ti sjekira i drvo za izgradnju mosta", 2200)
        return False

    return True

auto_active = False
auto_kind = None
auto_targets = []
auto_parent = {}
auto_subpath = []
auto_target = None
auto_last_step = 0

auto_code_active = False
auto_code_i = 0
auto_code_next = 0

def stop_auto():
    global auto_active, auto_kind, auto_targets, auto_parent, auto_subpath, auto_target, auto_code_active
    auto_active = False
    auto_kind = None
    auto_targets = []
    auto_parent = {}
    auto_subpath = []
    auto_target = None
    auto_code_active = False

def dfs_restart_from_here():
    global auto_targets, auto_parent, auto_subpath, auto_target, auto_last_step
    if not auto_active or auto_kind != "dfs":
        return
    order, parent = dfs_tree(player.pos)
    auto_targets, auto_parent = order[:], parent
    auto_subpath, auto_target = [], None
    auto_last_step = pygame.time.get_ticks()

def try_collect(p: Pos):
    global has_key, has_axe, has_wood, has_paper, mode, code_input
    if game_finished:
        return

    f = feat_at.get(p)
    if not f:
        return

    def on_change():
        if auto_active and auto_kind == "dfs":
            dfs_restart_from_here()
        if auto_active and auto_kind == "astar":
            astar_replan()

    if isinstance(f, Key):
        has_key = True
        remove_feature(f)
        popup.show("Ključ pokupljen")
        on_change()
        return

    if isinstance(f, Axe):
        has_axe = True
        remove_feature(f)
        popup.show("Sjekira pokupljena")
        on_change()
        return

    if isinstance(f, Paper):
        has_paper = True
        remove_feature(f)
        mode = MODE_PAPER
        on_change()
        return

    if isinstance(f, Tree):
        if not has_axe:
            popup.show("Treba ti sjekira da posiječeš drvo")
            return
        has_wood = True
        remove_feature(f)
        popup.show("Posijekao si drvo za most")
        on_change()
        return

    if isinstance(f, Terminal):
        if not has_paper:
            popup.show("Upiši šifru")
            return
        if terminal_unlocked:
            popup.show("Terminal je već otključan.")
            return
        code_input = ""
        mode = MODE_CODE
        popup.show(f"Upiši šifru ({len(SECRET_CODE)} znamenke) i ENTER.", 2400)
        return

    if isinstance(f, Bars):
        popup.show("Rešetka je spuštena. Upiši šifru")
        return

    if isinstance(f, Exit):
        start_exit_animation()
        finish_game()
        return

def passable_plan(p: Pos):
    f = feat_at.get(p)
    if isinstance(f, Door) and not has_key:
        return False
    if isinstance(f, Bars) and not terminal_unlocked:
        return False
    if is_sea(p) and not bridge_built:
        return bool(has_axe and has_wood)
    return True

def astar_path(start: Pos, goal: Pos):
    if start == goal:
        return []
    open_set = {start}
    came = {}
    g = {start: 0}
    f = {start: manhattan(start, goal)}

    while open_set:
        cur = min(open_set, key=lambda p: f.get(p, INF))
        if cur == goal:
            out = []
            x = goal
            while x != start:
                out.append(x)
                x = came[x]
            out.reverse()
            return out

        open_set.remove(cur)
        for nb in graf.get(cur, []):
            if not passable_plan(nb):
                continue
            tg = g[cur] + 1
            if tg < g.get(nb, INF):
                came[nb] = cur
                g[nb] = tg
                f[nb] = tg + manhattan(nb, goal)
                open_set.add(nb)
    return []

def start_auto(kind: str):
    global auto_active, auto_kind, auto_targets, auto_parent, auto_subpath, auto_target, auto_last_step
    if kind == "bfs":
        order, parent = bfs_tree(player.pos)
    else:
        order, parent = dfs_tree(player.pos)
    auto_active, auto_kind = True, kind
    auto_targets, auto_parent = order[:], parent
    auto_subpath, auto_target = [], None
    auto_last_step = pygame.time.get_ticks()

def astar_next_goal():
    if not has_key:
        return nearest(Key)
    d = find_first(Door)
    if d is not None:
        return d
    if not has_paper:
        return nearest(Paper)
    if not has_axe:
        return nearest(Axe)
    if not has_wood:
        return nearest(Tree)
    if not bridge_built:
        return nearest_sea_entry()
    if not terminal_unlocked:
        return nearest(Terminal)
    return find_first(Exit)

def astar_replan():
    global auto_subpath, auto_target
    if not auto_active or auto_kind != "astar":
        return
    goal = astar_next_goal()
    if goal is None:
        popup.show("Nema cilja na mapi")
        stop_auto()
        return
    path = astar_path(player.pos, goal)
    if not path:
        stop_auto()
        return
    auto_subpath, auto_target = path[:], goal

def start_auto_astar():
    global auto_active, auto_kind, auto_subpath, auto_target, auto_last_step
    auto_active, auto_kind = True, "astar"
    auto_subpath, auto_target = [], None
    auto_last_step = pygame.time.get_ticks()
    popup.show("A* pretraživanje", 1500)
    astar_replan()

def auto_try_terminal():
    global mode, code_input, auto_code_active, auto_code_i, auto_code_next
    if game_finished:
        return
    f = feat_at.get(player.pos)
    if isinstance(f, Terminal) and has_paper and not terminal_unlocked:
        mode = MODE_CODE
        code_input = ""
        auto_code_active = True
        auto_code_i = 0
        auto_code_next = pygame.time.get_ticks() + AUTO_CODE_STEP_MS
        popup.show("Upisivanje šifre", 1500)

def auto_type_code():
    global terminal_unlocked, mode, code_input, auto_code_active, auto_code_i, auto_code_next
    if game_finished:
        auto_code_active = False
        return
    if not auto_code_active or mode != MODE_CODE:
        auto_code_active = False
        return
    now = pygame.time.get_ticks()
    if now < auto_code_next:
        return
    if auto_code_i < len(SECRET_CODE):
        code_input += SECRET_CODE[auto_code_i]
        auto_code_i += 1
        auto_code_next = now + AUTO_CODE_STEP_MS
        return
    terminal_unlocked = True
    auto_code_active = False
    popup.show("Uspješno upisana lozinka. Rešetka je podignuta", 1400)
    mode = MODE_PLAY
    if auto_active and auto_kind == "dfs":
        dfs_restart_from_here()
    if auto_active and auto_kind == "astar":
        astar_replan()

def update_auto():
    global auto_last_step, auto_subpath, auto_target

    if game_finished or not auto_active or mode != MODE_PLAY:
        return

    now = pygame.time.get_ticks()
    if now - auto_last_step < AUTO_STEP_MS:
        return
    auto_last_step = now

    if auto_kind == "astar":
        if not auto_subpath:
            astar_replan()
            if not auto_subpath:
                return

        nxt = auto_subpath[0]
        if not can_enter(nxt):
            astar_replan()
            return

        auto_subpath.pop(0)
        player.pos = nxt
        try_collect(player.pos)
        auto_try_terminal()

        if auto_target == player.pos and auto_active and auto_kind == "astar":
            astar_replan()
        return

    while not auto_subpath:
        if not auto_targets:
            stop_auto()
            return
        t = auto_targets.pop(0)
        if t == player.pos:
            continue
        auto_target = t
        auto_subpath = tree_path_between(player.pos, t, auto_parent)
        if not auto_subpath:
            auto_target = None

    nxt = auto_subpath[0]
    if not can_enter(nxt):
        if auto_target is not None:
            auto_targets.append(auto_target)
        auto_subpath, auto_target = [], None
        return

    auto_subpath.pop(0)
    player.pos = nxt
    try_collect(player.pos)
    auto_try_terminal()
    if auto_target == player.pos:
        auto_target = None

def draw_dim(alpha=190):
    s = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    screen.blit(s, (0, 0))

def draw_tiles():
    for y in range(H):
        for x in range(W):
            p = Pos(x, y)
            color = COLOR_WALK if game_map.tile_at(p).walkable else COLOR_WALL
            r = pygame.Rect(x * CELL, y * CELL, CELL, CELL)
            pygame.draw.rect(screen, color, r)
            pygame.draw.rect(screen, GRID_COLOR, r, 1)

def draw_world():
    draw_tiles()
    img = bridge_big if bridge_built else sea_big
    if img:
        screen.blit(img, (sea.top_left.x * CELL, sea.top_left.y * CELL))
    for f in features:
        if isinstance(f, Paper):
            blit_cell("papirus", f.pos)
        else:
            blit_cell(f.sprite_key, f.pos)
    blit_cell("igrac", player.pos)

def draw_paper():
    draw_dim()
    sw, sh = screen.get_size()
    if paper_original is None:
        screen.blit(F(26).render("papir.png nije pronađen", True, (255, 255, 255)), (20, 20))
        return
    iw, ih = paper_original.get_size()
    sc = min((sw * 0.92) / iw, (sh * 0.92) / ih)
    nw, nh = int(iw * sc), int(ih * sc)
    big = pygame.transform.scale(paper_original, (nw, nh))
    screen.blit(big, ((sw - nw) // 2, (sh - nh) // 2))
    screen.blit(F(26).render("SPACE/ENTER/ESC za zatvoriti", True, (255, 255, 255)), (20, sh - 30))

def draw_code():
    draw_dim()
    screen.blit(F(32).render("Upiši šifru", True, (255, 255, 255)), (20, 20))
    shown = code_input + ("_" if (pygame.time.get_ticks() // 300) % 2 == 0 else "")
    screen.blit(F(46).render(shown, True, (255, 255, 255)), (20, 80))
    screen.blit(F(24).render("ENTER potvrdi | BACKSPACE briše | ESC izlaz", True, (255, 255, 255)), (20, 140))

def update_exit_animation():
    if game_finished:
        return
    global mode
    if pygame.time.get_ticks() - exit_start_ms >= 2600:
        mode = MODE_PLAY
        popup.show("Bravo, uspješno si pronašao izlaz iz ecsape room-a", 2600)

def draw_exit():
    t = pygame.time.get_ticks() - exit_start_ms
    if t < 550:
        a = int(210 * (1.0 - t / 550.0))
        flash = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        flash.fill((255, 255, 255, a))
        screen.blit(flash, (0, 0))
    for p in confetti:
        p[0] += p[2]
        p[1] += p[3]
        p[3] += 0.14
        p[4] *= 0.995
        pygame.draw.circle(screen, (255, 255, 255), (int(p[0]), int(p[1])), max(1, int(3 * p[4])))

def move(dx: int, dy: int):
    if mode != MODE_PLAY or game_finished:
        return
    np = Pos(player.pos.x + dx, player.pos.y + dy)
    if not game_map.in_bounds(np):
        return
    if not game_map.tile_at(np).walkable:
        return
    if not can_enter(np):
        return
    player.pos = np
    try_collect(player.pos)
    auto_try_terminal()

try_collect(player.pos)

running = True
while running:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False
            break

        if e.type != pygame.KEYDOWN:
            continue

        if e.key == pygame.K_ESCAPE:
            if mode in (MODE_PAPER, MODE_CODE):
                mode = MODE_PLAY
                auto_code_active = False
            else:
                running = False
            continue

        if game_finished:
            continue

        if mode == MODE_PLAY:
            if e.key == pygame.K_1:
                start_auto("bfs")
            elif e.key == pygame.K_2:
                start_auto("dfs")
            elif e.key == pygame.K_3:
                start_auto_astar()

        if e.key in (
            pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN,
            pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT
        ) and auto_active:
            stop_auto()

        if mode == MODE_PAPER:
            if e.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                mode = MODE_PLAY
            continue

        if mode == MODE_CODE:
            if not auto_code_active:
                if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if code_input == SECRET_CODE:
                        terminal_unlocked = True
                        popup.show("Uspješno upisana lozinka. Rešetka je podignuta")
                        mode = MODE_PLAY
                        if auto_active and auto_kind == "astar":
                            astar_replan()
                    else:
                        popup.show("Kriva lozinka, pokušaj opet", 1700)
                        code_input = ""
                elif e.key == pygame.K_BACKSPACE:
                    code_input = code_input[:-1]
                elif len(code_input) < len(SECRET_CODE) and e.unicode.isdigit():
                    code_input += e.unicode
            continue

        if mode == MODE_PLAY:
            if e.key in (pygame.K_w, pygame.K_UP):
                move(0, -1)
            elif e.key in (pygame.K_s, pygame.K_DOWN):
                move(0, 1)
            elif e.key in (pygame.K_a, pygame.K_LEFT):
                move(-1, 0)
            elif e.key in (pygame.K_d, pygame.K_RIGHT):
                move(1, 0)

    update_auto()
    auto_type_code()

    if mode == MODE_EXIT:
        update_exit_animation()

    draw_world()

    if mode == MODE_PAPER:
        draw_paper()
    elif mode == MODE_CODE:
        draw_code()
    elif mode == MODE_EXIT:
        draw_exit()

    popup.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
