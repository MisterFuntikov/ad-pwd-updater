import re
import os
import sys
import logging
from datetime import datetime


class OutputLogger:
    emit_write = None

    class Severity:
        DEBUG = 'DEBUG'
        ERROR = 'ERROR'

    def __init__(self, io_stream, severity, emit):
        super().__init__()
        self.io_stream = io_stream
        self.severity = severity
        self.emit_write = emit

    def write(self, text=''):
        if not re.fullmatch(r'\s+', text) and text != '':
            self.emit_write(text)

    def flush(self):
        self.io_stream.flush()
        pass


class LOGGER:

    _folder = None
    _object = None
    _handler = None
    _format = None
    _filedate = None
    _level_action = {}

    def __init__(self, folder=None):
        if not folder or os.path.isdir(folder) == False:
            # folder = 'log/'
            # os.mkdir(folder)
            pass
        self._folder = folder
        self._format = logging.Formatter(
            '%(asctime)s -- %(levelname)s -- %(message)s')
        self._object = logging.getLogger('logger')
        self._object.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(self._format)
        self._object.addHandler(console_handler)
        self._level_action = {
            'DEBUG': self._object.debug,
            'INFO': self._object.info,
            'WARNING': self._object.warning,
            'ERROR': self._object.error,
            'CRITICAL': self._object.critical,
        }
        sys.stdout = OutputLogger(
            sys.stdout, OutputLogger.Severity.DEBUG, self._object.debug)
        sys.stderr = OutputLogger(
            sys.stdout, OutputLogger.Severity.ERROR, self._object.error)
        pass

    def setFile(self) -> bool:
        cd = datetime.now().date()
        if cd == self._filedate:
            return True
        self._filedate = cd

        if not self._folder or os.path.isdir(self._folder) == False:
            return False

        fname = cd.strftime('%Y-%m-%d') + '.log'
        fname = os.path.join(self._folder, fname)
        if self._handler != None:
            self._object.removeHandler(self._handler)
        self._handler = logging.FileHandler(
            filename=fname, encoding='UTF8', mode='a')
        self._handler.setLevel(logging.DEBUG)
        self._handler.setFormatter(self._format)
        self._object.addHandler(self._handler)
        return True

    def log(self, msg: str, level='INFO'):
        if datetime.now().date() != self._filedate:
            self.setFile()
        level = level.upper()
        if level in self._level_action:
            self._level_action[level](msg)
        else:
            self._object.info(msg)
        pass
