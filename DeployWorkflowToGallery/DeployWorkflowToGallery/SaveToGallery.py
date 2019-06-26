import base64
import collections
import hashlib
import hmac
import io
import random
import datetime
import urllib
from typing import Dict
from urllib.parse import quote
import requests
import os
import CollectPackage


class Response:
    def __init__(self, status_code: int, results: str):
        self.status_code: int = status_code
        self.results: str = results


def save_to_gallery(base_url: str, api_key: str, api_secret: str, filepath: str, name: str, owner: str,
                    validate: bool = False, is_public: bool = True, worker_tag: str = "",
                    can_download: bool = True) -> Response:

    if base_url[-1] != '/':
        base_url += "/"
    endpoint = "api/admin/v1/workflows/"
    url = F"{base_url}{endpoint}"
    params = generate_oauth_params(api_key)
    signature = generate_signature("POST", url, params, api_secret)
    params.update({'oauth_signature': signature})

    filename = os.path.basename(filepath)
    ext = filename[-5:].lower()
    if ext == ".yxzp":
        file = open(filepath, 'rb')
    elif ext in [".yxmd", ".yxmc", ".yxwz"]:
        package = CollectPackage.collect_package(filepath)
        zip_bytes = CollectPackage.zip_package(package, filename.lower())
        file = io.BytesIO(zip_bytes)
    else:
        return Response(600, "File is not a supported format.  Must be yxzp, yxmd, yxmc, or yxwz")

    files = {
        'file': (filename, file),
        'name': (None, name),
        'owner': (None, owner),
        'validate': (None, bool_to_str(validate)),
        'isPublic': (None, bool_to_str(is_public)),
        'sourceId': (None, ""),
        'workerTag': (None, worker_tag),
        'canDownload': (None, bool_to_str(can_download)),
    }
    result = requests.post(url, params=params, files=files)
    file.close()
    return Response(result.status_code, result.text)


def quote_string(value) -> str:
    return requests.utils.quote(value, safe="~")


def generate_base_string(method: str, url: str, params: str) -> str:
    return "&".join((method, quote_string(url), quote_string(params)))


def generate_signature(method: str, url: str, params: Dict, secret: str) -> str:
    sorted_params = collections.OrderedDict(sorted(params.items()))
    normalized_params = urllib.parse.urlencode(sorted_params)
    base_string = generate_base_string(method, url, normalized_params)
    base_bytes = bytes(base_string, 'utf-8')
    secret_bytes = bytes("&".join([secret, '']), 'utf-8')
    digester = hmac.new(secret_bytes, base_bytes, hashlib.sha1)
    digest = digester.digest()
    encoded = base64.b64encode(digest)
    return encoded


def generate_oauth_params(api_key: str) -> Dict:
    timestamp = str(int(datetime.datetime.now().timestamp()))
    nonce = str(random.randint(0, 1000000))
    params: Dict = {
        'oauth_timestamp': timestamp,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_consumer_key': api_key,
        'oauth_version': '1.0',
        'oauth_nonce': nonce,
    }
    return params


def bool_to_str(value: bool) -> str:
    if value:
        return 'true'
    else:
        return 'false'
