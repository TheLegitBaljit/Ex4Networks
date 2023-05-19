from better_ping import *



def watchdog(dest_addr):
    timeout = 10
    while True:
        try:
            delay = ping(dest_addr, timeout)
            if delay is None:
                print(f"Server {dest_addr} cannot be reached.")
            else:
                delay = delay * 1000
                print(f"Reply from {dest_addr}: bytes=32 time={delay:.3f}ms")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)
