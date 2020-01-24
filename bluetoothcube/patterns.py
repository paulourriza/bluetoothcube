import re

from bluetoothcube.cubestate import FaceCube

from typing import List


# TODO: These functions deserve some unit tests.

def compile_pattern(s):
    base_pattern = "UUUUUUUUULLLFFFRRRBBBLLLFFFRRRBBBLLLFFFRRRBBBDDDDDDDDD"
    stripped = re.sub("\s+", "", s)
    faces = {f: [p for p, b in zip(stripped, base_pattern) if b == f]
             for f in "URFDLB"}
    return FaceCube(faces['U'] + faces['R'] + faces['F'] +
                    faces['D'] + faces['L'] + faces['B'])


def generate_variants_from_f(pattern: FaceCube) -> List[FaceCube]:
    return [pattern, pattern.rotated("x").rotated("x"),
            pattern.rotated("x"), pattern.rotated("x'"),
            pattern.rotated("y"), pattern.rotated("y'")]

def generate_corner_variants_from_f(pattern: FaceCube) -> List[FaceCube]:
    bottom = [pattern, pattern.rotated("x").rotated("x"),
            pattern.rotated("x"), pattern.rotated("x'")]
    top = [p.rotated("y").rotated("y") for p in bottom]        
    return bottom + top

GENERIC = [
    ("solved", compile_pattern("""
      U U U
      U U U
      U U U
L L L F F F R R R B B B
L L L F F F R R R B B B
L L L F F F R R R B B B
      D D D
      D D D
      D D D
""")),
    ("corners solved", compile_pattern("""
      U . U
      . U .
      U . U
L . L F . F R . R B . B
. L . . F . . R . . B .
L . L F . F R . R B . B
      D . D
      . D .
      D . D
""")),
    ("edges_solved", compile_pattern("""
      . U .
      U U U
      . U .
. L . . F . . R . . B .
L L L F F F R R R B B B
. L . . F . . R . . B .
      . D .
      D D D
      . D .
""")),
    ("any", compile_pattern("""
      . . .
      . U .
      . . .
. . . . . . . . . . . .
. L . . F . . R . . B .
. . . . . . . . . . . .
      . . .
      . D .
      . . .
""")),
]


CFOP_CROSS = generate_variants_from_f(compile_pattern("""
      . . .
      . U .
      . U .
. . . . F . . . . . . .
. L L F F F R R . . B .
. . . . F . . . . . . .
      . D .
      . D .
      . . .
"""))

CFOP_F2L = generate_variants_from_f(compile_pattern("""
      U U U
      U U U
      . . .
L L . . . . . R R B B B
L L . . F . . R R B B B
L L . . . . . R R B B B
      . . .
      D D D
      D D D
"""))

CFOP_OLL = generate_variants_from_f(compile_pattern("""
      U U U
      U U U
      . . .
L L . F F F . R R B B B
L L . F F F . R R B B B
L L . F F F . R R B B B
      . . .
      D D D
      D D D
"""))

CFOP_PLL = [compile_pattern("""
      U U U
      U U U
      U U U
L L L F F F R R R B B B
L L L F F F R R R B B B
L L L F F F R R R B B B
      D D D
      D D D
      D D D
""")]


PETRUS_2X2X2 = generate_corner_variants_from_f(compile_pattern("""
      . . .
      . U .
      . . .
. . . . . . . . . . . .
. L L F F . . R . . B .
. L L F F . . . . . . .
      D D .
      D D .
      . . .
"""))

PETRUS_2X2X3 = generate_corner_variants_from_f(compile_pattern("""
      . . .
      . U .
      . . .
. . . . . . . . . . . .
. L L F F F R R . . B .
. L L F F F R R . . . .
      D D D
      D D D
      . . .
"""))
