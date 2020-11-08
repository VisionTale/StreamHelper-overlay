from socket import socket

s: socket = None

# TODO Consider changing to amcp_pylib. Is [HTML] tag supported or is PR needed?


def init(ip: str = '127.0.0.1', port: int = 5250):
    global s
    s = socket()
    s.connect((ip, port))


def send_command(command) -> str:
    global s
    command += '\r\n'
    command = command.encode()
    s.send(command)
    buffer = s.recv(1024)
    message = buffer.decode('utf-8')
    while len(buffer) == 1024:
        buffer = s.recv(1024)
        message += buffer.decode('utf-8')
    return message


def close():
    global s
    s.close()
