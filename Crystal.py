class States:
    EXISTING = 2
    NEW = 1
    EMPTY = 0

    STR = "-OX"

    @staticmethod
    def get_char(state):
        return States.STR[state]


class Grid:
    def __init__(self, side_length):
        self.side_length = side_length
        self.grid = [[States.EMPTY for i in range(side_length)] for j in range(side_length)]
        self.points_by_state = {state: set() for state in range(100)}  # please don't use more than 100 states
        self.points_by_state[States.EMPTY] = {(i, j) for j in range(side_length) for i in range(side_length)}
        self.state_ordering = [States.EMPTY, States.NEW, States.EXISTING]

    def get_state_at(self, point):
        return self.grid[point[0]][point[1]]

    def set_state_at(self, point, new_state, maintain_ordering=True):
        old_state = self.get_state_at(point)
        self.points_by_state[old_state].remove(point)
        new_state = self.get_higher_state(old_state, new_state)
        self.grid[point[0]][point[1]] = new_state
        self.points_by_state[new_state].add(point)

    def set_state_at_point_array(self, point_array, new_state_array):
        for p_row, s_row in zip(point_array, new_state_array):
            for point, state in zip(p_row, s_row):
                self.set_state_at(point, state)

    def get_higher_state(self, s1, s2):
        return max([s1, s2], key=lambda x: self.state_ordering.index(x))

    def grow(self, growth_rules):
        points_to_grow = [p for p in self.points_by_state[States.NEW]]  # avoid "set changed size during iteration"
        for point in points_to_grow:
            neighbors = self.get_neighbors(point)
            neighbor_states = self.get_state_array(neighbors)
            # grow the neighbors depending on the rules
            rule_matches = [(env, rule.resulting_environment) for env, rule in growth_rules.rules.items() if rule.applies(neighbor_states)]

            if len(rule_matches) == 1:
                # apply growth rule
                k, resulting_environment = rule_matches[0]
                print("rule applied at point {} with environment\n{}\nand resulting environmment\n{}".format(point, neighbor_states, resulting_environment))
                self.set_state_at_point_array(neighbors, resulting_environment)
            elif len(rule_matches) > 1:
                raise Exception("should not match more than one rule because GrowthRuleSet's rules should have at most one rule for each environment\nrule matches: {}".format(rule_matches))
            else:
                # do nothing, just mark the current point as existing
                print("no rule applied at point {} with environment\n{}".format(point, neighbor_states))
                pass

            self.set_state_at(point, States.EXISTING)

    def get_neighbors(self, point):
        # still includes point's coordinates too; this should not be changed, so we are dealing with 3x3 arrays as much as possible
        x, y = point
        n = self.side_length
        return [
            [((x-1)%n, (y-1)%n), ((x  )%n, (y-1)%n), ((x+1)%n, (y-1)%n)],
            [((x-1)%n, (y  )%n), ((x  )%n, (y  )%n), ((x+1)%n, (y  )%n)],
            [((x-1)%n, (y+1)%n), ((x  )%n, (y+1)%n), ((x+1)%n, (y+1)%n)],
        ]

    def get_state_array(self, point_array):
        return [[self.get_state_at(p) for p in row] for row in point_array]

    def print(self):
        print("/" + "-" * (2 * self.side_length - 1) + "\\")
        for row in self.grid:
            print("|" + " ".join(States.get_char(state) for state in row) + "|")
        print("\\" + "-" * (2 * self.side_length - 1) + "/")


class GrowthRuleSet:
    def __init__(self):
        self.rules = {}

    def add(self, rule):
        key = rule.existing_environment
        value = rule.resulting_environment
        equivalent_keys = get_rotations_and_reflections(key)
        equivalent_values = get_rotations_and_reflections(value)
        # ordering of keys and values should correspond, given that the function generating them maintains ordered output
        for k, v in zip(equivalent_keys, equivalent_values):
            k = array_to_tuple(k)
            rule = GrowthRule(k, v)
            self.rules[k] = rule


