import curses
from random import choice, randrange
import numpy as np

chs = [ord(ch) for ch in 'adwsreADWSRE']
actions = ['left','right','up','down','restart','exit']
directions = actions[:4]
ch2action = dict(zip(chs, actions * 2))

def get_user_action(stdscr):
    ch = 'N'
    while(ch not in chs):
        ch = stdscr.getch()
    return ch2action[ch]

def invert(field):
    return np.array([row[::-1] for row in field])

class GameField():
    def __init__(self, stdscr, win_num = 2048, width = 4):
        self.win_num = win_num
        self.width = width
        self.field = []
        self.stdscr = stdscr
        self.score = 0
        self.high_score = 0
        self.end_game = 0 # 0: in game, 1: win, 2: lose

    def spawn(self):
        new_element = 4 if randrange(100) > 89 else 2
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.width) if (self.field[i][j] == 0)])
        self.field[i][j] = new_element

    def reset(self):
        self.high_score = max(self.high_score, self.score)
        self.field = np.zeros((self.width, self.width), dtype=int)
        self.score = 0
        self.end_game = 0
        self.spawn()

    def is_win(self):
        return any(any(item >= self.win_num for item in row) for row in self.field)

    def draw(self, stdscr):
        win_lose_str = ['Congratulations! You win!', 'Pity! You lose!']
        help_str1 = '(W) Up  (S) Down  (A) Left  (D) Right'
        help_str2 = '        (E) Exit  (R) Restart'
        separator = '*' + '------*' * self.width

        def cast(astr):
            stdscr.addstr(astr + '\n')

        def draw_game_field():
            cast(separator)
            for row in self.field:
                cast(''.join('|{:^5} '.format(num) if num > 0 else '|      ' for num in row) + '|')
                cast(separator)

        stdscr.clear()
        if (self.end_game != 0):
            cast(win_lose_str[self.end_game-1])
            cast(help_str2)
            return

        cast('score: ' + str(self.score))
        cast('high score: ' + str(self.high_score))
        draw_game_field()
        cast(help_str1)
        cast(help_str2)

    def can_move(self, direction = 'none'):
        def can_move_left(row):
            return any((row[i-1] == 0 or row[i-1] == row[i]) and row[i] != 0  for i in range(1, self.width))

        check = {}
        check['left'] = lambda field: any(can_move_left(row) for row in field)
        check['right'] = lambda field: check['left'](invert(field))
        check['up'] = lambda field: check['left'](field.T)
        check['down'] = lambda field: check['right'](field.T)

        if direction != 'none':
            return check[direction](self.field)
        else:
            return any(check[dir](self.field) for dir in directions)

    def move(self, direction):
        def move_left(row):  # return a new row
            row0 = [i for i in row if i != 0]
            row1 = []
            to_merge = 0
            for i in row0:
                if(to_merge == i):
                    row1.append(to_merge * 2)
                    self.score += to_merge * 2
                    to_merge = 0
                else:
                    row1.append(to_merge)
                    to_merge = i
            row1.append(to_merge)
            row1 = [i for i in row1 if i != 0]
            return row1 + [0] * (len(row) - len(row1))

        moves = {}
        moves['left'] = lambda field: np.array([move_left(row) for row in field])
        moves['right'] = lambda field: invert(moves['left'](invert(field)))
        moves['up'] = lambda field: (moves['left'](field.T)).T
        moves['down'] = lambda field: (moves['right'](field.T)).T

        if(self.can_move(direction)):
            self.field = moves[direction](self.field)
            self.spawn()
            return True
        return False

def main(stdscr):
    def init():
        game_field.reset()
        return 'game'

    def game():
        game_field.draw(stdscr)
        action = get_user_action(stdscr)
        if(action == 'exit'):
            return 'exit'
        if(action == 'restart'):
            return 'init'
        if(game_field.move(action)):
            if(game_field.is_win()):
                return 'win'
            if(not game_field.can_move()):
                return 'lose'
        return 'game'

    def not_game(outcome):
        game_field.end_game = 1 if outcome == 'win' else 2
        game_field.draw(stdscr)
        action = get_user_action(stdscr)
        act2state = {'exit': 'exit', 'restart': 'init'}
        return act2state.get(action, state)

    state2func = dict({
        'game': game,
        'win' : lambda: not_game('win'),
        'lose': lambda: not_game('lose'),
        'init': init
    })

    game_field = GameField(stdscr)
    state = 'init'
    while(state != 'exit'):
        state = state2func[state]()
    stdscr.clear()

curses.wrapper(main)