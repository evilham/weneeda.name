import mmh3

def hash_generator(s, range=2**128):
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
    # First hash: absolute offset / base
    base = mmh3.hash128(s, seed=42) % range
    yield base

    # Second hash: yield hashes in intervals determined by the second hash
    h = base
    interval = 1 + mmh3.hash(s, seed=47, signed=False)  # must not be 0; must be independent of the first hash
    while True:
        h = (h + interval) % range
        yield h
        if h == base: break

def hash_parts_generator(s, count_parts, part_range):
    for h in hash_generator(s, range=part_range**count_parts):
        parts = [ ((h // (part_range**i)) % part_range) for i in range(count_parts) ]
        yield tuple(parts)
