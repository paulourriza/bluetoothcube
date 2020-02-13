import kivy
import random

from kivy.clock import Clock
from kociemba.pykociemba.color import color_keys
#from kociemba.pykociemba.tools import randomCube
from kociemba.pykociemba.cubiecube import CubieCube
from kociemba.pykociemba.coordcube import CoordCube
from kociemba import solve
from threading import Thread, Event

from bluetoothcube.cubestate import CubieCube, MOVES_GIIKER_TO_KOCIEMBA

from typing import List


class Move:
    def __init__(self, face: str, dir: str, count: int = 1) -> None:
        self.face = face
        self.dir = dir
        self.count = count

    def __repr__(self):
        # Internal, actual representation of the move.
        return (f"{self.face}{self.dir}"
                f"{self.count if self.count > 1 else ''}")

    def nice_str(self):
        # Nice representation, preferred by humans (no R'3 etc.)
        if not self.is_printable():
            return ""
        count = self.count % 4
        dir = self.dir
        if count == 2:
            dir = ''
        elif count == 3:
            # Inverse direction
            dir = "" if dir else "'"
            count = 1
        return (f"{self.face}{dir}{count if count > 1 else ''}")

    def is_printable(self):
        return self.count % 4 != 0

    @staticmethod
    def list_to_str(list: List['Move']):
        return ' '.join(str(m) for m in list if m.is_printable())


def merge_moves(a: Move, b: Move) -> List[Move]:
    if a.face != b.face:
        return [a, b]

    if a.dir != b.dir:
        return [a, b]

    new_count = a.count + b.count

    return [Move(a.face, a.dir, new_count)]


class BluetoothCube(kivy.event.EventDispatcher):
    solved = kivy.properties.BooleanProperty(False)

    def __init__(self):
        self.register_event_type('on_state_changed')
        self.register_event_type('on_move_raw')
        self.register_event_type('on_move_merged')
        super(BluetoothCube, self).__init__()
        self.cube_state = CubieCube()
        self.move_history_raw: List[Move] = []
        self.move_history_merged: List[Move] = []
        self.connection = None

    def set_connection(self, connection):
        self.connection = connection
        self.cube_state = CubieCube()
        self.connection.bind(on_state_updated=self.process_state_update)

    def disable_connection(self):
        self.cube_state = CubieCube()
        self.connection = None
        self.solved = self.cube_state.is_solved()
        self.dispatch('on_state_changed', self.cube_state)

    def process_state_update(self, connection, state):
        self.cube_state = CubieCube(giiker_state=state)
        self.solved = self.cube_state.is_solved()

        face = color_keys[MOVES_GIIKER_TO_KOCIEMBA[(state[16] >> 4) & 0x0F]]
        dir = ("" if (state[16] & 0x0F) == 1 else "'")
        move = Move(face, dir)
        self.move_history_raw.append(move)

        # s = '  '.join(self.cube_state.get_representation_strings())
        # print(f"{s}  {move}")

        self.dispatch('on_state_changed', self.cube_state)
        self.dispatch('on_move_raw', move)

        self.add_move_to_rich_history(move)

    def add_move_to_rich_history(self, move: Move):
        if len(self.move_history_merged) < 1:
            self.move_history_merged.append(move)
            return

        # Merge last two moves, if applicable
        last_move = self.move_history_merged[-1]
        self.move_history_merged.pop()
        new_moves = merge_moves(last_move, move)
        self.move_history_merged += new_moves

        # Trim the moves list to last 50 moves.
        self.move_history_merged = self.move_history_merged[-50:]

        # print(Move.list_to_str(self.move_history_merged))

        self.dispatch('on_move_merged', new_moves[-1])

    def on_state_changed(self, *args):
        pass

    def on_move_raw(self, *args):
        pass

    def on_move_merged(self, *args):
        pass


