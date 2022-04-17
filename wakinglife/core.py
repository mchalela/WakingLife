# Life is just a game

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# IMPORTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from collections.abc import Mapping
import attr

import numpy as np

import pygame

import time

gray = 27, 27, 27
white = 250, 250, 250
magenta = 252, 79, 255
green = 0, 143, 17
dark_green = 0, 50, 0

# Initialize pygame
pygame.init()

clock = pygame.time.Clock()

size = width, height = 911, 911
screen = pygame.display.set_mode(size)
pygame.display.set_caption("Waking Life")

screen.fill(gray)


RNG = np.random.default_rng(42)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# WORLD CONSTANTS
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
MAP_CENTER = np.array([0.0 + width / 2, 0.0 + height / 2])
MAP_SIZE = width / 4
N_CELLS = 20
CELL_SIZE = S = MAP_SIZE / N_CELLS

H = 2 * S
W = np.sqrt(3.0) * S
H_SPACING = 3 / 4 * H
V_SPACING = W

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# WORLD GENERATION
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@attr.s
class World(Mapping):
    grid = attr.ib()
    generation = attr.ib(default=0)

    def __getitem__(self, k):
        """x[k] <=> x.__getitem__(k)."""
        return self.grid[k]

    def __iter__(self):
        """iter(x) <=> x.__iter__()."""
        return iter(self.grid.values())

    def __len__(self):
        """len(x) <=> x.__len__()."""
        return len(self.grid)

    def __getattr__(self, a):
        """getattr(x, y) <==> x.__getattr__(y) <==> getattr(x, y)."""
        return self[a]

    @property
    def nalive(self):
        return sum([int(cell.state) for cell in self])

    @classmethod
    def from_Nside(cls, N):
        cells = {}
        for q in range(-N, N + 1):
            for r in range(-N, N + 1):
                s = -q - r
                if np.abs(s) <= N:
                    cells[(q, r)] = Cell(q, r, state=False)
        return World(cells)

    @staticmethod
    def qr2xy(q, r):
        return

    @staticmethod
    def xy2qr(x, y):
        return

    def evolve(self):
        new_world = {}
        for cell in self:
            # print(cell)
            new_state = cell.apply_rules(current_world=self)
            # print((cell.q, cell.r), new_state)
            new_world[(cell.q, cell.r)] = Cell(
                cell.q, cell.r, state=new_state, rules=cell.rules
            )
        return World(new_world, generation=self.generation + 1)
        # return World(new_world, generation=self.generation + 1)


@attr.s
class Cell:
    """Cell object.

    Following axial coordinates system:
    https://www.redblobgames.com/grids/hexagons/
    """

    q = attr.ib()
    r = attr.ib()
    state = attr.ib(validator=attr.validators.instance_of(bool))
    rules = attr.ib()

    @rules.default
    def _rules_default(self):
        return [rule_to_born, rule_to_die]  # , rule_to_mutate]

    @property
    def s(self):
        return -self.q - self.r

    @property
    def center(self):
        x = W * (self.s / 2 + self.q)
        y = 3 / 2 * S * self.s
        return np.array([x, y]) - MAP_CENTER

    @property
    def relative_corners(self):
        a = np.array([0, H / 2])
        b = np.array([-W / 2, H / 4])
        c = np.array([-W / 2, -H / 4])
        d = np.array([0, -H / 2])
        e = np.array([W / 2, -H / 4])
        f = np.array([W / 2, H / 4])
        return [a, b, c, d, e, f]

    @property
    def corners(self):
        return [rl - self.center for rl in self.relative_corners]

    # @property
    def living_neighbors(self, current_world, levels=1):
        alive = 0
        q, r, s = self.q, self.r, self.s

        for nq in [q - levels, q, q + levels]:
            for nr in [r - levels, r, r + levels]:
                ns = -nq - nr
                # check for s whitin levels
                if np.abs(s - ns) >= levels + 1:
                    continue
                # check for self
                if (nq == q) and (nr == r):
                    continue
                # check for edges
                if (nq, nr) not in current_world:
                    continue
                alive += int(current_world[nq, nr].state)
        return alive

    def apply_rules(self, current_world):
        results = [rule(self, current_world) for rule in self.rules]
        return any(results)

    # Draw methods
    def draw(self, screen):
        if self.state:
            pygame.draw.polygon(screen, green, self.corners)
        else:
            pygame.draw.polygon(screen, gray, self.corners)
            self.draw_edges(screen)

    def draw_edges(self, screen):
        corners = self.corners
        for i, icorner in enumerate(corners):
            pygame.draw.line(screen, dark_green, icorner, corners[i - 1])

    def draw_corners(self, screen):
        corners = self.corners
        for i, icorner in enumerate(corners):
            pygame.draw.circle(screen, green, icorner, 3)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# SET OF RULES
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def rule_to_die(cell, world):
    n = cell.living_neighbors(world, levels=1)
    if cell.state and (n in [2, 3, 4]):
        return True
    return False


def rule_to_born(cell, world):
    n = cell.living_neighbors(world, levels=1)
    if not cell.state and n == 4:
        return True
    return False


def rule_to_mutate(cell, world):
    mutation_p = 0.001
    p = RNG.uniform(0, 1, size=1)
    if p < mutation_p:
        return ~cell.state
    return None


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# MAIN
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def random_population(world, percentage):
    nalive = int(len(world) * percentage / 100)
    rand_cells = RNG.choice(list(world.grid.values()), nalive, replace=False)
    for cell in rand_cells:
        cell.state = True
    return World(world.grid, generation=0)


# Center of the world
pygame.draw.circle(screen, white, MAP_CENTER, 3)

# Create cells
world = World.from_Nside(N_CELLS)

# initial random state
world = random_population(world, percentage=40)


# Draw intial map
for cell in world:
    cell.draw_edges(screen)

font = pygame.font.SysFont("verdana", 16)


def show_score(x, y, score):
    t = font.render(f"Living: {score}", True, white, gray)
    screen.blit(t, (x, y))


def show_FPS(x, y, fps):
    t = font.render(f"FPS: {fps:.1f}", True, white, gray)
    screen.blit(t, (x, y))


print(f"Number of cells: {len(world)}/{world.nalive}")
print(len(world.grid))

status = True
while status:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            status = False
        if event.type == pygame.MOUSEBUTTONUP:
            world = random_population(world, 20)

    t0 = time.time_ns()
    world = world.evolve()
    screen.fill(gray)
    for cell in world:
        cell.draw(screen)

    show_score(10, 10, world.nalive)
    dt = (time.time_ns() - t0) / 1e9
    fps = 1 / dt
    show_FPS(10, 30, fps)

    pygame.display.update()
    clock.tick(20)
