from data_src.CONSTANTS import CACHE, CACHE_SHA_URL, DATA_PATH, DEBUG, FIREFOX_HEADER, MCACHE
from decimal import Decimal
from hashlib import sha256
from json import loads
from os import mknod
from os.path import exists
from pathlib2 import Path
from minimalog.minimal_log import MinimalLog
from string import digits
from urllib.request import Request, urlopen
ml = MinimalLog(__name__)


def count_len_of_input_function_return(func_returns_countable, *args) -> int:
    """
    :param func_returns_countable: a function that returns a countable
    :param args: any input arguments passed function needs
    :return: the length of the passed function's return
    """
    return len(func_returns_countable(*args))


def fetch_cache() -> dict:
    ml.log_event('fetch cache and local sha256')
    try:
        with open(str(Path(DATA_PATH, CACHE))) as c:
            ml.log_event('success! probably!')
            return loads(c.read())
    except OSError:
        raise OSError


def filter_duplicate_cards_by_key(cards: dict, key: str) -> dict:
    unique_card_names = dict()
    try:
        for card_id in cards:
            card_value_at_key = cards[card_id][key]
            if card_value_at_key not in unique_card_names.keys():
                unique_card_names[card_value_at_key] = cards[card_id]
        return unique_card_names
    except RuntimeError:
        raise RuntimeError


def generate_mcache():
    ml.log_event('TODO generating mcache')
    # TODO FUTURE create mcache file, define data extraction, extract from large dict, write to mcache
    pass


def get_cache_date(cache) -> str:
    ml.log_event('get cache date')
    try:
        cache_date = cache['meta']['date']
        return cache_date
    except RuntimeError:
        raise RuntimeError


def get_cache_version(cache) -> str:
    ml.log_event('get cache version')
    try:
        cache_date = cache['meta']['version']
        return cache_date
    except RuntimeError:
        raise RuntimeError


def process_mana_cost(mana_string) -> int:
    # ml.log_event('processing mana cost for {}'.format(mana_string))
    mana_sum = 0
    try:
        if mana_string is None:
            return mana_sum
        mana_string = mana_string.replace('{', '').replace('}', '')
        for element in mana_string:
            if element not in digits:
                mana_sum += 1
                continue
            mana_sum += int(element)
        return mana_sum
    except ArithmeticError:
        raise ArithmeticError


def _card_contains_all_colors(card_color: str, colors: str) -> bool:
    c, cc = colors, card_color
    try:
        for color in colors:
            if color not in card_color:
                return False
            colors = colors.replace(color, '')
            if colors == '':
                # ml.log_event('inclusive search color {} matches card color {}'.format(c, cc))
                return True
        return False
    except IndexError:
        raise IndexError


def _convert_list_of_strings_to_alphabetical_string(list_of_strings: list) -> str:
    try:
        return ''.join(sorted(list_of_strings))
    except IndexError:
        raise IndexError


def _decimal_difference(start_time: str, stop_time: str) -> Decimal:
    ml.log_event('taking decimal difference of {} from {}'.format(stop_time, start_time))
    try:
        dec_start = Decimal(start_time)
        dec_stop = Decimal(stop_time)
        return dec_stop - dec_start
    except ValueError:
        raise ValueError


def _get_sha256_local() -> str:
    ml.log_event('get local sha256')
    if DEBUG:
        ml.log_event('debug mode, skipping local hash check')
        return 'DEBUG'
    with open(str(Path(DATA_PATH, CACHE))) as c:
        checksum = sha256(c.read().encode('utf-8')).hexdigest()
        ml.log_event('hash fetched as {}'.format(checksum))
        return checksum


def _get_sha256_remote() -> str:
    ml.log_event('get remote sha256')
    if DEBUG:
        ml.log_event('debug mode, skipping remote hash fetch')
        return 'DEBUG'
    try:
        response = urlopen(Request(url=CACHE_SHA_URL, headers=FIREFOX_HEADER))
    except ConnectionError:
        raise ConnectionError
    try:
        checksum = response.fp.read().decode('utf-8')
        ml.log_event('remote hash fetched from {} as {}'.format(response.url, checksum))
        return checksum
    except UnicodeError:
        raise UnicodeError


def _is_metadata_valid() -> bool:
    ml.log_event('check metadata validity')
    l_sha256 = _get_sha256_local()
    r_sha256 = _get_sha256_remote()
    try:
        mcache = str(Path(DATA_PATH, MCACHE))
        if not exists(mcache):
            try:
                mknod(path=mcache)
            except OSError:
                raise OSError
            generate_mcache()
        if not r_sha256 and l_sha256:
            return False
        if not r_sha256 == l_sha256:
            return False
        ml.log_event('checksums match, metadata is valid!')
        return True
    except OSError:
        raise OSError


def _sanitize_colors(color_string: str) -> str:
    """
    :param color_string: a string, potentially from a user
    :return: remove non-alpha, remove duplicates, alphabetize, and uppercase
    """
    sanitized_string = \
        ''.join(sorted(''.join(set(''.join([letter for letter in color_string if letter.isalpha()]))).upper()))
    # ml.log_event('color string {} sanitized to {}'.format(color_string, sanitized_string))
    return sanitized_string


print('importing {}'.format(__name__))
ml.log_event('importing {}'.format(__name__))
