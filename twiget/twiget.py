import json
from json import JSONDecodeError
from threading import Lock, Thread

import requests
from requests.exceptions import ChunkedEncodingError


class TwiGet:
    def __init__(self, bearer):
        self._bearer = bearer
        self._callbacks = dict()
        self._lock = Lock()
        self._stop = True
        self._thread = None

    def add_rule(self, query, tag):
        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {self._bearer}'}
        data = json.dumps({'add': [{'value': query, 'tag': tag}]})

        response = requests.post('https://api.twitter.com/2/tweets/search/stream/rules', headers=headers, data=data)
        return json.loads(response.content.decode())

    def get_rules(self):
        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {self._bearer}'}
        response = requests.get('https://api.twitter.com/2/tweets/search/stream/rules', headers=headers)
        return json.loads(response.content.decode())

    def delete_rules(self, ids):
        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {self._bearer}'}
        data = json.dumps({'delete': {'ids': ids}})
        response = requests.post('https://api.twitter.com/2/tweets/search/stream/rules', headers=headers, data=data)
        return json.loads(response.content.decode())

    def add_callback(self, name, callback):
        self._callbacks[name] = callback

    def get_callbacks(self):
        return list(self._callbacks.items())

    def delete_callback(self, name):
        del self._callbacks[name]

    def _get_stream(self):
        headers = {'Content-type': 'application/json', 'Authorization': f'Bearer {self._bearer}'}
        while not self._stop:
            with requests.get('https://api.twitter.com/2/tweets/search/stream', headers=headers, stream=True) as stream:
                try:
                    for line in stream.iter_lines():
                        try:
                            data = json.loads(line.decode())
                        except JSONDecodeError:
                            data = None
                        if data:
                            for callback_key in self._callbacks:
                                self._callbacks[callback_key](data)
                        if self._stop:
                            break
                except ChunkedEncodingError:
                    pass

    def start_getting_stream(self):
        with self._lock:
            if self._thread is None:
                self._stop = False
                self._thread = Thread(target=self._get_stream)
                self._thread.start()

    def is_getting_stream(self):
        with self._lock:
            return self._thread is not None

    def stop_getting_stream(self):
        with self._lock:
            if self._thread is not None:
                self._stop = True
        if self._thread:
            self._thread.join()
            self._thread = None
