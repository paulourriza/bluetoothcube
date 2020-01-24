import re

from bluetoothcube.cubestate import FaceCube

from typing import List

from itertools import permutations

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

def generate_2x2x2_variants_from_f(pattern: FaceCube) -> List[FaceCube]:
    # 8 variants - 1 per corner
    bottom = [pattern, pattern.rotated("y").rotated("y"),
            pattern.rotated("y"), pattern.rotated("y'")]
    top = [p.rotated("x").rotated("x") for p in bottom]
    return bottom + top

def generate_2x2x3_variants_from_f(pattern: FaceCube) -> List[FaceCube]:
    # 12 variants - 4 sideways rotations added to 2x2x2 variants
    bottom = [pattern, pattern.rotated("y").rotated("y"),
            pattern.rotated("y"), pattern.rotated("y'")]
    side = [p.rotated("x") for p in bottom]
    top = [p.rotated("x").rotated("x") for p in bottom]
    return bottom + side + top

def unique_perms(series):
    return {"".join(p) for p in permutations(series)}

def generate_petrus_eo_perms() -> List[FaceCube]:
    # 20 variants before rotation, 240 with 12 2x2x3 rotations
    eo_base_pattern = list("....U................LL..F..RRBBBLL.....RRBBB...DDDDDD")
    edge_face = {}
    # edge faces towards correct center
    edge_face['towards'] = [1,  3,  5,  24, 26, 37]
    # edge faces away from correct center
    edge_face['away']    = [19, 10, 16, 23, 27, 46]

    eo_perms = sorted(unique_perms('UUUFFF'))
    variants = []
    for p in eo_perms: # 1 for each unique EO permutation
        pat = eo_base_pattern.copy()
        for i in range(6): # 1 for each EO edge
            if i < 3: # it's a U edge
                if p[i] == 'U':
                    pat[edge_face['towards'][i]] = 'U'
                else:
                    pat[edge_face['away'][i]] = 'F'
            else: # it's an F edge
                if p[i] == 'F':
                    pat[edge_face['towards'][i]] = 'F'
                else:
                    pat[edge_face['away'][i]] = 'U'
        variants += generate_2x2x3_variants_from_f(compile_pattern(''.join(pat)))
    return variants

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


PETRUS_2X2X2 = generate_2x2x2_variants_from_f(compile_pattern("""
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

PETRUS_2X2X3 = generate_2x2x3_variants_from_f(compile_pattern("""
      . . .
      . U .
      . . .
. . . . . . . . . . . .
L L . . F . . R R B B B
L L . . . . . R R B B B
      . . .
      D D D
      D D D
"""))

PETRUS_EO = generate_petrus_eo_perms()
