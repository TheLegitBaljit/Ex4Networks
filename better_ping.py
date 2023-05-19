from watchdog import *
import threading
import os
import socket
import struct
import time



# This is the ICMP
ICMP_ECHO_REQUEST = 8


def checksum(source_string):
    sum = 0
    countTo = (len(source_string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = source_string[count + 1] * 256 + source_string[count]
        sum = sum + thisVal
        sum = sum & 0xffffffff
        count = count + 2

    if countTo < len(source_string):
        sum = sum + source_string[len(source_string) - 1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    answer = ~sum
    answer = answer & 0xffff

    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer


def receive_ping(my_socket, ID, timeout):
    time_remaining = timeout
    while True:
        started_select = time.time()
        what_ready = select([my_socket], [], [], time_remaining)
        if what_ready[0] == []:
            return

        time_received = time.time()
        received_packet = my_socket.recv(100)
        icmp_header = received_packet[20:28]
        type, code, checksum, packet_ID, sequence = struct.unpack(
            "bbHHh", icmp_header
        )
        if packet_ID == ID:
            bytes_In_double = struct.calcsize("d")
            time_sent = struct.unpack("d", received_packet[28:28 + bytes_In_double])[0]
            return time_received - time_sent

        time_remaining -= time_received - started_select
        if time_remaining <= 0:
            return


def send_ping(my_socket, dest_addr, ID):
    dest_addr = socket.gethostbyname(dest_addr)  # Converts the destination address to IPv4 address.

    my_checksum = 0
    # Code for icmp request
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    bytes_In_double = struct.calcsize("d")
    data = bytes_In_double * "Q"
    data = struct.pack("d", time.time()) + data.encode()

    my_checksum = checksum(header + data)

    header = struct.pack(
        "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
    )
    packet = header + data
    my_socket.sendto(packet, (dest_addr, 1))


def ping(dest_addr, timeout=2):
    icmp_proto = socket.getprotobyname("icmp")
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp_proto)  # Creating socket with icmp
    my_ID = os.getpid() & 0xFFFF  # Gets the process id and converts it to 16 bits.
    send_ping(my_socket, dest_addr, my_ID)
    delay = receive_ping(my_socket, my_ID, timeout)

    my_socket.close()

    return delay


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} <ip>")
        sys.exit(1)

    ip_address = sys.argv[1]

    print(f"Pinging {ip_address} with Python:")

    watchdog_thread = threading.Thread(target=watchdog, args=(ip_address,))
    watchdog_thread.start()

    for i in range(4):
        try:
            delay = ping(ip_address)

            if delay is None:
                print("Request timed out.")

            else:
                delay = delay * 1000

                print(f"Reply from {ip_address}: bytes=32 time={delay:.3f}ms")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(1)

    # Wait for the watchdog thread to finish
    watchdog_thread.join()
