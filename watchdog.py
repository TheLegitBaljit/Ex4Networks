import threading
import socket
import sys
import time


def watchdog():
    watchdog_timer = 10  # 10 seconds watchdog timer

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('localhost', 3000))
    s.listen(5)

    while True:
        clientsocket, address = s.accept()
        try:
            data = clientsocket.recv(1024).decode('utf-8')
            if data == 'reset':
                watchdog_timer = 10  # reset watchdog timer when receiving reset signal from ping.py
            else:
                break  # exit when receiving exit signal from ping.py
        except Exception as e:
            print(f"Error occurred: {str(e)}")

        time.sleep(1)  # wait for 1 second before next iteration
        watchdog_timer -= 1  # decrement watchdog timer every second

        if watchdog_timer == 0:  # if watchdog timer reaches zero then exit and print server cannot be reached.
            print("server cannot be reached.")
            sys.exit(0)


if __name__ == '__main__':
    watchdog()
