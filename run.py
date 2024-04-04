import http.server
import http.client
from http import HTTPStatus
import json
import sys


server_list = json.load(open('server_list.json', 'r'))


class ForwardHandler(http.server.BaseHTTPRequestHandler):
    server_version = "NanoCDN/1.0"
    protocol_version = "HTTP/1.1"

    def log_request(self, code='-', size='-'):
        if isinstance(code, HTTPStatus):
            code = code.value
        self.log_message('%s "%s" %s %s',
                         self.headers['Host'], self.requestline, str(code), str(size))

    def send_response(self, code, message=None):
        self.log_request(code)
        self.send_response_only(code, message)
        self.send_header('Server', self.server_version)

    # =======================================================

    def do_GET(self):
        # Forward the request to the target server
        # Get the target server from the request, header HOST
        target_server = self.headers['Host']
        if target_server not in server_list:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return
        # Get the target method from the request
        target_method = self.command
        # Get the target path from the request
        target_path = self.path

        # Forward the request to the target server
        # Create a new request to the target server
        target_request = http.client.HTTPConnection(server_list[target_server])
        # Send the request to the target server
        try:
            target_request.request(target_method, target_path)
        except (ConnectionRefusedError, OSError):
            self.close_connection = True
            self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
            self.end_headers()
            return
        # Get the response from the target server
        target_response = target_request.getresponse()
        # Send the response to the client
        self.send_response(target_response.status)
        for name, value in target_response.getheaders():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(target_response.read())
        # Close the connection to the target server
        target_request.close()

    def do_HEAD(self):
        # Forward the request to the target server
        # Get the target server from the request, header HOST
        target_server = self.headers['Host']
        if target_server not in server_list:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return
        # Get the target method from the request
        target_method = self.command
        # Get the target path from the request
        target_path = self.path

        # Forward the request to the target server
        # Create a new request to the target server
        target_request = http.client.HTTPConnection(server_list[target_server])
        # Send the request to the target server
        try:
            # target_request.request(target_method, target_path)
            target_request.request('GET', target_path)  # Bug 1: HeadAmp
        except (ConnectionRefusedError, OSError):
            self.close_connection = True
            self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
            self.end_headers()
            return
        # Get the response from the target server
        target_response = target_request.getresponse()
        # Send the response to the client
        self.send_response(target_response.status)
        for name, value in target_response.getheaders():
            self.send_header(name, value)
        self.end_headers()
        # self.wfile.write(target_response.read())  # The only difference with do_GET
        # Close the connection to the target server
        target_request.close()

    def do_POST(self):
        # Forward the request to the target server
        # Get the target server from the request, header HOST
        target_server = self.headers['Host']
        if target_server not in server_list:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            return
        # Get the target method from the request
        target_method = self.command
        # Get the target path from the request
        target_path = self.path
        # Get the target body from the request
        target_content_length = int(self.headers.get('Content-Length', '0'))
        target_body = self.rfile.read(target_content_length)

        # Forward the request to the target server
        # Create a new request to the target server
        target_request = http.client.HTTPConnection(server_list[target_server])
        # Send the request to the target server
        try:
            target_request.request(target_method, target_path, target_body)
        except (ConnectionRefusedError, OSError):
            self.close_connection = True
            self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
            self.end_headers()
            return
        # Get the response from the target server
        target_response = target_request.getresponse()
        # Send the response to the client
        self.send_response(target_response.status)
        for name, value in target_response.getheaders():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(target_response.read())
        # Close the connection to the target server
        target_request.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8090
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, ForwardHandler)
    httpd.serve_forever()
