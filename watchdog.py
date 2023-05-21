import threading
import socket
import sys


def watchdog(ip):
    watchdog_timer = 10  # 10 seconds watchdog timer

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', 3000))
    s.listen(5)

    while True:
        clientsocket, address = s.accept()
        data = clientsocket.recv(1024).decode('utf-8')
        if data == 'reset':
            watchdog_timer = 10  # reset watchdog timer when receiving reset signal from ping.py
        else:
            break  # exit when receiving exit signal from ping.py

    watchdog_timer -= 1  # decrement watchdog timer every second

    if watchdog_timer == 0:  # if watchdog timer reaches zero then exit and print server cannot be reached.
        print(f"server {ip} cannot be reached.")
        sys.exit(0)


if __name__ == '__main__':
    ip = sys.argv[1]
    watchdog(ip)
