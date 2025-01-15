HTTP_SPLIT_REGEX = rb"(GET|POST|HEAD|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH) (.*?) (HTTP\/\d\.\d)\r\n((?:.*?\r\n)*?)\r\n(.*)"

STATUS_CODES = {400: "Bad Request",401: "Unauthorized",403: "Forbidden",404: "Not Found",405: "Method Not Allowed",500: "Internal Server Error",501: "Not Implemented",502: "Bad Gateway",503: "Service Unavailable",504: "Gateway Timeout",505: "HTTP Version Not Supported",301: "Moved Permanently",302: "Found",303: "See Other",304: "Not Modified",307: "Temporary Redirect",308: "Permanent Redirect",200: "OK"}

CACHE_MINUTES = 5

class StatusCode:
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    REQUEST_TIMEOUT = 408
    CLIENT_CLOSED_REQUEST = 499
    INTERNAL_SERVER_ERROR = 500
    NOT_IMPLEMENTED = 501
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504
    HTTP_VERSION_NOT_SUPPORTED = 505
    MOVED_PERMANENTLY = 301
    MOVED_TEMPORARILY = 302
    FOUND = 302
    SEE_OTHER = 303
    NOT_MODIFIED = 304
    TEMPORARY_REDIRECT = 307
    PERMANENT_REDIRECT = 308
    OK = 200

CONTENT_TYPES = {
    "html": "text/html",
    "css": "text/css",
    "js": "application/javascript",
    "json": "application/json",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "ico": "image/x-icon",
    "txt": "text/plain",
    "xml": "application/xml",
    "pdf": "application/pdf",
    "zip": "application/zip",
    "tar": "application/x-tar",
    "gz": "application/gzip",
    "mp3": "audio/mpeg",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "ogg": "audio/ogg",
    "webp": "image/webp",
    "flac": "audio/flac",
    "wav": "audio/wav",
}