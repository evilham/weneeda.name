from itertools import dropwhile

import mmh3
import pytest

from hashing import hash_generator, hash_parts_generator

def test_hash_generator_imperative():
    """Test usage of hash_generator in an imperative way.

    With 4 items and range 2**128, this should be collision-free (and the
    seed is deterministic :D), so it should be equivalent to just mmh3.
    """
    my_hashes = []
    to_hash = ['a', 'b', 'c', 'd']
    for thing in to_hash:
        for h in hash_generator(thing):
            if h not in my_hashes:
                my_hashes.append(h)
                break
    assert my_hashes == [mmh3.hash128(x, seed=42) for x in to_hash]

def test_hash_generator_functional():
    """Test usage of hash_generator in an imperative way.

    With 4 items and range 2**128, this should be collision-free (and the
    seed is deterministic :D), so it should be equivalent to just mmh3.
    """
    my_hashes = []
    to_hash = ['a', 'b', 'c', 'd']

    def has_collision(h):
        return h in my_hashes

    for thing in to_hash:
        h = next(dropwhile(has_collision, hash_generator(thing)))
        my_hashes.append(h)

    assert my_hashes == [mmh3.hash128(x, seed=42) for x in to_hash]

def test_hash_collisions_handled():
    """Test usage of hash_generator with collisions.

    With 6 items and range 25, a collision is likely to occur (birthday paradox).
    We should still be able to fit all items (with decent probability and it's deterministic :D).
    """
    to_hash = ['a', 'b', 'c', 'd', 'e', 'f']
    my_hashes = {}

    def has_collision(h):
        return h in my_hashes

    for thing in to_hash:
        h = next(dropwhile(has_collision, hash_generator(thing, range=25)))
        my_hashes[h] = thing
    assert my_hashes != [mmh3.hash128(x, seed=42) for x in to_hash], "a collision occured"
    assert len(my_hashes) == 6, "we fit all items"

def test_table_full_handled():
    """Test usage of hash_generator with collisions.

    With 4 items and range 3, an unresolvable collision must occur (pidgeonhole principle).
    We should not loop infinitely like idiots :D
    """
    to_hash = [b'a', b'b', b'c', b'd']
    my_hashes = {}

    def has_collision(h):
        return h in my_hashes

    with pytest.raises(StopIteration): # I should be unable to find a non-colliding hash at some point, so my generator will run out
        for thing in to_hash:
            h = next(dropwhile(has_collision, hash_generator(thing, range=3)))
            my_hashes[h] = thing
    assert len(my_hashes) == 3, "we fit what we could"

def test_hash_parts_generator():
    N = 4000
    PARTS = 3
    RANGE = 20
    my_hashes = []
    to_hash = [str(i) for i in range(N)]

    def has_collision(h):
        return h in my_hashes

    for thing in to_hash:
        h = next(dropwhile(has_collision, hash_parts_generator(thing, PARTS, RANGE)))
        # print(thing, h)
        my_hashes.append(h)

    assert len(my_hashes) == N, "no unresolvable collisions occured"
    for h in my_hashes:
        assert len(h) == PARTS
        for part in h:
            assert 0 <= part < RANGE

def test_hash_does_not_repeat():
    all_hashes = list(hash_generator("hi", range=1000))
    assert len(all_hashes) == len(set(all_hashes)), "hashes are unique"

def test_hash_is_deterministic():
    assert list(hash_generator("hi", range=42)) == [7, 19, 31, 1, 13, 25, 37]