class GrowthRule:
    def __init__(self, existing_environment_1s_and_0s, resulting_environment_1s_and_0s):
        self.existing_environment = GrowthRule.convert_1s_and_0s_to_state(existing_environment_1s_and_0s, States.EXISTING)
        self.resulting_environment = GrowthRule.convert_1s_and_0s_to_state(resulting_environment_1s_and_0s, States.NEW)

    def applies(self, environment):
        print("seeing if rule with existing environment\n{}\nand resulting environment\n{}\napplies to environment\n{}".format(self.existing_environment, self.resulting_environment, environment))
        environment = GrowthRule.filter_state_array(environment, States.EXISTING)
        print("filtered_environment:\n{}".format(environment))
        print("result: {}\n\n".format(environment == self.existing_environment))
        return environment == self.existing_environment

    @staticmethod
    def convert_1s_and_0s_to_state(input_arr, output_state):
        # changed condition from == 1 to != 0 because the rules have already been initialized (and thus their 1s converted to >= 1) before GrowthRuleSet.add is called, and don't want the existing environment to be overwritten to all zeros because the 1s were already changed to 2s
        return [[output_state if cell != 0 else 0 for cell in row] for row in input_arr]

    @staticmethod
    def filter_state_array(input_arr, state_to_keep):
        return [[x if x == state_to_keep else 0 for x in row] for row in input_arr]

    # guidelines for rules:
    # - middle cell should be States.NEW (the one that is being grown, because it hasn't yet done so due to just having sprouted from an older growth)
    # - pay attention only to States.EXISTING for the environment; do not pay attention to new cells, so that each iteration of growth occurs simultaneously


def get_rotations_and_reflections(arr):
    # output must be ordered
    result = []
    for rotation in get_rotations(arr):
        result += [rotation, get_reflection(rotation)]
    return result


def get_rotations(arr):
    f = rotate_right
    return [arr, f(arr), f(f(arr)), f(f(f(arr)))]  # don't optimize prematurely


def rotate_right(arr):
    assert len(arr) == 3 and all(len(x) == 3 for x in arr)  # whatever, generalize it later if you need to
    return [
        [arr[2][0], arr[1][0], arr[0][0],],
        [arr[2][1], arr[1][1], arr[0][1],],
        [arr[2][2], arr[1][2], arr[0][2],],
    ]


def get_reflection(arr):
    # just use one axis; if you want reflection along the other, use rotations as well
    return [row[::-1] for row in arr]


def is_equivalent(arr1, arr2):
    return any(arr1 == x for x in get_rotations_and_reflections(arr2))


def array_to_tuple(arr):
    return tuple(tuple(x for x in row) for row in arr)



if __name__ == "__main__":
    grid = Grid(31)

    seed_position_array_1 = [
        [(15, 15),],
    ]
    seed_position_array_2 = [
        [(14, 15),],
        [(15, 14), (15, 16),],
    ]

    seed_position_array = seed_position_array_1
    seed_state_array = [[States.NEW for cell in row] for row in seed_position_array]

    grid.set_state_at_point_array(seed_position_array, seed_state_array)

    growth_rules = GrowthRuleSet()
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ],
        [
            [1, 0, 1],
            [0, 0, 0],
            [1, 0, 1],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [0, 0, 0],
            [0, 1, 0],
        ],
        [
            [1, 0, 1],
            [0, 0, 0],
            [0, 1, 0],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [0, 0, 0],
            [1, 0, 0],
        ],
        [
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [0, 0, 0],
            [1, 1, 0],
        ],
        [
            [0, 1, 1],
            [0, 0, 0],
            [1, 1, 0],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [0, 0, 0],
            [1, 0, 1],
        ],
        [
            [0, 1, 0],
            [0, 0, 0],
            [1, 0, 1],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [0, 0, 0],
            [1, 1, 1],
        ],
        [
            [0, 1, 0],
            [0, 0, 0],
            [1, 1, 1],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [1, 0, 1],
            [1, 0, 1],
        ],
        [
            [0, 1, 0],
            [1, 0, 1],
            [1, 0, 1],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [1, 0, 1],
            [0, 0, 0],
        ],
        [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
        ],
    ))
    growth_rules.add(GrowthRule(
        [
            [0, 0, 0],
            [1, 0, 1],
            [0, 1, 0],
        ],
        [
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0],
        ],
    ))

    # for rule in growth_rules.rules:
    #     print(rule)

    grid.print()
    for i in range(10):
        input("\npress enter to continue\n")
        grid.grow(growth_rules)
        grid.print()
