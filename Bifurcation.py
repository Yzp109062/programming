import matplotlib.pyplot as plt


def logistic_map(x, r):
    return r * x * (x - 1)


def iterate(f, x0, *args, **kwargs):
    x = x0
    while True:
        yield x
        x = f(x, *args, **kwargs)


def get_iterations(f, x0, n0, n1, *args, **kwargs):
    # get n0-th through n1-th iterations
    g = iterate(f, x0, *args, **kwargs)
    for _ in range(n0):
        next(g)  # throw it away
    return [next(g) for _ in range(n1 - n0)]


def find_equilibria(f, x0, *args, **kwargs):
    # how to do this, finding where it converges?
    # could specify some large N, find the range of the orbit between, say, N and N+1024 steps. Plot all those points.
    N = 10000
    n = 1024
    iterations = get_iterations(f, x0, N, N+n, *args, **kwargs)
    return sorted(set(iterations))


def scatter(f, x0, n0, n1, *args, **kwargs):
    ys = get_iterations(f, x0, n0, n1, *args, **kwargs)
    plt.scatter(range(n0, n1), ys)
    plt.show()


# def plot_equilibria(f, x0, *args, **kwargs):
#     plt.


def plot_bifurcation_diagram(f, x0, arg_range_min, arg_range_max):
    # f should be func of one variable, plotting only bifurcation along that one and holding all else constant
    assert f.__code__.co_argcount == 1, "f must be function of one variable for bifurcation plot"
    raise Exception("TODO")


if __name__ == "__main__":
    scatter(logistic_map, 0.01, 10000, 11024, 3.8)
    scatter((lambda x: (2*x+1) % 100), 0, 10000, 11024)  # test


