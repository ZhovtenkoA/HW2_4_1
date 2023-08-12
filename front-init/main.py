import pathlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import json
import socket
from threading import Thread
import datetime


BASE_DIR = pathlib.Path()


class SocketServer(Thread):
    def __init__(self):
        super().__init__()
        self.host = socket.gethostname()
        self.port = 5000
        self.server_socket = None

    def run(self):
        self.server_socket = socket.socket()
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(2)

        while True:
            conn, address = self.server_socket.accept()
            print(f"Connection from {address}")
            client_thread = ClientThread(conn)
            client_thread.start()


class ClientThread(Thread):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn

    def run(self):
        while True:
            message = self.conn.recv(100).decode()
            if not message:
                break
            print(f"Received message server: {message}")
            message = {
                key: value
                for key, value in [el.split("=") for el in message.split("&")]
            }
            print(message)
        self.conn.close()


class MyServer(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        self.save_data_to_json(post_data)
        self.send_response(302)
        self.send_header("Location", "/message")
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        match pr_url.path:
            case "/":
                self.send_html_file("index.html")
            case "/message":
                self.send_html_file("message.html")
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file("error.html", 404)

    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(file, "rb") as fd:  # ./assets/js/app.js
            self.wfile.write(fd.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())


    def save_data_to_json(self, record):
        record = record.decode()
        record = {key: urllib.parse.unquote_plus(value) for key, value in [
            el.split('=') for el in record.split('&')]}
        data_time = datetime.datetime.now()
        data = {str(data_time): record}

        file_path = BASE_DIR.joinpath('storage/data.json')

        if file_path.is_file():
            with open(file_path, 'r', encoding='utf-8') as fd:
                existing_data = json.load(fd)

            existing_data.update(data)
            data = existing_data

        with open(file_path, 'w+', encoding='utf-8') as fd:
            json.dump(data, fd, ensure_ascii=False, indent=2)

        print(data)


def run(server_class=HTTPServer, handler_class=MyServer):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        print("App is working...")
        socket_server = SocketServer()
        socket_server.start()
        http.serve_forever()

    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run()
