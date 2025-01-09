import pathlib
import re
import datetime
import socket
from constants import HTTP_SPLIT_REGEX, StatusCode
from logger import Logger

class HttpRequest:
    
    def __init__(self, method: str, path: str, protocol: str, headers: dict[str, any], body: bytes):
        self.method = method
        self.path = str(pathlib.Path('.'+path).absolute().resolve())
        self.protocol = protocol
        self.headers = headers
        self.body = body

    def __repr__(self):
        return f"HttpRequest({self.method}, {self.path}, {self.protocol}, {list(self.headers.keys())}, {self.body})"
    
    def log(self, src):
        time = datetime.datetime.now().strftime("%H:%M:%S")
        Logger.info(f"{src} - [{time}] {self.method} {self.path} {self.protocol}")

    @staticmethod
    def parse_bytes(data: bytes) -> 'HttpRequest':
        Logger.verbose("Parsing HTTP request")
        groups = re.match(HTTP_SPLIT_REGEX, data, re.MULTILINE | re.DOTALL).groups()
        if len(groups) < 5:
            return None, StatusCode.BAD_REQUEST
        headers = {k: v for k, v in [(header.split(": ")[0], header.split(": ")[1]) for header in groups[3].decode().split("\r\n") if header]}
        return HttpRequest(groups[0].decode(), groups[1].decode(), groups[2].decode(), headers, groups[4] if groups[4] else b""), StatusCode.OK
    
    @staticmethod
    def __find_header_value(data: bytes, header: str) -> str:
        header = header.lower()
        data = data.decode().lower()
        start = data.find(header)
        if start == -1:
            return None
        start += len(header) + 2
        end = data.find("\r\n", start)
        return data[start:end]

    @staticmethod
    def receive_http(client: socket.socket) -> tuple[bytes, StatusCode]:
        client.setblocking(True)
        try:
            data = b""
            continue_to = float("inf")
            found_body = False
            while continue_to > 0:
                b = client.recv(1)
                if b == b"":
                    return None, StatusCode.CLIENT_CLOSED_REQUEST
                
                data += b
                if data[-4:] == b"\r\n\r\n" and not found_body:
                    found_body = True
                    header_val = HttpRequest.__find_header_value(data, "Content-Length")
                    if header_val and header_val.isdigit():
                        continue_to = int(header_val)
                        if continue_to < 0:
                            return None, StatusCode.BAD_REQUEST
                    elif header_val and not header_val.isdigit():
                        return None, StatusCode.BAD_REQUEST
                    else:
                        continue_to = 0
                continue_to -= 1

            Logger.verbose("Received HTTP request")
            client.setblocking(False)
            return data, StatusCode.OK
        
        except TimeoutError:
            Logger.error("Request timed out (REQUEST_TIMEOUT)")
            client.setblocking(False)
            return None, StatusCode.REQUEST_TIMEOUT
        except Exception as e:
            Logger.error(f"Failed to receive HTTP request: {e} (INTERNAL_SERVER_ERROR)")
            client.setblocking(False)
            return None, StatusCode.INTERNAL_SERVER_ERROR
