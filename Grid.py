from enum import Enum
import random
import copy
from typing import List, Tuple
import math


class State(Enum):
    UNKNOWN = 0
    RED = 1
    BLUE = 2

    def __str__(self):
        if self.value == 0:
            return 'O'
        elif self.value == 1:
            return '\U0001f7e5'
        else:
            return '\U0001f7e6'

    def __repr__(self):
        return self.name

class ContradictionException(Exception):
    pass

class Grid:

    def __init__(self, row_clues: List[List[int]], col_clues: List[List[int]], grid = None):
        self.row_clues = row_clues
        self.col_clues = col_clues
        self.nRows = len(self.row_clues)
        self.nCols = len(self.col_clues)

        self.grid: List[List[State]] = [[State.UNKNOWN for y in range(self.nCols)] for x in range(self.nRows)] \
            if grid is None else grid

    @staticmethod
    def from_puzzle_num(puzzle_num: int):
        row_file = f'rows_{puzzle_num}'
        col_file = f'cols_{puzzle_num}'
        row_clues = Grid.parse_clues(row_file)
        col_clues = Grid.parse_clues(col_file)

        return Grid(row_clues, col_clues)

    def __str__(self):
        return '\n'.join(''.join(str(x) for x in row) for row in self.grid)

    def solve(self):
        dirty = True
        iteration = 0
        while dirty:
            dirty = False
            for row_num in range(self.nRows):
                new_row, new_dirty = self.solveRow(self.getRow(row_num), self.row_clues[row_num], fill_color=State.RED)
                if new_dirty:
                    dirty = True
                    self.setRow(row_num, new_row)

            for col_num in range(self.nCols):
                new_col, new_dirty = self.solveRow(self.getCol(col_num), self.col_clues[col_num], fill_color=State.BLUE)
                if new_dirty:
                    dirty = True
                    self.setCol(col_num, new_col)

            iteration += 1

        unknowns = self.get_unknown_coords()
        if unknowns:
            cached_grid = copy.deepcopy(self.grid)
            spec_row, spec_col = random.choice(unknowns)
            print(f'Speculating ({spec_row, spec_col} is RED')
            try:
                self.grid[spec_row][spec_col] = State.RED
                self.solve()
            except ContradictionException:
                self.grid = cached_grid
                try:
                    print(f'Got contradiction! Try ({spec_row, spec_col} is BLUE')
                    self.grid[spec_row][spec_col] = State.BLUE
                    self.solve()
                except ContradictionException:
                    self.grid = cached_grid
                    print(f'({spec_row}, {spec_col}) is a contradiction. Back up.')
                    raise


    def get_unknown_coords(self) -> List[Tuple[int, int]]:
        result = []
        for row_num, row in enumerate(self.grid):
            result += ((row_num, col_num) for col_num, col in enumerate(row) if col == State.UNKNOWN)
        return sorted(result, key=lambda x: self.dist(x, (self.nRows / 2, self.nCols / 2)), reverse=True)

    def getRow(self, row_num: int):
        return self.grid[row_num].copy()

    def setRow(self, row_num: int, new_row: List[State]):
        self.grid[row_num] = new_row

    def getCol(self, col_num):
        return [row[col_num] for row in self.grid]

    def setCol(self, col_num, new_col: List[State]):
        for i, x in enumerate(new_col):
            self.grid[i][col_num] = x

    def solveRow(self, row: List[State], clues: List[int], fill_color: State) -> Tuple[List[State], bool]:
        if not clues:
            return row, False

        x_color = State.RED if fill_color == State.BLUE else State.BLUE
        dirty = False

        def helper(clue_index):
            nonlocal row
            nonlocal dirty
            left = next(i for i, x in enumerate(row) if x != x_color)
            right = len(row) - next(i for i, x in enumerate(reversed(row)) if x != x_color)

            for clue in clues[:clue_index]:
                while any(x == x_color for x in row[left:left+clue]):
                    left += 1
                left += clue + 1
            for clue in clues[-1:clue_index:-1]:
                while any(x == x_color for x in row[right - clue:right]):
                    right -= 1
                right -= clue + 1


            clue = clues[clue_index]
            while any(x == x_color for x in row[left:left+clue]):
                if clue_index == 0:
                    if row[left] == State.UNKNOWN:
                        dirty = True
                        row[left] = x_color
                    elif row[left] == fill_color:
                        raise ContradictionException
                left += 1
            while any(x == x_color for x in row[right - clue:right]):
                if clue_index == len(clues) - 1 and row[right-1] != x_color:
                    if row[right-1] == State.UNKNOWN:
                        dirty = True
                        row[right - 1] = x_color
                    elif row[right-1] == fill_color:
                        raise ContradictionException
                right -= 1


            width = right - left
            if width < clue:
                raise ContradictionException('Contradiction!')
            if clue == width:
                if row[left:right] != [fill_color] * width:
                    dirty = True
                    row[left:right] = [fill_color] * width
                if left > 1:
                    if row[left-1] != x_color:
                        dirty = True
                        row[left-1] = x_color
                if right < len(row) - 2:
                    if row[right] != x_color:
                        dirty = True
                        row[right] = x_color
            elif clue * 2 > width:
                e = width - clue
                new_fill = [fill_color] * (right - left - 2*e)
                if row[left+e:right-e] != new_fill:
                    dirty = True
                    row[left+e:right-e] = new_fill

        try:
            left = next(i for i, x in enumerate(row) if x != x_color)
        except StopIteration:
            pass
        else:
            if row[left:clues[0]] == [fill_color] * clues[0]:
                internal, internal_dirty = self.solveRow(row[left+clues[0]:], clues[1:], fill_color)
                dirty |= internal_dirty
                return row[:left+clues[0]] + internal, dirty

        try:
            right = len(row) - next(i for i, x in enumerate(reversed(row)) if x != x_color)
        except StopIteration:
            pass
        else:
            if row[right-clues[-1]:right] == [fill_color] * clues[-1]:
                internal, internal_dirty = self.solveRow(row[:right-clues[-1]], clues[:-1], fill_color)
                dirty |= internal_dirty
                return internal + row[right-clues[-1]:], dirty

        for i in range(len(clues)):
            helper(i)

        return row, dirty

    @staticmethod
    def parse_clues(filename):
        clues = []
        with open(filename, 'r') as f:
            for line in f:
                clues.append(list(map(int, line.strip().split())))
        return clues

    @staticmethod
    def dist(x, y):
        return math.sqrt((x[0]-y[0])**2 + (x[1]-y[1])**2)
