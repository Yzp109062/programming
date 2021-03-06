import matplotlib.pyplot as plt


MEMO = {}

def f(n):
    assert n > 0, "{} <= 0".format(n)

    designations = list(range(1, n+1))

    # memoization
    if n in MEMO:
        return MEMO[n]
    elif n >= 3 and (n-1) in MEMO:
        # make list of length n-1, note that 1 always kills 2 first, then it is 3's turn
        # don't bother doing this if n is just 2, so we don't have to worry about the index

        # try getting value directly without making a list, note that 1 -> 3, x -> x+2, etc. except last_item -> 1
        # new_designations = designations[2:] + [designations[0]]
        # assert len(new_designations) == n-1
        f_n_minus_1 = f(n-1)  # remember that this is 1-indexed, don't worry about function call overhead
        # index_to_get = f_n_minus_1 - 1
        # result = new_designations[index_to_get]
        # MEMO[n] = result
        # return result
        if f_n_minus_1 == n-1:  # last item in list maps to 1
            result = 1
        else:
            result = f_n_minus_1 + 2
        MEMO[n] = result
        return result

    statuses = [1 for person in designations]
    current_index = 0
    increment = lambda index: (index + 1) % n
    n_left = n
    while n_left > 1:
        assert statuses[current_index] == 1  # current person must be alive
        next_index = increment(current_index)
        while statuses[next_index] == 0:
            next_index = increment(next_index)
        # now kill this person
        statuses[next_index] = 0
        n_left -= 1
        # now get next living person as current index, note that they will not be any of the ones we just checked, nor the one that just died
        # if current index is the last one then it will loop around to them again; can only infinite loop if no one is alive
        current_index = increment(next_index)
        while statuses[current_index] == 0:
            current_index = increment(current_index)
        # go again, this current index kills next living person, unless they are the last one
    result = designations[current_index]
    MEMO[n] = result
    return result


# later may be able to use memoized results for smaller n
# for instance, say in the case of N you have whittled it down to four people left with designations [11, 12, 205, 894]
# then you can just look up the answer for n=4 and get that member of this list (depending on whose turn it is)
# so you can actually just use f(n-1) and build up that way


if __name__ == "__main__":
    # a = 1000
    # for i in range(a, 101*a, a):
    #     print(i, f(i))
    xs = list(range(1, 10001))
    ys = [f(x) for x in xs]
    plt.scatter(xs, ys)
    plt.show()
