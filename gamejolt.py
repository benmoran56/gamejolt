import json as _json
import hashlib as _hashlib

from concurrent.futures import ProcessPoolExecutor as _Executor
from urllib.request import urlopen as _urlopen
from urllib.parse import urlencode as _urlencode
from urllib.parse import urljoin as _urljoin
from functools import lru_cache as _lru_cache


class GameJoltAPI:
    def __init__(self, game_id, private_key, username=None, token=None):
        """Interface for the Game Jolt game API.

        :param game_id: str
        :param private_key: str
        :param username: str
        :param token: str
        """
        self._game_id = game_id
        self._private_key = private_key
        self.username = username
        self.token = token

        self._base_url = "http://api.gamejolt.com/api/game/v1/"
        self._values = {'format': 'json', 'game_id': self._game_id}

        self._executor = _Executor(max_workers=1)

    @_lru_cache()
    def _encode_signed_url(self, url):
        """Add a signature parameter to a url.

        :param url: A fully formed url, without a signature.
        :return: A str of the signed url, ready to use for an API call.
        """
        url_bytes = bytearray(url + self._private_key, encoding='ascii')
        signature = _hashlib.sha1(url_bytes).hexdigest()
        parameter = _urlencode({"signature": signature})
        return "{}&{}".format(url, parameter)

    def _submit(self, endpoint, values):
        """Submit an API call with url and optional parameters.

        :param endpoint: A fully formed url including endpoint.
        :param values: A dictionary of parameters. Non-signed.
        :return: A `Future` containing the API response.
        """
        url = "{}?{}".format(endpoint, _urlencode(values))
        signed_url = self._encode_signed_url(url)
        return self._executor.submit(self._get_response, signed_url)

    @staticmethod
    def _get_response(signed_url):
        """Perform an API query and return the result.

        :param signed_url: A fully formed url with signature.
        :return: A dict containing the response.
        """
        try:
            http_response = _urlopen(signed_url)
            response = _json.loads(http_response.read())['response']
            return response
        except Exception as e:
            return {'success': 'false', 'error': str(e)}

    def session_open(self):
        """Open a user session.

        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "sessions/open/")
        values = self._values.copy()
        values['username'] = self.username
        values['user_token'] = self.token
        return self._submit(endpoint, values)

    def session_ping(self, idle=False):
        """Send a keep-alive ping for an open session.

        :param idle: If True, set the session status to 'idle'.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "sessions/ping/")
        values = self._values.copy()
        values['username'] = self.username
        values['user_token'] = self.token
        if idle:
            values['status'] = "idle"
        else:
            values['status'] = "active"
        return self._submit(endpoint, values)

    def session_close(self):
        """Close an open user session.

        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "sessions/close/")
        values = self._values.copy()
        values['username'] = self.username
        values['user_token'] = self.token
        return self._submit(endpoint, values)

    def trophies_fetch(self, achieved=False, trophy_id=None):
        """Fetch a dictionary of trophies.

        :param achieved: If True, only fetch achieved trophies.
        :param trophy_id: Fetch a specific trophy, by ID. Setting this
               will override the `achieved` parameter.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "trophies/")
        values = self._values.copy()
        values['username'] = self.username
        values['user_token'] = self.token
        if achieved:
            values['achieved'] = "true"
        # TODO: allow a list of multiple IDs:
        if trophy_id:
            values['trophy_id'] = trophy_id
        return self._submit(endpoint, values)

    def trophies_add_achieved(self, trophy_id):
        """Set a specific trophy ID as having been achieved.

        :param trophy_id: The ID of the trophy to set to achieved.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "trophies/add-achieved/")
        values = self._values.copy()
        values['username'] = self.username
        values['user_token'] = self.token
        values['trophy_id'] = trophy_id
        return self._submit(endpoint, values)

    def scores_fetch(self, table_id=None, limit=10):
        """Fetch the game scores.

        :param table_id: Fetch a specific score table. If None, the
               default score table will be returned.
        :param limit: Set an upper limit on how many scores to return.
               Defaults to 10.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "scores/")
        values = self._values.copy()
        values['limit'] = limit
        if table_id:
            values['table_id'] = table_id
        return self._submit(endpoint, values)

    def scores_add(self, sort, score=None, table_id=None):
        """Submit a new game score.

        Submit a new score to the default table, or to a specific table.
        If a "username" and "token" is available, the score will be submitted
        under that users account. Otherwise, the score will be submitted as a
        guest.

        :param sort: An int of the score.
        :param score: An optional score display name. If None,
               defaults to the sort value.
        :param table_id: Add the score to a specific table. If None,
               defaults to the Main table.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "scores/add/")
        values = self._values.copy()
        if self.username and self.token:
            values['username'] = self.username
            values['user_token'] = self.token
        else:
            values['guest'] = "Guest"
        values['sort'] = sort
        values['score'] = score or sort
        if table_id:
            values['table_id'] = table_id
        return self._submit(endpoint, values)

    def scores_tables(self):
        """Retrieve information on available score tables.

        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "scores/tables/")
        return self._submit(endpoint, self._values)

    def data_store_fetch(self, key, public=False):
        """Retrieve the data for a specific key.

        Retrieve data for the specified key. If a "username" and "token"
        is available, it will be retrieved from that specific account.
        Otherwise, the public key data will be retrieved. You can
        also pass the 'public=True' parameter to specifically request
        public data retrieval.

        :param key: The key for the data to retrieve.
        :param public: If True, always retrieve public key data.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "data-store/")
        values = self._values.copy()
        values['key'] = key
        if self.username and self.token and not public:
            values['username'] = self.username
            values['user_token'] = self.token
        return self._submit(endpoint, values)

    def data_store_set(self, key, data, public=False):
        """Set the data for a specific key.

        Set data for the specified key. If a "username" and "token"
        is available, it will be set for that account. Otherwise,
        the data will be set to the public key. You can also pass
        the 'public=True' parameter to specifically set the public
        key data.

        :param key: The key to set the data to.
        :param data: The data to send.
        :param public: If True, always set the data to the public key.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "data-store/set/")
        values = self._values.copy()
        values['key'] = key
        values['data'] = data
        if self.username and self.token and not public:
            values['username'] = self.username
            values['user_token'] = self.token
        return self._submit(endpoint, values)

    def data_store_update(self, key, operation, value, public=False):
        """Perform an update operation on data for a specific key.

        You can perform specific operations to previously set key data.
        The available operations are 'add', 'subtract', 'multiply' and
        'divide' for numeric data, and 'append' and 'prepend' for string
        data. See the Game Jolt API documentation for more information.

        If a "username" and "token" is available, the operations are
        performed for data under that account. Otherwise, the operations
        are performed on the public key data. You can also pass the
        'public=True' parameter to specifically operate on the public data.

        :param key: The key to perform the operation on.
        :param operation: The operation to perform.
        :param value: The value to use in the operation.
        :param public: If True, always operate on public data.
        :return: A `Future` containing the API response.
        """
        assert operation in ('add', 'subtract', 'multiply', 'divide', 'append', 'prepend')
        endpoint = _urljoin(self._base_url, "data-store/update/")
        values = self._values.copy()
        values['key'] = key
        values['operation'] = operation
        values['value'] = value
        if self.username and self.token and not public:
            values['username'] = self.username
            values['user_token'] = self.token
        return self._submit(endpoint, values)

    def data_store_remove(self, key, public=False):
        """Delete a key and it's data from the data store.

        Completely remove a key, and it's data from the data store.
        If a "username" and "token" is available, the key will be deleted
        from that specific account. Otherwise, the public key and it's data
        will be deleted. You can also pass the 'public=True' parameter to
        specifically target the public data for deletion.

        :param key: The key and its data to delete.
        :param public: If True, delete a public key and data.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "data-store/remove/")
        values = self._values.copy()
        values['key'] = key
        if self.username and self.token and not public:
            values['username'] = self.username
            values['user_token'] = self.token
        return self._submit(endpoint, values)

    def data_store_get_keys(self, public=False):
        """Retrieve all available keys in the data store.

        If a "username" and "token" is avialable, the keys will be shown
        for that specific account. Otherwise, the public keys will be shown.
        You can also pass the 'public=True' parameter to specifically
        retrieve public keys.

        :param public: If True, retrieve the public keys.
        :return: A `Future` containing the API response.
        """
        endpoint = _urljoin(self._base_url, "data-store/get-keys/")
        values = self._values.copy()
        if self.username and self.token and not public:
            values['username'] = self.username
            values['user_token'] = self.token
        return self._submit(endpoint, values)
