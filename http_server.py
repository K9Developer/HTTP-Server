import pathlib
import os
import re
from typing import Literal
from concurrent.futures import ThreadPoolExecutor
from constants import CONTENT_TYPES, STATUS_CODES, StatusCode
from http_request import HttpRequest
from logger import Logger
import socket

from route import Route

class HttpServer:

    def __init__(self):
        os.system("cls" if os.name == "nt" else "clear")
        self.routes = {}
        self.allowed_directories = []
        self.moved_routes = {}
        self.blacklisted_files = []
        self.error_pages: dict[StatusCode, Route] = {}
        self.default_error_page = None
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root = pathlib.Path(".").absolute().resolve()

    def __make_path(self, path: str) -> pathlib.Path:
        if type(path) == pathlib.Path:
            return path
        if os.path.isabs(path):
            return pathlib.Path(path)
        return (self.root / path).absolute().resolve()

    def add_route(self, route: Route):
        for alias in route.aliases:
            self.routes[self.__make_path(alias)] = route
        self.routes[self.__make_path(route.path)] = route
        Logger.info(f"Added route {route}")

    def add_error_code_page(self, code: StatusCode, route: Route):
        route.path = self.__make_path(route.path)
        self.error_pages[code] = route

    def set_default_error_code_page(self, route: Route):
        self.default_error_page = route

    def allow_directory(self, path: str):
        self.allowed_directories.append(self.__make_path(path))

    def add_moved_route(self, path: str, new_path: str, type: Literal["temp", "perm"] = "temp"):
        self.moved_routes[self.__make_path(path)] = {"new_path": self.__make_path(new_path), "status_code": StatusCode.MOVED_PERMANENTLY if type == "perm" else StatusCode.MOVED_TEMPORARILY}

    def set_root(self, path: str):
        self.root = self.__make_path(path)
        os.chdir(self.root)

    def disallow_file(self, path: str):
        self.blacklisted_files.append(self.__make_path(path))

    def __receive_http_request(self, client: socket.socket) -> tuple[HttpRequest, StatusCode]:
        http_request, status_code = HttpRequest.receive_http(client)
        if status_code != StatusCode.OK:
            return None, status_code
        return HttpRequest.parse_bytes(http_request)

    def __construct_http_response(self, req: HttpRequest, status_code: StatusCode, headers: dict[str, str], body: bytes) -> bytes:
        status_code_description = STATUS_CODES.get(status_code, "Unknown Error")
        response = [
            f"{req.protocol if req else 'HTTP/1.1'} {status_code} {status_code_description}".encode(),
            *[f"{k}: {v}".encode() for k, v in headers.items()],
            "".encode(),
            body if type(body) == bytes else body.encode()
        ]
        return b"\r\n".join(response)

    def __get_content_type(self, path: str) -> str:
        extension = path.split(".")[-1]
        return CONTENT_TYPES.get(extension, "plain/text")

    def __send_page(self, req: HttpRequest, client: socket.socket, status_code: StatusCode, html: bytes, content_type: str = None):
        if content_type is None:
            path = self.__make_path(req.path)
            path = self.routes[path].path if path in self.routes else path
            if type(path) != str: path = str(path)
            content_type = self.__get_content_type(path)

        headers = {
            "Content-Length": len(html),
            "Content-Type": content_type,
            "Server": "K9Server",
        }
        if status_code == StatusCode.MOVED_PERMANENTLY or status_code == StatusCode.MOVED_TEMPORARILY:
            headers["Location"] = str(self.moved_routes[self.__make_path(req.path)]["new_path"])
        client.sendall(self.__construct_http_response(req, status_code, headers, html))

    def __get_error_page(self, status_code: StatusCode) -> bytes:
        error_page = self.error_pages.get(status_code)
        if error_page:
            with open(self.__make_path(error_page.path), "rb") as f:
                return f.read()
        elif self.default_error_page:
            with open(self.__make_path(self.default_error_page.path), "rb") as f:
                return f.read().replace(b"{{status_code}}", str(status_code).encode())
        return STATUS_CODES.get(status_code, "Unknown Error").encode()

    def __get_file_code(self, path: pathlib.Path) -> StatusCode:
        if path in self.routes:
            path = self.__make_path(self.routes[path].path) # to handle aliases
        if path in self.blacklisted_files:
            return StatusCode.FORBIDDEN
        if not self.__is_file_accessible(path):
            return StatusCode.FORBIDDEN
        if self.moved_routes.get(path):
            return self.moved_routes[path]["status_code"]
        if not path.exists():
            return StatusCode.NOT_FOUND
        if not path.is_file():
            return StatusCode.NOT_IMPLEMENTED
        if not os.access(path, os.R_OK):
            return StatusCode.FORBIDDEN
        return StatusCode.OK

    def __is_file_accessible(self, path: pathlib.Path) -> bool:
        try:
            for directory in self.allowed_directories:
                path.relative_to(directory)
                return True
        except ValueError:
            return False
        
        return path in self.routes

    def __strip_params(self, path: pathlib.Path) -> tuple[str, dict[str, str]]:
        path = str(path)
        if "?" not in path:
            return self.__make_path(path), {}
        path, params = path.split("?")
        return self.__make_path(path), {k: v for k, v in [param.split("=") for param in params.split("&")]}

    def __parse_return_data(self, ret) -> dict:
        if ret is None:
            return None
        if type(ret) == dict:
            ret["status_code"] = ret.get("status_code", StatusCode.OK)
            ret["content_type"] = ret.get("content_type", "plain/text")
            ret["body"] = ret.get("body", b"")
            return ret
        if type(ret) == int:
            return {"status_code": ret, "content_type": "plain/text", "body": b""}
        return {"status_code": StatusCode.OK, "content_type": "plain/text", "body": ret}

    def __handle_get_request(self, req: HttpRequest, client: socket.socket, addr: tuple):
        req.log(addr[0])
        
        requested_path = self.__make_path(req.path)
        path, params = self.__strip_params(requested_path)
        requested_path = path
        req.path = requested_path
        route = self.routes.get(requested_path)
        if not route and self.__is_file_accessible(requested_path):
            file_code = self.__get_file_code(requested_path)
            if file_code != StatusCode.OK:
                page = self.__get_error_page(file_code)
                self.__send_page(req, client, file_code, page, "text/html")
                return
            
            with open(requested_path, "rb") as f:
                data = f.read()
            self.__send_page(req, client, StatusCode.OK, data)
            return

        ret = route.handler(req, client, params, req.body)
        ret_data = self.__parse_return_data(ret)
        if ret_data is None:
            requested_path = self.__make_path(route.path) if route else requested_path
            file_code = self.__get_file_code(requested_path)
            if file_code != StatusCode.OK:
                page = self.__get_error_page(file_code)
                self.__send_page(req, client, file_code, page, "text/html")
                return
            with open(requested_path, "rb") as f:
                data = f.read()
            self.__send_page(req, client, StatusCode.OK, data)
        else:
            if ret_data["status_code"] != StatusCode.OK:
                page = self.__get_error_page(ret_data["status_code"])
                self.__send_page(req, client, ret_data["status_code"], page, "text/html")
                return
            self.__send_page(req, client, ret_data["status_code"], ret_data["body"], ret_data["content_type"])

        Logger.verbose(f"Closing connection from {addr}")        

    def __handle_client(self, client: socket.socket, addr: tuple):
        req, read_code = self.__receive_http_request(client)
        callback = {
            "GET": self.__handle_get_request,
            "POST": self.__handle_get_request,
        }

        if read_code != StatusCode.OK:
            page = self.__get_error_page(read_code)
            self.__send_page(req, client, page, str(read_code).encode())
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            return
        
        if req is None:
            page = self.__get_error_page(StatusCode.BAD_REQUEST)
            self.__send_page(req, client, StatusCode.BAD_REQUEST, page)
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            return
        
        if req.method not in callback:
            page = self.__get_error_page(StatusCode.METHOD_NOT_ALLOWED)
            self.__send_page(req, client, StatusCode.METHOD_NOT_ALLOWED, page)
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            Logger.verbose(f"Received invalid method {req.method} from {addr}")
            return
        
        callback[req.method](req, client, addr)
        client.shutdown(socket.SHUT_RDWR)
        client.close()

    def __print_box(self, lines: list[str]):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        pure_lines = [ansi_escape.sub('', line) for line in lines]
        PADDING, GREEN, WHITE, RESET = 10, "\033[32m", "\033[37m", "\033[0m"
        width = len(max(pure_lines, key=len)) + PADDING
        
        top = f"{GREEN}╭{'─' * (width - 2)}╮{RESET}"
        bottom = f"{GREEN}╰{'─' * (width - 2)}╯{RESET}"
        vert_pad = f"{GREEN}│{WHITE}{' ' * (width - 2)}{GREEN}│{RESET}"
        
        print(top)
        print(vert_pad)
        for i, line in enumerate(lines):
            pure_len = len(pure_lines[i])
            left_padding = (width - 2 - pure_len) // 2
            right_padding = width - 2 - pure_len - left_padding
            padded_line = ' ' * left_padding + line + ' ' * right_padding
            print(f"{GREEN}│{WHITE}{padded_line}{GREEN}│{RESET}")
        print(vert_pad)
        print(bottom)

    def start(self, port: int):
        Logger.info(f"Starting server on port {port}")
        self.soc.bind(("0.0.0.0", port))
        self.soc.listen(50)
        self.soc.setblocking(False)
        public_ip = socket.gethostbyname(socket.gethostname())
        self.__print_box([
            f"Visit \033[34mhttp://localhost:{port}\033[0m",
            f"Or visit \033[34mhttp://{public_ip}:{port}\033[0m",
            "Press \033[33mCtrl+C\033[0m to stop the server"
        ])

        with ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                try:
                    client, addr = self.soc.accept()
                    Logger.verbose(f"Connection from {addr}")
                    executor.submit(self.__handle_client, client, addr)
                except BlockingIOError:
                    pass
                except KeyboardInterrupt:
                    Logger.info("Stopping server")
                    executor.shutdown(wait=False)
                    break