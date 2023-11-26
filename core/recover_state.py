"""Functions for recovering the internal Xorshift state from Math.random outputs"""

from functools import partial
from struct import pack, unpack
from typing import Iterable, Sequence
import numpy as np
from . import gf2
from .xorshift import Xorshift, XorshiftSpiderMonkey, XorshiftV8


def extract_observation(double: float, v8: bool) -> int:
    """Extract observable bits from Math.random() result"""
    if v8:
        return unpack("<Q", pack("d", double + 1.0))[0] & 0xFFFFFFFFFFFFF  # type: ignore
    as_int: int = unpack("<Q", pack("d", double))[0]
    return (as_int >> (1022 - (as_int >> 52))) & 1


# state bit size x observation bit size
# V8 generates 52 observable bits for the double mantissa
# s0 >> 12
# 4 doubles are needed to recover the entire state without bruteforce
# up to 64 doubles are needed to align the cache
OBSERVATION_MATRIX_V8 = np.zeros((128, 4 * 52), np.uint8)
rng: Xorshift
for state_bit_i in range(128):
    state = 1 << state_bit_i
    rng = XorshiftV8((state & 0xFFFFFFFFFFFFFFFF, state >> 64))
    for observation_i in range(4):
        # extract mantissa
        observation: int = extract_observation(rng.math_random(), v8=True)
        OBSERVATION_MATRIX_V8[
            state_bit_i,
            observation_i * 52 : (observation_i + 1) * 52,
        ] = gf2.int_to_gf2vec(observation, 52)

LEFT_NULLBASIS_V8 = gf2.left_nullbasis(OBSERVATION_MATRIX_V8)
INVERSE_V8 = gf2.generalized_inverse(OBSERVATION_MATRIX_V8)

# SpiderMonkey generates 52 observable bits but only the LSB directly correlates to the state
# (s0 + s1) & ((1 << 53) - 1)
# (s0 + s1) & 1 == (s0 & 1) ^ (s0 & 1)
# 128 doubles are needed to recover the state without bruteforce
OBSERVATION_MATRIX_SPIDER_MONKEY = np.zeros((128, 128), np.uint8)

for state_bit_i in range(128):
    state = 1 << state_bit_i
    rng = XorshiftSpiderMonkey((state & 0xFFFFFFFFFFFFFFFF, state >> 64))
    for observation_i in range(128):
        # extract mantissa
        observation = extract_observation(rng.math_random(), v8=False)
        OBSERVATION_MATRIX_SPIDER_MONKEY[state_bit_i, observation_i] = observation

LEFT_NULLBASIS_SPIDER_MONKEY = gf2.left_nullbasis(OBSERVATION_MATRIX_SPIDER_MONKEY)
INVERSE_SPIDER_MONKEY = gf2.generalized_inverse(OBSERVATION_MATRIX_SPIDER_MONKEY)


def recover_rng(observations: Sequence[float], v8: bool) -> Iterable[Xorshift]:
    """Recover possible Xorshift internal states from Math.random() results"""
    if v8:
        observation_matrix = OBSERVATION_MATRIX_V8
        nullbasis = LEFT_NULLBASIS_V8
        inverse_matrix = INVERSE_V8
        observation_size = 52
    else:
        observation_matrix = OBSERVATION_MATRIX_SPIDER_MONKEY
        nullbasis = LEFT_NULLBASIS_SPIDER_MONKEY
        inverse_matrix = INVERSE_SPIDER_MONKEY
        observation_size = 1
    observed_bits = np.concatenate(
        tuple(
            map(
                partial(gf2.int_to_gf2vec, size=observation_size),
                map(
                    partial(extract_observation, v8=v8),
                    observations[:4] if v8 else observations[:128],
                ),
            )
        )
    )
    principal_solution = (observed_bits @ inverse_matrix) & np.uint8(1)
    for result_i in range(1 << len(nullbasis)):
        solution = gf2.apply_left_nullspace(nullbasis, principal_solution, result_i)
        if np.all((solution @ observation_matrix) & 1 == observed_bits):
            integer_solution = gf2.gf2vec_to_int(solution)
            integer_state = (
                integer_solution & 0xFFFFFFFFFFFFFFFF,
                integer_solution >> 64,
            )
            test_rng: Xorshift
            if v8:
                test_rng = XorshiftV8(integer_state)
                # align the cache properly
                offset = None
                for offset, obs in enumerate(observations):
                    if obs != test_rng.math_random():
                        break
                assert offset is not None
                for _ in range(offset):
                    test_rng.prev_state()
                test_rng.cache = []
                for _ in range(64 - offset):
                    test_rng.math_random()
            else:
                test_rng = XorshiftSpiderMonkey(integer_state)
            valid = True
            for obs in observations:
                if obs != test_rng.math_random():
                    valid = False
                    break
            if valid:
                yield test_rng
