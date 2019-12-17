import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def make_none_array(shape):
    a = np.empty(shape, dtype=float)
    a[:] = np.nan
    return a


def elevation_change_parabolic(d, max_d, max_change):
    b = max_d
    h = max_change
    return -h/(b**2) * (d**2) + 2*h/b * d

def elevation_change_linear(d, max_d, max_change):
    b = max_d
    h = max_change
    return h/b * d

def elevation_change_semicircle(d, max_d, max_change):
    b = max_d
    h = max_change
    return h/b * np.sqrt(2*b*d - d**2)

def elevation_change_inverted_semicircle(d, max_d, max_change):
    b = max_d
    h = max_change
    return h - h/b * np.sqrt(b**2 - d**2)

def elevation_change_sinusoidal(d, max_d, max_change):
    b = max_d
    h = max_change
    return h/2 * (1 + np.sin(np.pi/b * (d - b/2)))

def elevation_change_constant(d, max_d, max_change):
    return max_change

ELEVATION_CHANGE_FUNCTIONS = [
    elevation_change_parabolic,
    elevation_change_linear,
    elevation_change_semicircle,
    elevation_change_inverted_semicircle,
    elevation_change_sinusoidal,
    elevation_change_constant,
]


def get_land_and_sea_colormap():
    # see PrettyPlot.py
    linspace_cmap_forward = np.linspace(0, 1, 128)
    linspace_cmap_backward = np.linspace(1, 0, 128)
    blue_to_black = mcolors.LinearSegmentedColormap.from_list('BlBk', [
        mcolors.CSS4_COLORS["blue"], 
        mcolors.CSS4_COLORS["black"],
    ])
    land_colormap = mcolors.LinearSegmentedColormap.from_list('land', [
        mcolors.CSS4_COLORS["darkgreen"],
        mcolors.CSS4_COLORS["limegreen"],
        mcolors.CSS4_COLORS["gold"],
        mcolors.CSS4_COLORS["darkorange"],
        mcolors.CSS4_COLORS["red"],
        mcolors.CSS4_COLORS["saddlebrown"],
        mcolors.CSS4_COLORS["gray"],
        mcolors.CSS4_COLORS["white"],
        # mcolors.CSS4_COLORS[""],
    ])
    # colors_land = plt.cm.YlOrBr(linspace_cmap_backward)  # example of how to call existing colormap object
    colors_land = land_colormap(linspace_cmap_forward)
    colors_sea = blue_to_black(linspace_cmap_backward)
    colors = np.vstack((colors_sea, colors_land))
    colormap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors)
    return colormap


