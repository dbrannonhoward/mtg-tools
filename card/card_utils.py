from data_src.CONSTANTS import CACHE, CACHE_SHA_URL, DATA_PATH, DEBUG, FIREFOX_HEADER
from decimal import Decimal
from hashlib import sha256
from json import loads
from pathlib2 import Path
from minimalog.minimal_log import MinimalLog
from urllib.request import Request, urlopen
ml = MinimalLog(__name__)


def convert_list_of_strings_to_alphabetical_string(list_of_strings: list) -> str:
    return ''.join(sorted(list_of_strings))


def decimal_difference(start_time: str, stop_time: str) -> Decimal:
    dec_start = Decimal(start_time)
    dec_stop = Decimal(stop_time)
    return dec_stop - dec_start


def fetch_cache_and_local_sha() -> tuple:
    ml.log_event('fetch cache and local sha256')
    try:
        with open(str(Path(DATA_PATH, CACHE))) as c:
            raw_string = c.read()
            return loads(raw_string), get_sha256_local(raw_string)
    except OSError:
        raise OSError


def generate_mcache():
    ml.log_event('TODO generating mcache')
    # TODO FUTURE create mcache file, define data extraction, extract from large dict, write to mcache
    pass


def get_sha256_local(raw_string) -> str:
    ml.log_event('get local sha256')
    if DEBUG:
        return 'DEBUG'
    return sha256(raw_string.encode('utf-8')).hexdigest()


def get_sha256_remote() -> str:
    ml.log_event('get remote sha256')
    if DEBUG:
        return 'DEBUG'
    try:
        response = urlopen(Request(url=CACHE_SHA_URL, headers=FIREFOX_HEADER))
    except ConnectionError:
        raise ConnectionError
    try:
        hash_bytes = response.fp.read()
        return hash_bytes.decode('utf-8')
    except UnicodeError:
        raise UnicodeError


print('importing ' + __name__)
