"""Xorshift128+ implementations used in JavaScript Engines"""

from abc import abstractmethod
from struct import pack, unpack
from array import array
from typing import Collection


class Xorshift:
    """Xorshift128+ implementation used in JavaScript Engines"""

    def __init__(self, seed: Collection[int]) -> None:
        self.state = array("Q", seed)

    def next_state(self) -> None:
        """Advance the internal Xorshift state"""
        seed_1, seed_0 = self.state
        self.state[0] = seed_0
        seed_1 ^= (seed_1 << 23) & 0xFFFFFFFFFFFFFFFF
        self.state[1] = seed_1 ^ seed_0 ^ (seed_1 >> 17) ^ (seed_0 >> 26)

    def prev_state(self) -> None:
        """Undo an advance to the internal Xorshift state"""
        seed_0, seed_1 = self.state
        seed_1 ^= seed_0 ^ (seed_0 >> 26)
        seed_1 ^= seed_1 >> 17
        seed_1 ^= seed_1 >> 34
        seed_1 ^= (seed_1 << 23) & 0xFFFFFFFFFFFFFFFF
        seed_1 ^= (seed_1 << 46) & 0xFFFFFFFFFFFFFFFF
        self.state[0] = seed_1
        self.state[1] = seed_0

    @abstractmethod
    def math_random(self) -> float:
        """Implementation of JavaScript's Math.random"""


class XorshiftV8(Xorshift):
    """Xorshift algorithm used in Google Chrome's V8 engine"""

    def __init__(self, seed: Collection[int]) -> None:
        super().__init__(seed)
        self.cache: list[float] = []

    def math_random(self) -> float:
        if not self.cache:
            for _ in range(64):
                self.cache.append(
                    unpack("d", pack("<Q", (self.state[0] >> 12) | 0x3FF0000000000000))[
                        0
                    ]
                    - 1.0
                )
                self.next_state()
        return self.cache.pop()


class XorshiftSpiderMonkey(Xorshift):
    """Xorshift algorithm used in FireFox's SpiderMonkey engine"""

    def math_random(self) -> float:
        self.next_state()
        rand = (self.state[0] + self.state[1]) & 0x1FFFFFFFFFFFFF
        bit_length = rand.bit_length()
        result: float = unpack(
            "d",
            pack(
                "<Q",
                ((rand - (1 << (bit_length - 1))) << (53 - bit_length))
                | ((969 + bit_length) << 52),
            ),
        )[0]
        return result
