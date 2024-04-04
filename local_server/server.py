# projz_renpy_translation, a translator for RenPy games
# Copyright (C) 2023  github.com/abse4411
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
import socket
import threading
import time
from threading import Lock
from queue import Queue
from typing import List

from flask import Flask, abort, request, jsonify

from local_server.index import WebTranslationIndex
from trans import Translator
from util import my_input, line_to_args

app = Flask(__name__)
app.logger.disabled = True
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.disabled = True
# _required_fields = ['identifier', 'text', 'language', 'type', 'gamedir']
_required_fields = ['identifier', 'text', 'language', 'type', 'substituted']

_cache_res = {}
_cache_lock = Lock()


def ok_of(response: dict):
    response['code'] = 0
    return response


_translation_index: WebTranslationIndex = None
_index_lock = Lock()


def set_index(index: WebTranslationIndex):
    global _translation_index
    with _index_lock:
        _translation_index = index


def get_index():
    global _translation_index
    with _index_lock:
        return _translation_index


@app.post('/translation')
def translation():
    if request.json:
        payload = request.json
        for f in _required_fields:
            if f not in payload:
                abort(400)
    else:
        abort(400)
    # print(payload['text'], payload['identifier'], payload['type'])
    index = get_index()
    new_text = None
    if index:
        new_text = index.translate(payload)
        # print(f'new text: {new_text}')
    return jsonify(ok_of({'new_text': new_text}))


from werkzeug.serving import make_server


class MockTranslator(Translator):

    def translate(self, text: str):
        return text + ' (Google)'


def is_binded_port(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError as e:
            logging.exception(e)
            return True


class FlaskServer(threading.Thread):

    def __init__(self, index: WebTranslationIndex, host: str, port: int):
        super().__init__(daemon=True)
        set_index(index)
        self.index = index
        self._host = host
        self._port = port
        self._server = None
        self._event = threading.Event()
        self._event.clear()
        self._done = False
        self.error = None

    def run(self):
        print(f'Starting server with: {self._host}:{self._port}')
        try:
            with make_server(self._host, self._port, app) as server:
                self.index.start()
                self._server = server
                self._done = True
                self._event.set()
                server.serve_forever()
        except Exception as e:
            self.index.stop()
            self._server = None
            logging.exception(e)
            self.error = e
        finally:
            self._event.set()

    def start_server(self):
        print('Launching server...')
        if not is_binded_port(self._host, self._port):
            self.start()
            self._event.wait()
            return self._done
        else:
            return False

    def is_stopped(self):
        return self._server is None

    def stop_server(self):
        if self._server:
            self.index.stop()
            self._server.shutdown()
            self._server = None

    def set_translator(self, translator: Translator, font:str):
        self.index.stop()
        self.index.set_translator(translator, font)
        self.index.start()