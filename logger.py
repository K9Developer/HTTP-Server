from enum import IntEnum
from datetime import datetime
import inspect
import os

class DebugLevel(IntEnum):
    VERBOSE = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    NONE = 4

class Logger:
    COLORS = {
        'RESET': '\033[0m',
        'GRAY': '\033[90m',
        'BLUE': '\033[34m',
        'YELLOW': '\033[33m',
        'RED': '\033[31m',
        'BOLD': '\033[1m'
    }

    DEBUG_LEVEL = DebugLevel.VERBOSE

    @staticmethod
    def _get_caller_info():
        current_frame = inspect.currentframe()
        frame = current_frame
        while frame:
            if frame.f_back and 'logger.py' not in frame.f_back.f_code.co_filename:
                filename = os.path.basename(frame.f_back.f_code.co_filename)
                line_number = frame.f_back.f_lineno
                return f"{filename}:{line_number}"
            frame = frame.f_back
        return "unknown:0"

    @staticmethod
    def _format_message(level: str, color: str, message: str) -> str:
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        caller_info = Logger._get_caller_info()
        return (f"{Logger.COLORS[color]}[{timestamp}] {level:<8} "
                f"({caller_info}): {message}{Logger.COLORS['RESET']}")

    @staticmethod
    def verbose(message: str) -> None:
        if Logger.DEBUG_LEVEL <= DebugLevel.VERBOSE:
            print(Logger._format_message('VERBOSE', 'GRAY', message))

    @staticmethod
    def info(message: str) -> None:
        if Logger.DEBUG_LEVEL <= DebugLevel.INFO:
            print(Logger._format_message('INFO', 'BLUE', message))

    @staticmethod
    def warning(message: str) -> None:
        if Logger.DEBUG_LEVEL <= DebugLevel.WARNING:
            print(Logger._format_message('WARNING', 'YELLOW', message))

    @staticmethod
    def error(message: str) -> None:
        if Logger.DEBUG_LEVEL <= DebugLevel.ERROR:
            print(Logger._format_message('ERROR', 'RED', str(message)))