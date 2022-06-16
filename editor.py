import curses
import json
import os
import string
import sys
from curses import *

accept_keycodes = [ord(key) for key in list(string.ascii_letters + string.digits + string.punctuation + " ")]

KEY_ESC = 27
KEY_ENTER = 10
KEY_BACKSPACE = 8

# This makes you able to change the keycodes and rebind ESC, ENTER, BACKSPACE
if os.path.exists("keycode_rebinds.json"):
    with open("keycode_rebinds.json", "r") as file:
        keycode_rebinds = json.load(file)

    for key, val in keycode_rebinds.items():
        globals()[key] = val


# floor to positive
def ftp(num):
    if num < 0:
        return 0
    return num


def edit_buffer(buffer, key, cursor, window) -> (list, bool):
    try:
        edited = False
        new_buffer = buffer.copy()
        if cursor.col == 1 and cursor.row == 1 and key == 8:
            return new_buffer, False

        if key == KEY_BACKSPACE and cursor.col == 1:
            line = new_buffer[cursor.row - 1]
            line_move_to = new_buffer[cursor.row - 2]
            new_buffer[cursor.row - 2] = line_move_to + line

            # shift all elements in buffer by one
            for i in range(cursor.row - 1, len(new_buffer) - 1):
                new_buffer[i] = new_buffer[i + 1]

            cursor.up()
            len_of_buffer = len(new_buffer[cursor.row - 1]) + 1
            cursor.col = len_of_buffer if len_of_buffer < window.n_cols - 1 else window.n_cols

            edited = True

            return new_buffer, edited

        if key == KEY_BACKSPACE:
            line = new_buffer[cursor.row - 1]
            new_buffer[cursor.row - 1] = line[:ftp(cursor.col - 2)] + line[cursor.col - 1:]
            cursor.left()
            edited = True

        if key == KEY_ENTER:
            if len(new_buffer) - 1 < cursor.row:
                new_buffer.append("")
            line = new_buffer[cursor.row - 1]
            new_line = new_buffer[cursor.row]
            new_buffer[cursor.row - 1] = line[:cursor.col - 1]
            new_buffer[cursor.row] = line[cursor.col - 1:] + new_line
            cursor.down()
            cursor.col = 1
            edited = True

        elif key in accept_keycodes:
            line = new_buffer[cursor.row - 1]
            new_buffer[cursor.row - 1] = line[:cursor.col - 1] + chr(key) + line[cursor.col - 1:]
            cursor.right()
            edited = True

        return new_buffer, edited
    except IndexError as e:
        print(e)
        return buffer, False


# just a function that makes list from the string of the command
def raw_to_command(raw):
    return "".join(raw).lower().split(" ")


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
                if key == KEY_ESC:
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
                self.stdscr.addstr(rows - 1, len(buffer), "")

    def text_editor(self, file_name):
        self.stdscr.nodelay(True)
        if os.path.exists(file_name):
            with open(file_name, "r") as file:
                buffer = file.readlines()
        else:
            buffer = []

        window = Window(0, 0)
        cursor = Cursor(window)

        is_saved = False

        while True:
            key = self.stdscr.getch()

            if not file_name:
                file_name = "untitled.txt"

            if key == KEY_ESC:
                cmd_buffer = self.open_cmd_overlay()
                if cmd_buffer is not None:
                    cmd = raw_to_command(cmd_buffer)
                    if cmd[0] == ":b":
                        return
                    elif cmd[0] == ":q":
                        sys.exit(0)
                    elif cmd[0] == ":w":
                        with open(file_name, "w") as file:
                            file.write("\n".join(buffer))
                        is_saved = True
                    elif cmd[0] == ":chn":
                        try:
                            file_name = cmd[1]
                        except IndexError:
                            pass
                    elif cmd[0] == ":sav":
                        try:
                            with open(cmd[1], "w") as file:
                                file.write("\n".join(buffer))
                        except IndexError:
                            pass

            rows, cols = self.stdscr.getmaxyx()
            window.n_rows = rows - 1
            window.n_cols = cols - 1

            if len(buffer) < cursor.row:
                for i in range(cursor.row - len(buffer)):
                    buffer.append("")

            cursor.update(key)

            buffer, was_edited = edit_buffer(buffer, key, cursor, window)

            if was_edited:
                is_saved = False

            self.stdscr.clear()

            if is_saved:
                cmd_promp = file_name + " " * (cols - len(file_name) - 1)
            else:
                cmd_promp = (file_name + "*") + " " * (cols - len(file_name) - 2)

            self.stdscr.addstr(0, 0, cmd_promp, curses.A_REVERSE)

            for row, line in enumerate(buffer[:window.n_rows]):
                self.stdscr.addstr(row + 1, 0, line[:window.n_cols])

            self.stdscr.addstr(window.n_rows, window.n_cols - len(f"{cursor.row}:{cursor.col}"),
                               f"{cursor.row}:{cursor.col}")

            self.stdscr.addstr(cursor.row, cursor.col - 1, f"")
            self.stdscr.refresh()

    def main(self, stdscr):
        stdscr.nodelay(True)
        self.stdscr = stdscr
        while True:
            key = self.stdscr.getch()

            cmd_buffer = None

            # just for user to know what to do
            self.stdscr.addstr(0, 0, "Welcome to Jim press ESC to open cmd line")
            self.stdscr.addstr(1, 2, "Commands:")
            self.stdscr.addstr(2, 4, ":e <name> to open file")
            self.stdscr.addstr(3, 4, ":w to save file")
            self.stdscr.addstr(4, 4, ":chn <name> to change file name")
            self.stdscr.addstr(5, 4, ":sav <name> change file as different name")
            self.stdscr.addstr(6, 4, ":b to go back")
            self.stdscr.addstr(7, 4, ":q to quit")

            if key == KEY_ESC:
                cmd_buffer = self.open_cmd_overlay()
                self.stdscr.clear()

            if cmd_buffer is not None:
                cmd = raw_to_command(cmd_buffer)
                if cmd[0] == ":e":
                    # user can input file without name this is exception for it
                    try:
                        self.text_editor(cmd[1])
                        self.stdscr.clear()
                    except IndexError:
                        self.text_editor("")
                        self.stdscr.clear()
                elif cmd[0] == ":q":
                    sys.exit(0)


if __name__ == '__main__':
    editor = Editor()
    wrapper(editor.main)