class Map:
    def __init__(self, x_size, y_size):
        # really row size and column size, respectively
        self.x_size = x_size
        self.y_size = y_size
        self.array = make_none_array((x_size, y_size))
        self.filled_positions = set()
        self.unfilled_neighbors = set()
        self.unfilled_inaccessible = set()
        self.initialize_unfilled_inaccessible()

    def initialize_unfilled_inaccessible(self):
        for x in range(self.x_size):
            for y in range(self.y_size):
                self.unfilled_inaccessible.add((x, y))

    def size(self):
        return self.x_size * self.y_size

    def fill_position(self, x, y, value):
        self.array[x, y] = value
        return
        # old way
        raise Exception("do not use")
        assert (x, y) not in self.filled_positions
        assert self.filled_positions & self.unfilled_neighbors == set()
        assert self.filled_positions & self.unfilled_inaccessible == set()
        assert self.unfilled_neighbors & self.unfilled_inaccessible == set()
        self.array[x, y] = value
        self.filled_positions.add((x, y))
        self.unfilled_neighbors -= {(x, y)}
        self.unfilled_inaccessible -= {(x, y)}
        for neighbor_coords in self.get_neighbors(x, y):
            if neighbor_coords in self.unfilled_inaccessible:
                assert neighbor_coords not in self.unfilled_neighbors
                self.unfilled_neighbors.add(neighbor_coords)
                self.unfilled_inaccessible -= {neighbor_coords}

    def fill_point_set(self, point_set, value):
        for p in point_set:
            self.fill_position(p[0], p[1], value)

    def fill_all(self, value):
        for x in range(self.x_size):
            for y in range(self.y_size):
                self.fill_position(x, y, value)

    def get_value_at_position(self, x, y):
        return self.array[x, y]

    def get_neighbors(self, x, y):
        res = set()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_x = x + dx
                new_y = y + dy
                if new_x < 0 or new_x >= self.x_size:
                    continue
                if new_y < 0 or new_y >= self.y_size:
                    continue
                res.add((new_x, new_y))
        return res

    def get_random_path(self, a, b, points_to_avoid):
        # start and end should inch toward each other
        i = 0
        points_in_path = {a, b}
        current_a = a
        current_b = b
        while True:
            which_one = i % 2
            current_point = [current_a, current_b][which_one]
            objective = [current_b, current_a][which_one]
            points_to_avoid_this_step = points_to_avoid | points_in_path
            
            next_step = self.get_next_step_in_path(current_point, objective, points_to_avoid_this_step)
            if which_one == 0:
                current_a = next_step
            elif which_one == 1:
                current_b = next_step
            else:
                raise

            points_in_path.add(next_step)

            if current_a in self.get_neighbors(*current_b):
                break

            i += 1
        return points_in_path

    def get_next_step_in_path(self, current_point, objective, points_to_avoid):
        dx = objective[0] - current_point[0]
        dy = objective[1] - current_point[1]
        z = dx + dy*1j
        objective_angle = np.angle(z, deg=True)
        neighbors = self.get_neighbors(*current_point)
        neighbors = [n for n in neighbors if n not in points_to_avoid]
        neighbor_angles = [np.angle((n[0]-current_point[0]) + (n[1]-current_point[1])*1j, deg=True) for n in neighbors]
        # set objective angle to zero for purposes of determining weight
        neighbor_effective_angles = [abs(a - objective_angle) % 360 for a in neighbor_angles]
        neighbor_effective_angles = [a-360 if a>180 else a for a in neighbor_effective_angles]
        neighbor_weights = [180-abs(a) for a in neighbor_effective_angles]
        assert all(0 <= w <= 180 for w in neighbor_weights), "{}\n{}\n{}".format(neighbors, neighbor_effective_angles, neighbor_weights)
        total_weight = sum(neighbor_weights)
        norm_weights = [w / total_weight for w in neighbor_weights]
        chosen_one_index = np.random.choice([x for x in range(len(neighbors))], p=norm_weights)
        chosen_one = neighbors[chosen_one_index]
        return chosen_one

    def get_random_contiguous_region(self, expected_size, points_to_avoid=None, prioritize_internal_unfilled=False):
        assert expected_size > 1
        if points_to_avoid is None:
            points_to_avoid = set()
        center = None
        while center is None or center in points_to_avoid:
            center = self.get_random_point()
        points = {center}
        neighbors = [p for p in self.get_neighbors(*center) if p not in points_to_avoid]
        while True:
            if len(neighbors) == 0:
                break
            if prioritize_internal_unfilled:
                n_filled_neighbors_of_neighbors = [sum(n2 in points for n2 in self.get_neighbors(*n)) for n in neighbors]
                weights = [x/sum(n_filled_neighbors_of_neighbors) for x in n_filled_neighbors_of_neighbors]
                chosen_index = np.random.choice(list(range(len(neighbors))), p=weights)
                current_point = neighbors[chosen_index]
            else:
                current_point = random.choice(neighbors)
            points.add(current_point)
            neighbors = [p for p in self.get_neighbors(*current_point) if p not in points_to_avoid | points]
            if random.random() < 1/expected_size:
                break
        return points

    def get_distances_from_edge(self, point_set):
        if len(point_set) == 0:
            return {}
        res = {}
        points_on_edge = [p for p in point_set if any(n not in point_set for n in self.get_neighbors(*p))]
        for p in points_on_edge:
            res[p] = 1
        interior_point_set = point_set - set(points_on_edge)
        interior_distances = self.get_distances_from_edge(interior_point_set)
        for p, d in interior_distances.items():
            res[p] = d + 1
        return res

    def make_random_elevation_change(self, positive_feedback=False):
        reg = self.get_random_contiguous_region(1000, prioritize_internal_unfilled=True)
        raw_func = random.choice(ELEVATION_CHANGE_FUNCTIONS)
        distances = self.get_distances_from_edge(reg)
        max_d = max(distances.values())

        if positive_feedback:
            # land begets land, sea begets sea
            # point_in_region = random.choice(list(reg))
            # elevation_at_point = self.array[point_in_region[0], point_in_region[1]]
            elevations_in_region = [self.array[p[0], p[1]] for p in reg]
            average_elevation_in_region = np.mean(elevations_in_region)
            mu = average_elevation_in_region/2
        else:
            mu = 0

        big_abs_elevation = 100
        if abs(mu) > big_abs_elevation:
            # decrease mu linearly down to 0 at 2*big_abs_elevation, and then drop more after that to decrease
            big_elevation_signed = big_abs_elevation * (1 if mu > 0 else -1)
            mu_excess = mu - big_elevation_signed
            mu -= 2*mu_excess

        sigma = 10
        max_change = np.random.normal(mu, sigma)

        func = lambda d: raw_func(d, max_d, max_change)
        changes = {p: func(d) for p, d in distances.items()}
        for p, d_el in changes.items():
            current_el = self.get_value_at_position(*p)
            new_el = current_el + d_el
            self.fill_position(p[0], p[1], new_el)

    def get_random_point(self, border_width=0):
        x = random.randrange(border_width, self.x_size - border_width)
        y = random.randrange(border_width, self.y_size - border_width)
        return (x, y)

    def get_random_zero_loop(self):
        x0_0, y0_0 = self.get_random_point(border_width=2)
        dx = 0
        dy = 0
        while np.sqrt(dx**2 + dy**2) < self.x_size * 1/2 * np.sqrt(2):
            x0_1 = random.randrange(2, self.x_size - 2)
            y0_1 = random.randrange(2, self.y_size - 2)
            dx = x0_1 - x0_0
            dy = y0_1 - y0_0
        # x0_1 = (x0_0 + self.x_size // 2) % self.x_size  # force it to be considerably far away to get more interesting result
        # y0_1 = (y0_0 + self.y_size // 2) % self.y_size
        source_0 = (x0_0, y0_0)
        source_1 = (x0_1, y0_1)
        path_0 = self.get_random_path(source_0, source_1, points_to_avoid=set())
        path_1 = self.get_random_path(source_0, source_1, points_to_avoid=path_0)

        res = path_0 | path_1
        # print(res)
        return res


        raise Exception("go no further")
        # old way
        # trajectory_0 = [source_0]
        # trajectory_1 = [source_1]
        # display_arr = make_none_array((self.x_size, self.y_size))  # for debugging
        # display_arr = display_arr.astype(str)
        # display_arr[x, y] = "S"
        # LEFT = 0
        # RIGHT = -1
        # 
        # while True:
        #     # two starting points, each has two paths coming away from it
        #     # the paths from the same starting point are not allowed to intersect each other or themselves
        #     # when paths from different sources meet, cut off the paths and take the trajectories up to that point
        #     neighbors_0_left  = self.get_neighbors(*trajectory_0[0])
        #     neighbors_0_right = self.get_neighbors(*trajectory_0[-1])
        #     neighbors_1_left  = self.get_neighbors(*trajectory_1[0])
        #     neighbors_1_right = self.get_neighbors(*trajectory_1[-1])
        #     coords_0_left  = random.choice([p for p in neighbors_0_left if p not in trajectory_0])
        #     coords_0_right = random.choice([p for p in neighbors_0_right if p not in trajectory_0])
        #     coords_1_left  = random.choice([p for p in neighbors_1_left if p not in trajectory_1])
        #     coords_1_right = random.choice([p for p in neighbors_1_right if p not in trajectory_1])
        # 
        #     if coords_0_left in trajectory_1:
        #         cut_point = coords_0_left
        #         trajectory_0 = [coords_0_left] + trajectory_0
        #         # display_arr[coords_0] = "0"
        #         break
        #     elif coords_1_left in trajectory_0:
        #         cut_point = coords_1_left
        #         trajectory_1 = [coords_1_left] + trajectory_1
        #         # display_arr[coords_1] = "1"
        #         break
        # 
        #     trajectory_0 = [coords_0_left] + trajectory_0 + [coords_0_right]
        #     trajectory_1 = [coords_1_left] + trajectory_1 + [coords_1_right]
        #     # display_arr[coords_0] = "0"
        #     # display_arr[coords_1] = "1"
        #     # print(display_arr)
        #     # input("debug")
        # 
        # cut_index_0 = trajectory_0.index(cut_point)
        # cut_index_1 = trajectory_1.index(cut_point)
        # source_index_0 = trajectory_0.index(source_0)
        # source_index_1 = trajectory_1.index(source_1)
        # begin_0 = min(cut_index_0, source_index_0)
        # end_0 = max(cut_index_0, source_index_0)
        # begin_1 = min(cut_index_1, source_index_1)
        # end_1 = max(cut_index_1, source_index_1)
        # trajectory_0_cut = trajectory_0[begin_0 : end_0]
        # trajectory_1_cut = trajectory_1[begin_1 : end_1]
        # points = set(trajectory_0_cut) | set(trajectory_1_cut) | {cut_point}
        # for p in points:
        #     self.fill_position(p[0], p[1], 0)

    def add_random_zero_loop(self):
        points = self.get_random_zero_loop()
        for p in points:
            self.fill_position(p[0], p[1], 0)

    def fill_elevations_outward_propagation(self):
        # old
        raise Exception("do not use")
        # try filling the neighbors in "shells", get all the neighbors at one step and do all of them first before moving on
        # but that leads to a square propagating outward, so should sometimes randomly restart the list
        while len(self.unfilled_neighbors) + len(self.unfilled_inaccessible) > 0:
            to_fill_this_round = [x for x in self.unfilled_neighbors]
            random.shuffle(to_fill_this_round)
            for p in to_fill_this_round:
                # p = random.choice(list(self.unfilled_neighbors))
                # neighbor = random.choice([x for x in self.get_neighbors(*p) if x in self.filled_positions])
                # neighbor_el = self.get_value_at_position(*neighbor)
                filled_neighbors = [x for x in self.get_neighbors(*p) if x in self.filled_positions]
                average_neighbor_el = np.mean([self.get_value_at_position(*n) for n in filled_neighbors])
                d_el = np.random.normal(0, 100)
                el = average_neighbor_el + d_el
                self.fill_position(p[0], p[1], el)
                if random.random() < 0.02:
                    break  # for
                    # then will have new list of neighbors
            self.draw()

    def fill_elevations(self, n_steps, plot_every_n_steps=None):
        # touched_points = set()
        # while len(touched_points) < 0.95 * self.x_size * self.y_size:
        #     reg = self.get_random
        if plot_every_n_steps is not None:
            plt.ion()
        for i in range(n_steps):
            self.make_random_elevation_change(positive_feedback=True)
            if plot_every_n_steps is not None and i % plot_every_n_steps == 0:
                self.draw()

    def plot(self):
        self.pre_plot()
        plt.show()

    def draw(self):
        plt.gcf().clear()
        self.pre_plot()
        plt.draw()
        plt.pause(0.001)

    def pre_plot(self):
        # plt.imshow(self.array, interpolation="gaussian")  # History.py uses contourf rather than imshow
        min_elevation = self.array.min()
        max_elevation = self.array.max()
        n_sea_contours = 10
        n_land_contours = 30
        if min_elevation < 0:
            sea_contour_levels = np.linspace(min_elevation, 0, n_sea_contours)
        else:
            sea_contour_levels = [0]
        if max_elevation > 0:
            land_contour_levels = np.linspace(0, max_elevation, n_land_contours)
        else:
            land_contour_levels = [0]
        assert sea_contour_levels[-1] == land_contour_levels[0] == 0
        contour_levels = list(sea_contour_levels[:-1]) + list(land_contour_levels)
        colormap = get_land_and_sea_colormap()
        max_abs_elevation = abs(self.array).max()
        max_color_value = max_abs_elevation
        min_color_value = -1 * max_abs_elevation

        # draw colored filled contours
        plt.contourf(self.array, cmap=colormap, levels=contour_levels, vmin=min_color_value, vmax=max_color_value)

        # draw contour lines, maybe just one at sea level
        plt.contour(self.array, levels=[min_elevation, 0, max_elevation], colors="k")

        try:
            plt.colorbar()
        except IndexError:
            # np being stupid when there are too few contours
            pass


if __name__ == "__main__":
    m = Map(60, 100)
    m.fill_all(0)
    # n_steps = m.size()
    n_steps = 100000
    print("plotting {} steps".format(n_steps))
    m.fill_elevations(n_steps, plot_every_n_steps=100)
    m.plot()
