import mmh3

def hash_generator(s, range=2**128, seed1=42, infinite=False):
    """Generator that returns a list of hashes of the input.

    The list is deterministic, so the intended usage is to keep getting hashes
    until you don't have a collision:

        for h in hash_generator(my_input):
            if <collision free>:
                do_something_with_the_hash
                break

    or, in a more functional way:

        def has_collision(h):
            ...

        good_hash = next(dropwhile(has_collision, hash_generator(thing)))

    @param s: input string or bytes

    @param range: Return a number between 0 and range instead of the full range of the hash

    It implements double hashing (https://en.wikipedia.org/wiki/Double_hashing)
    using MurmurHash3.
    """
    print("*** hash_generator: range", range)
    i = 0
    # First hash: absolute offset / base
    base = mmh3.hash128(s, seed=seed1) % range
    h = base
    yield h
    # Second hash: yield hashes in consecutive intervals determined by the
    # second hash
    interval = 1 + mmh3.hash128(s, seed=seed1+47)  # must not be 0; must be independent of the first hash
    while h != base:
        h = (h + interval) % range
        yield h
    print("stopping after {} iterations".format(i))

def hash_parts_generator(s, count_parts, part_range):
    """This gives up too early!"""
    hashgens = [hash_generator(s, part_range, seed1=i) for i in range(count_parts)]
    return zip(*hashgens)

def hash_parts_generator2(s, count_parts, part_range):
    """This is horribly broken somehow :D"""
    for h in hash_generator(s, range=count_parts*part_range):
        print('***', h)
        yield tuple([((h % (part_range**i)) // (part_range**(i-1))) for i in range(count_parts)])
