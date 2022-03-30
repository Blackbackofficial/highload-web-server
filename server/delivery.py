import datetime
import fcntl
import os
import re
import urllib.parse


class HTTP_request:
    def __init__(self):
        self.method = None
        self.protocol = None
        self.url = None
        self.headers = None
        self.query = None


MIME_TYPES = {
    'html': 'text/html', 'css': 'text/css', 'js': 'text/javascript', 'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'swf': 'application/x-shockwave-flash',
    'txt': 'text/txt', 'default': 'text/plain'
}

RESPONSE_CODES = {
    'OK': '200 OK', 'NOT_FOUND': '404 Not Found',
    'NOT_ALLOWED': '405 Method Not Allowed', 'FORBIDDEN': '403 Forbidden'
}

RESPONSE_OK = 'HTTP/{} {}\r\n' 'Content-Type: {}\r\n' 'Content-Length: {}\r\n' 'Date: {}\r\n' \
              'Server: PythonServer\r\n\r\n'

RESPONSE_FAIL = 'HTTP/{} {}\r\n' 'Server: PythonServer'

DATETIME_TEMPLATE = '%a, %d %b %Y %H:%M:%S GMT'

ALLOW_METHODS = ['HEAD', 'GET']


def build_response(resp_code='', protocol='', content_type='', content_length=''):
    if resp_code == RESPONSE_CODES["OK"]:
        date = datetime.datetime.utcnow().strftime(DATETIME_TEMPLATE)
        return RESPONSE_OK.format(protocol, resp_code, content_type, content_length, date).encode()
    else:
        return RESPONSE_FAIL.format(protocol, resp_code).encode()


def parse_request(request_string):
    request = HTTP_request()
    try:
        request.method = re.findall(r'^(\w+)', request_string)[0]
    except IndexError:
        request.method = None

    try:
        request.protocol = re.findall(r'HTTP/([0-9.]+)', request_string)[0]
    except IndexError:
        request.protocol = None

    try:
        request.url = re.findall(r'([^\s?]+)', request_string)[1]
        request.url = urllib.parse.unquote(request.url)
    except IndexError:
        request.url = None

    return request


def request_processing(request_string, document_root=''):
    request = parse_request(request_string)
    protocol = request.protocol

    if request.method not in ALLOW_METHODS:
        return build_response(RESPONSE_CODES["NOT_ALLOWED"], protocol), None

    # Up the folders
    if len(re.findall(r'\.\./', request.url)) > 1:
        return build_response(RESPONSE_CODES["FORBIDDEN"], protocol), None

    request.url += 'index.html' if request.url[-1] == '/' else ''
    file_path = request.url[1:]

    try:
        file = os.open(os.path.join(document_root, file_path), os.O_RDONLY)
        flag = fcntl.fcntl(file, fcntl.F_GETFL)
        fcntl.fcntl(file, fcntl.F_SETFL, flag | os.O_NONBLOCK)
    except (FileNotFoundError, IsADirectoryError):
        if 'index.html' in request.url:
            return build_response(RESPONSE_CODES["FORBIDDEN"], protocol), None
        else:
            return build_response(RESPONSE_CODES["NOT_FOUND"], protocol), None
    except OSError:
        return build_response(RESPONSE_CODES["NOT_FOUND"], protocol), None

    try:
        content_type = MIME_TYPES[re.findall(r'\.(\w+)$', file_path)[0]]
    except KeyError:
        content_type = MIME_TYPES["default"]

    content_length = os.path.getsize(os.path.join(document_root, file_path))

    if request.method == 'HEAD':
        file = None

    return build_response(RESPONSE_CODES["OK"], protocol, content_type, str(content_length)), file
