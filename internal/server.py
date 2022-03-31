from internal.delivery import request_proc
from pathlib import Path
import configparser
import os
import socket
import select
import contextlib


def server():
    config = configparser.ConfigParser()
    if Path("/etc/httpd.conf").is_file():
        config.read_file(open(r'/etc/httpd.conf'))
    else:
        config.read_file(open(r'httpd.conf'))

    try:
        PORT = int(config.get('config', 'listen'))
        CPU_LIMIT = int(config.get('config', 'cpu_limit'))
        DOCUMENT_ROOT = config.get('config', 'document_root')
    except contextlib.suppress(Exception):
        PORT = 80
        DOCUMENT_ROOT = '/var/www/html'
        CPU_LIMIT = 4

    print("Starting server on port {}, document root: {}, cpu limit: {}".format(PORT, DOCUMENT_ROOT, CPU_LIMIT))
    serverSoc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSoc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serverSoc.bind(('0.0.0.0', PORT))
    serverSoc.listen(1)
    serverSoc.setblocking(False)

    # CPU_LIMIT
    for _ in range(1, CPU_LIMIT):
        pid = os.fork()
        if pid == 0:
            break

    epoll = select.epoll()
    epoll.register(serverSoc.fileno(), select.EPOLLIN | select.EPOLLET)

    try:
        while True:
            connections = {}
            requests = {}
            responses = {}
            connList = epoll.poll()
            for fileno, event in connList:
                if fileno == serverSoc.fileno():
                    try:
                        while True:
                            connection, _ = serverSoc.accept()
                            connection.setblocking(False)
                            epoll.register(connection.fileno(), select.EPOLLIN | select.EPOLLET)
                            connections[connection.fileno()] = connection
                            requests[connection.fileno()] = b''
                    except socket.error:
                        pass
                elif event & select.EPOLLIN:
                    try:
                        while True:
                            buffer = connections[fileno].recv(1024)
                            if not buffer:
                                break
                            requests[fileno] += buffer
                    except socket.error:
                        pass

                    if b'\n\n' in requests[fileno] or b'\n\r\n' in requests[fileno]:
                        epoll.modify(fileno, select.EPOLLOUT | select.EPOLLET)

                    resp, file = request_proc(requests[fileno].decode(), DOCUMENT_ROOT)  # 'UTF-8'
                    file_content = b""
                    if file:
                        buff = b""
                        while True:
                            file_content += buff
                            buff = os.read(file, 1024)
                            if not buff:
                                break
                        os.close(file)
                    responses[fileno] = resp + file_content
                elif event & select.EPOLLOUT:
                    try:
                        while len(responses[fileno]) > 0:
                            countBytes = connections[fileno].send(responses[fileno])
                            responses[fileno] = responses[fileno][countBytes:]
                    except socket.error:
                        pass

                    if len(responses[fileno]) == 0:
                        epoll.modify(fileno, select.EPOLLET)
                        connections[fileno].shutdown(socket.SHUT_RDWR)
                elif event & select.EPOLLHUP:
                    epoll.unregister(fileno)
                    connections[fileno].close()
                    del connections[fileno]
    except KeyboardInterrupt:
        print('Error is KeyboardInterrupt')
    finally:
        epoll.unregister(serverSoc.fileno())
        epoll.close()
        serverSoc.close()
