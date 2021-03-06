# Church's lambda calculus

true_ = lambda x: lambda y: x
false_ = lambda x: lambda y: y

not_ = lambda x: x (false_) (true_)
and_ = lambda x: lambda y: (x (true_) (false_)) (y (true_) (false_)) (false_)
or_ = lambda x: lambda y: (x) (true_) ((y) (true_) (false_))

nand_ = lambda x: lambda y: (not_) (and_ (x) (y))
nor_ = lambda x: lambda y: (not_) (or_ (x) (y))
xor_ = lambda x: lambda y: (and_) (or_ (x) (y)) (nand_ (x) (y))

print_bool = lambda f: print(f (True) (False))  # show which bool it is

for op in [and_, or_, nand_, nor_, xor_]:
    for a in [true_, false_]:
        for b in [true_, false_]:
            print_bool(op (a) (b))
    print()

y_ = lambda f: (lambda x: f (x) (x)) (lambda x: f (x) (x))

# Church numerals
zero_ = lambda f: lambda x: x
one_ = lambda f: lambda x: f (x)
succ_ = lambda n: lambda f: lambda x: f (n) (f (x))

plus_ = lambda a, b: None  # TODO
minus_ = lambda a, b: None  # TODO
factorial_ = lambda n: None  # TODO
