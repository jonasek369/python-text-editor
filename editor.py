import curses
import string
import sys
from curses import *

accept_keycodes = [ord(key) for key in list(string.ascii_letters + string.digits + string.punctuation + " ")]


# floor to positive
def ftp(num):
    if num < 0:
        return 0
    return num


def rotate(input, n):
    return input[n:] + input[:n]


def edit_buffer(buffer, key, cursor, window) -> list:
    try:
        new_buffer = buffer.copy()

        # TODO: Makes this to delete and move text to back line

        if cursor.col == 1 and cursor.row == 1 and key == 8:
            return new_buffer

        if key == 8 and cursor.col == 1:
            line = new_buffer[cursor.row - 1]
            line_move_to = new_buffer[cursor.row - 2]
            new_buffer[cursor.row - 2] = line_move_to + line

            # shift all elements in buffer by one
            for i in range(cursor.row - 1, len(new_buffer)-1):
                new_buffer[i] = new_buffer[i+1]

            cursor.up()
            len_of_buffer = len(new_buffer[cursor.row - 1])-1
            cursor.col = len_of_buffer if len_of_buffer < window.n_cols-1 else window.n_cols

            return new_buffer

        if key == 8:
            line = new_buffer[cursor.row - 1]
            new_buffer[cursor.row - 1] = line[:ftp(cursor.col - 2)] + line[cursor.col - 1:]
            cursor.left()

        if key == 10:
            line = new_buffer[cursor.row - 1]
            new_line = new_buffer[cursor.row]
            new_buffer[cursor.row - 1] = line[:cursor.col - 1]
            new_buffer[cursor.row] = line[cursor.col - 1:] + new_line
            cursor.down()
            cursor.col = 1

        elif key in accept_keycodes:
            line = new_buffer[cursor.row - 1]
            new_buffer[cursor.row - 1] = line[:cursor.col - 1] + chr(key) + line[cursor.col - 1:]
            cursor.right()

        return new_buffer
    except IndexError as e:
        print(e)
        return buffer


class Window:
    def __init__(self, n_rows, n_cols):
        self.n_rows = n_rows
        self.n_cols = n_cols


class Cursor:
    def __init__(self, window, row=1, col=1):
        self.row = row
        self.col = col
        self.window = window

    def up(self):
        if self.row > 1:
            self.row -= 1

    def down(self):
        if self.row < self.window.n_rows:
            self.row += 1

    def left(self):
        if self.col > 1:
            self.col -= 1

    def right(self):
        if self.col < self.window.n_cols:
            self.col += 1

    def update(self, key):
        if key == KEY_UP:
            self.up()
        elif key == KEY_DOWN:
            self.down()
        elif key == KEY_LEFT:
            self.left()
        elif key == KEY_RIGHT:
            self.right()


class Editor:
    def __init__(self):
        self.stdscr = None

    def open_cmd_overlay(self):
        buffer = []
        while True:
            try:
                key = self.stdscr.getch()
                if key == 27:
                    return
                if key == 8:
                    buffer = buffer[:len(buffer) - 1]
                key = chr(key)
                if key == "\n":
                    return buffer
                if key in list(string.ascii_letters + string.digits + string.punctuation + " "):
                    buffer.append(key)
            except:
                rows, cols = self.stdscr.getmaxyx()
                cmd_promp = "".join(buffer) + " " * (cols - len(buffer) - 1)
                self.stdscr.addstr(rows - 1, 0, cmd_promp, curses.A_REVERSE)

    def text_editor(self, file_name):
        self.stdscr.nodelay(True)

        with open(file_name, "r") as file:
            buffer = file.readlines()

        window = Window(0, 0)
        cursor = Cursor(window)
        while True:
            try:
                key = self.stdscr.getch()
            except:
                key = 0
            if key == 27:
                cmd_buffer = self.open_cmd_overlay()
                if cmd_buffer is not None:
                    if "".join(cmd_buffer)[:2] == ":b":
                        return
                    if "".join(cmd_buffer)[:2] == ":q":
                        sys.exit(0)
                    if "".join(cmd_buffer)[:2] == ":w":
                        with open(file_name, "w") as file:
                            file.write("\n".join(buffer))

            rows, cols = self.stdscr.getmaxyx()
            window.n_rows = rows - 1
            window.n_cols = cols - 1

            if len(buffer) < window.n_rows:
                for i in range(window.n_rows - len(buffer)):
                    buffer.append("")

            cursor.update(key)

            buffer = edit_buffer(buffer, key, cursor, window)

            self.stdscr.clear()
            cmd_promp = file_name + " " * (cols - len(file_name) - 1)
            self.stdscr.addstr(0, 0, cmd_promp, curses.A_REVERSE)

            for row, line in enumerate(buffer[:window.n_rows]):
                self.stdscr.addstr(row + 1, 0, line[:window.n_cols])

            self.stdscr.addstr(window.n_rows, window.n_cols-len(f"{cursor.row}:{cursor.col}"), f"{cursor.row}:{cursor.col}")

            self.stdscr.addstr(cursor.row, cursor.col - 1, f"")
            self.stdscr.refresh()

    def main(self, stdscr):
        stdscr.nodelay(True)
        self.stdscr = stdscr
        while True:
            key = self.stdscr.getch()
            cmd_buffer = None

            if key == 27:
                cmd_buffer = self.open_cmd_overlay()
                self.stdscr.clear()

            if cmd_buffer is not None:
                if "".join(cmd_buffer)[:2] == ":e":
                    self.text_editor("".join(cmd_buffer)[3:])
                    self.stdscr.clear()
                if "".join(cmd_buffer)[:2] == ":q":
                    sys.exit(0)


if __name__ == '__main__':
    editor = Editor()
    wrapper(editor.main)