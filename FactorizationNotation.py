import math
import random
import sympy
import turtle

import LSystem


# parentheses surrounding a group means it is in prime factor notation
# ultimately all ints except 0 can be written in factor notation


def factor_one_level(n):
    if n == 1:
        return [0]  # otherwise sympy will just return an empty array; I'll use a convention where 1 is "(0)" rather than "()"
    factors = sympy.ntheory.factorint(n)
    array = []
    for p, exp in sorted(factors.items()):
        prime_index = sympy.ntheory.generate.primepi(p) - 1
        if len(array) < prime_index + 1:
            array += [0] * (prime_index + 1 - len(array))
        array[prime_index] = exp
    return array[::-1]  # larger primes on the left


def integer_to_factor_notation(n, factor_one=True):
    if n == 0:
        return "0"
    if n == 1 and not factor_one:
        return "1"
    array = factor_one_level(n)
    factored = factor_one_level(n)
    return "(" + "".join(integer_to_factor_notation(x, factor_one) for x in factored) + ")"


def factor_notation_to_integer(s):
    if s == "0":
        return 0
    groups = get_top_level_groups(s)
    array = [factor_notation_to_integer(x) for x in groups]
    primes = map(sympy.ntheory.prime, range(1, len(array) + 1))
    return product_exp(primes, array[::-1])


def product_exp(a, b):
    result = 1
    for x, y in zip(a, b):
        result *= x ** y
    return result


def get_top_level_groups(s):
    assert s[0] == "(" and s[-1] == ")", "invalid string; all groups in factorization notation must be surrounded by parentheses"
    s = s[1: -1]
    groups = []
    current = ""
    paren_count = 0

    for x in s:
        current += x
        if x == "(":
            paren_count += 1
        elif x == ")":
            paren_count -= 1
        assert paren_count >= 0
        if paren_count == 0 and current != "":
            groups.append(current)
            current = ""
    assert paren_count == 0 and current == "", "count {}, current {}".format(paren_count, current)
    return groups


def test():
    for _ in range(10):
        n = random.randint(1, 1e6)
        s = integer_to_factor_notation(n)
        assert n == factor_notation_to_integer(s)


if __name__ == "__main__":
    test()

    n = (2 ** 6) * (3 ** 4) * (5 ** 5)
    # n = (2 ** 16) - 1
    # n = 16 * 3
    # n = 7
    # n = 2
    # print(integer_to_factor_notation(n))
    # s = "(((0))(0))"  # 3^2 * 2 = 18
    s = "((((0)0)0)0)"  # 3^(3^3) = 7625597484987
    # print(factor_notation_to_integer(s))

    # now make turtle graphics from the notation of different numbers (treating them as L-Systems)

    snowflake_rule_dict = {
        "0": LSystem.LSystemRule("0", {"0)0(0(0)0": 1, "0": 0}),
    }
    rule_dict = {
        "(": LSystem.LSystemRule("(", {"((0)": 0.5, "(": 0.5}),
        ")": LSystem.LSystemRule(")", {"(0))": 0.5, ")": 0.5}),
        "0": LSystem.LSystemRule("0", {"(0)": 0.5, "0": 0.5}),
    }
    turtle_dict = {
        "(": ["L90", "F2"],
        ")": ["R90", "F2"],
        "0": ["F2"],
    }
    system = LSystem.LSystem(rule_dict, turtle_dict)
    snowflake_system = LSystem.LSystem(snowflake_rule_dict, turtle_dict)

    # What is the series of numbers generated by square Koch snowflake?
    # [1, 40, a_2 > 5^2500, ...]
    # start_str = "(0)"
    # n_iterations = 1
    # res = snowflake_system.apply_iterated(start_str, n_iterations, max_length=10000)
    # res = "(" * n_iterations + res + ")" * n_iterations
    # print(res)
    # print(factor_notation_to_integer(res))  # for this curve, series grows explosively (2 iterations is already far too big of a number)
    # snowflake_system.plot(res)

    # generate random factorization, give int and plot
    # start_str = "(0)"
    # res = system.apply_iterated(start_str, 3, max_length=10000)
    # print(res)
    # print(math.log(factor_notation_to_integer(res), 10))
    # system.plot(res)

    # generate random int of reasonable size and composite-ness, plot
    def get_composite_n():
        n = 1
        for _ in range(100):
            p = 2
            while random.random() < 0.9:
                p = sympy.ntheory.nextprime(p)
            n *= p
        return n

    n = get_composite_n()
    print(n)
    s = integer_to_factor_notation(n)
    print(s)
    system.plot(s)