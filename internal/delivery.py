import datetime
import fcntl
import os
import re
import urllib.parse


RESPONSE_CODES = {
    'OK': '200 OK', 'NOT_FOUND': '404 Not Found',
    'NOT_ALLOWED': '405 Method Not Allowed', 'FORBIDDEN': '403 Forbidden'
}

MIME_TYPES = {
    'html': 'text/html', 'css': 'text/css', 'js': 'text/javascript', 'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'swf': 'application/x-shockwave-flash',
    'txt': 'text/txt', 'default': 'text/plain'
}

RESPONSE_OK = 'HTTP/{} {}\r\n' 'Content-Type: {}\r\n' 'Content-Length: {}\r\n' 'Date: {}\r\n' \
              'Server: PythonServer\r\n\r\n'

RESPONSE_FAIL = 'HTTP/{} {}\r\n' 'Server: PythonServer'

DATETIME_TEMPLATE = '%a, %d %b %Y %H:%M:%S GMT'

ALLOW_METHODS = ['HEAD', 'GET']


class HTTP_request:
    def __init__(self):
        self.Method = None
        self.Protocol = None
        self.Url = None
        self.Headers = None


def response(resp_code='', protocol='', content_type='', content_length=''):
    if resp_code == RESPONSE_CODES["OK"]:
        date = datetime.datetime.utcnow().strftime(DATETIME_TEMPLATE)
        return RESPONSE_OK.format(protocol, resp_code, content_type, content_length, date).encode()
    else:
        return RESPONSE_FAIL.format(protocol, resp_code).encode()


def parse_request(request_string):
    request = HTTP_request()
    try:
        request.Method = re.findall(r'^(\w+)', request_string)[0]
    except IndexError:
        request.Method = None

    try:
        request.Protocol = re.findall(r'HTTP/([0-9.]+)', request_string)[0]
    except IndexError:
        request.Protocol = None

    try:
        request.Url = re.findall(r'([^\s?]+)', request_string)[1]
        request.Url = urllib.parse.unquote(request.Url)
    except IndexError:
        request.Url = None

    return request


def request_proc(request_string, document_root=''):
    request = parse_request(request_string)
    protocol = request.Protocol

    if request.Method not in ALLOW_METHODS:
        return response(RESPONSE_CODES["NOT_ALLOWED"], protocol), None

    # Up the folders
    if len(re.findall(r'\.\./', request.Url)) > 1:
        return response(RESPONSE_CODES["FORBIDDEN"], protocol), None

    request.Url += 'index.html' if request.Url[-1] == '/' else ''
    file_path = request.Url[1:]

    try:
        file = os.open(os.path.join(document_root, file_path), os.O_RDONLY)
        flag = fcntl.fcntl(file, fcntl.F_GETFL)
        fcntl.fcntl(file, fcntl.F_SETFL, flag | os.O_NONBLOCK)
    except (FileNotFoundError, IsADirectoryError):
        if 'index.html' in request.Url:
            return response(RESPONSE_CODES["FORBIDDEN"], protocol), None
        else:
            return response(RESPONSE_CODES["NOT_FOUND"], protocol), None
    except OSError:
        return response(RESPONSE_CODES["NOT_FOUND"], protocol), None

    try:
        content_type = MIME_TYPES[re.findall(r'\.(\w+)$', file_path)[0]]
    except KeyError:
        content_type = MIME_TYPES["default"]

    content_length = os.path.getsize(os.path.join(document_root, file_path))

    if request.Method == 'HEAD':
        file = None

    return response(RESPONSE_CODES["OK"], protocol, content_type, str(content_length)), file
