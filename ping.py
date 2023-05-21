import os
import sys
import socket
import struct
import select
import time

ICMP_ECHO_REQUEST = 8


def checksum(source_string):
    sum = 0
    countTo = (len(source_string) // 2) * 2
    count = 0
    while count < countTo:
        thisVal = source_string[count + 1] * 256 + source_string[count]
        sum += thisVal
        sum &= 0xffffffff
        count += 2

    if countTo < len(source_string):
        sum += source_string[len(source_string) - 1]
        sum &= 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum += (sum >> 16)

    answer = ~sum
    answer &= 0xffff

    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receive_one_ping(my_socket, ID, timeout):
    timeLeft = timeout

    while True:
        start_select = time.time()
        ready = select.select([my_socket], [], [], timeLeft)
        select_time = (time.time() - start_select)

        if ready[0] == []:
            return

        timeReceived = time.time()
        recPacket, addr = my_socket.recvfrom(1024)
        icmpHeader = recPacket[20:28]
        type_, code_, checksum_, packetID_, sequence_ = struct.unpack("bbHHh", icmpHeader)

        if packetID_ == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            ttl = ord(struct.unpack("c", recPacket[8:9])[0])
            return timeReceived - timeSent, ttl

        timeLeft -= select_time

        if timeLeft <= 0:
            return


def send_one_ping(my_socket, dest_addr, ID):
    dest_addr = socket.gethostbyname(dest_addr)

    my_checksum = 0

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
    data = struct.pack("d", time.time())
    my_checksum = checksum(header + data)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1)
    packet = header + data

    my_socket.sendto(packet, (dest_addr, 1))


def ping(dest_addr, timeout):
    icmp = socket.getprotobyname("icmp")

    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
    except socket.error as e:
        if e.errno == 1:
            msg = "Operation not permitted"
            raise socket.error(msg)

    my_ID = os.getpid() & 0xFFFF

    send_one_ping(my_socket, dest_addr, my_ID)
    result = receive_one_ping(my_socket, my_ID, timeout)

    my_socket.close()

    if result == None:
        return None, None

    delay, ttl = result

    return delay, ttl


if __name__ == '__main__':
    dest_addr = sys.argv[1]
    timeout = 1
    seq = 1

    while True:
        try:
            result = ping(dest_addr, timeout)
            if result == None:
                print(f"Request timed out")
            else:
                delay, ttl = result
                delay *= 1000
                print(f"Reply from {dest_addr}: bytes=32 seq={seq} TTL={ttl} time={delay:.3f}ms")

            seq += 1
            time.sleep(1)
        except KeyboardInterrupt:
            print("Interrupted")
            exit(1)