# Listens for cube moves, tries to detect when the user has finished manually
# scrambling the cube, and emits a signal when that happens.
class ScrambleDetector(kivy.event.EventDispatcher):
    # TODO: These constants should be customizable
    MIN_LENGTH = 15
    MIN_SOLUTION = 5
    DELAY = 3.0

    def __init__(self, cube: BluetoothCube) -> None:
        self.register_event_type('on_manual_scramble_finished')
        self.register_event_type('on_target_scramble_matched')
        super().__init__()

        self.cube = cube
        self.cube.bind(
            solved=self.on_solved,
            on_move_raw=self.on_move_raw)

        self.is_solved = False
        self.mid_scramble = False
        self.scramble_length = 0

        self.scramble_delay_schedule = None

    def on_solved(self, cube: BluetoothCube, solved: bool) -> None:
        if solved:
            self.is_solved = True
            self.mid_scramble = False
            self.scramble_length = 0

    def on_move_raw(self, cube: BluetoothCube, move: Move) -> None:
        if self.is_solved and not cube.solved:
            # First move.
            self.is_solved = False
            self.mid_scramble = True
        if self.mid_scramble:
            self.scramble_length += 1
            if self.scramble_delay_schedule:
                Clock.unschedule(self.scramble_delay_schedule)
            self.scramble_delay_schedule = Clock.schedule_once(
                lambda td: self.on_scramble_stopped(), self.DELAY)

    def on_scramble_stopped(self):
        # User did not make a move for DELAY seconds.
        self.mid_scramble = False
        if self.scramble_length > self.MIN_LENGTH:
            cube_str = self.cube.cube_state.toFaceCube().to_String()
            if cube_str == self.target_scramble.to_String():
                self.dispatch('on_target_scramble_matched')
            solution_length = len(solve(cube_str).split())
            if solution_length <= self.MIN_SOLUTION:
                print("NOT SCRAMBLED ENOUGH: kociemba solution is", solution_length, "steps")
            else:
                print("SCRAMBLED!!! kociemba solution is", solution_length, " steps")
                self.dispatch('on_manual_scramble_finished')

    def on_manual_scramble_finished(self, *args):
        pass

    def on_target_scramble_matched(self, *args):
        pass

    def set_scramble(self, fc):
        self.target_scramble = fc

def randomCube():
    """
    Generates a random cube.
    @return A random cube in the string representation. Each cube of the cube space has the same probability.
    """
    cc = CubieCube()
    cc.setFlip(random.randint(0, CoordCube.N_FLIP - 1))
    cc.setTwist(random.randint(0, CoordCube.N_TWIST - 1))
    while True:
        cc.setURFtoDLB(random.randint(0, CoordCube.N_URFtoDLB - 1))
        cc.setURtoBR(random.randint(0, CoordCube.N_URtoBR - 1))

        if (cc.edgeParity() ^ cc.cornerParity()) == 0:
            break
    fc = cc.toFaceCube()
    return fc

# Populates a buffer of scrambles that can be consumed by calling get_scramble().
# TODO: can instead be written as EventDispatcher instead of Thread
class ScrambleGenerator(Thread):
    def __init__(self):
        super().__init__()
        self.max_scrambles = 5
        self.scrambles = []
        self.scramble_state = []
        self.exit_now = Event()
        self.buffer_not_empty = Event()
        self.buffer_not_full = Event()
        self.buffer_not_full.set()

    def run(self):
        while not self.exit_now.is_set():
            if len(self.scrambles) < self.max_scrambles:
                s = self.generate_scramble()
                self.scrambles.append(s)
                self.buffer_not_empty.set()
            else:
                self.buffer_not_full.clear()
                self.buffer_not_full.wait()

    def get_scramble(self):
        if len(self.scrambles) == 0:
            self.buffer_not_empty.clear()
            self.buffer_not_empty.wait()
        s = self.scrambles.pop()
        self.buffer_not_full.set()
        return s

    def generate_scramble(self):
        fc = randomCube()
        s = solve(fc.to_String())
        s = s.split()[::-1]   # split and reverse
        # invert solution
        for i in range(len(s)):
            if len(s[i]) == 1:
                s[i] += "'"
            elif s[i][1] == "'":
                s[i] = s[i][0]
        return (" ".join(s), fc)

    def exit(self):
        self.exit_now.set()
        self.get_scramble()
