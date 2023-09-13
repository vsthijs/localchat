import socket
import curses
import time
from curses import wrapper

frametime = 0.5
running: bool = True
txtbuf: str = str()
winpos: tuple[int, int] = (0, 0)
PORT: int = 2194
SOCK: socket.socket = None
USERNAME: str = "anonymous"
SENTPING: list[str] = None


def initsock():
    global SOCK
    SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    SOCK.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    SOCK.bind(("0.0.0.0", PORT))
    SOCK.settimeout(0.05)


def sendmsg(txt: str):
    b = txt.encode("utf-8")
    SOCK.sendto(b, ("255.255.255.255", PORT))


def recvmsg():
    try:
        packet = SOCK.recvfrom(1024)[0].decode("utf-8")
        if packet == "1list":
            if USERNAME != "anonymous":
                sendmsg(f"1{USERNAME}")
        elif packet[0] == "1":
            if SENTPING and packet[1:] not in SENTPING:
                printbuf(f"online peer: {packet[1:]}")
        elif packet[0] == "0":
            printbuf(packet[1:])
    except TimeoutError:
        pass


def printbuf(txt: str):
    global txtbuf

    if len(txt) >= 2 and txt[0] == "\\" and txt[1] == ":":
        txt = ":" + txt[2:]

    txtbuf += txt+"\n"


def evalcommand(txt: str):
    global running, USERNAME, SENTPING
    if txt[0] == ":":
        command = txt[1:].split(" ")
        match command:
            case ["q" | "quit"]:
                running = False
            case ["setusr", n]:
                USERNAME = n
            case ["list"]:
                SENTPING = []
                sendmsg("1list")
            case _:
                printbuf(f"# err: unknown command '{txt}'")
    else:
        sendmsg(f"0{USERNAME}> {txt}")


def getkey(stdscr):
    try:
        k = stdscr.getch()
        try:
            if chr(k) in "abcdefghaijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_-+=|\\/?<>,.1234567890!@#$%^&*();:'\"[]{} \n":
                return chr(k)
            else:
                return k
        except ValueError:
            return k
    except curses.error:
        return None


def main(stdscr):
    global winpos, running, txtbuf
    initsock()

    stdscr.nodelay(True)
    winpos = stdscr.getmaxyx()
    txtbuf = str()
    inpbuf = str()

    while (running):
        stdscr.clear()
        winpos = stdscr.getmaxyx()
        stdscr.addstr(1, 0, txtbuf)
        stdscr.addstr(0, 0, f"[ username: {USERNAME} ]")
        stdscr.addstr(winpos[0]-1, 0, inpbuf)
        stdscr.refresh()

        recvmsg()

        # input handling
        inp = getkey(stdscr)

        if inp == 8:  # backspace
            if len(inpbuf) > 0:
                inpbuf = inpbuf[:-1]
        elif inp in [13, "\n"]:
            evalcommand(inpbuf)
            inpbuf = ""
        elif inp == str(inp):
            inpbuf += inp


try:
    if __name__ == "__main__":
        wrapper(main)
finally:
    SOCK.close()
