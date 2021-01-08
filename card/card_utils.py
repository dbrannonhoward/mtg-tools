from data_src.CONSTANTS import CACHE, CACHE_SHA_URL, DATA_PATH, DEBUG, FIREFOX_HEADER, MCACHE
from decimal import Decimal, getcontext
from hashlib import sha256
from json import loads
from os import mknod
from os.path import exists
from pathlib2 import Path
from minimalog.minimal_log import MinimalLog
from string import digits
from sys import exit
from time import perf_counter
from urllib.request import Request, urlopen
getcontext().prec = 4  # TODO Decimal not used
ml = MinimalLog(__name__)


def card_pool_is_dict(card_pool) -> bool:
    """
    :param card_pool: an object that needs to be verified as a dict
    :return: True if card_pool is dict
    """
    ml.log_event('verifying card pool is dict')
    try:
        if isinstance(card_pool, dict):
            ml.log_event('success!')
            return True
        return False
    except TypeError:
        raise TypeError


def fetch_cache() -> dict:
    """
    :return: a json object read from disk into a dict
    """
    ml.log_event('fetch cache and local sha256')
    try:
        cache_src = str(Path(DATA_PATH, CACHE))
        if exists(cache_src):
            with open(cache_src) as cs:
                ml.log_event('success! probably!')
                return loads(cs.read())
        event = 'cache {} not found, exiting python'.format(cache_src)
        print(event)
        ml.log_event(event)
        exit()
    except OSError:
        raise OSError


def filter_duplicate_cards_by_key(card_pool: dict, key='name') -> dict:
    """
    :param card_pool: a CardPool dictionary containing MagicCard dictionaries
    :param key: a dictionary key used to filter multiple values with the same key
    :return: a CardPool dictionary containing MagicCard dictionaries
    """
    # TODO bug, removal is arbitrary, with the first match taking precedence
    unique_card_names = dict()
    temp_uniques = list()
    try:
        for card_id in card_pool:
            card_value_at_key = card_pool[card_id][key]
            if card_value_at_key not in temp_uniques:
                temp_uniques.append(card_value_at_key)
                unique_card_names[card_id] = card_pool[card_id]
        return unique_card_names
    except RuntimeError:
        raise RuntimeError


def generate_mcache():
    """
    :return: TODO
    """
    ml.log_event('TODO generating mcache')
    # TODO FUTURE create mcache file, define data extraction, extract from large dict, write to mcache
    pass


def get_cache_date(cache) -> str:
    """
    :param cache: data read from disk
    :return: a dictionary entry containing cache date
    """
    ml.log_event('get cache date')
    try:
        cache_date = cache['meta']['date']
        return cache_date
    except RuntimeError:
        raise RuntimeError


def get_cache_version(cache) -> str:
    """
    :param cache: data read from disk
    :return: a dictionary entry containing cache version
    """
    ml.log_event('get cache version')
    try:
        cache_date = cache['meta']['version']
        return cache_date
    except RuntimeError:
        raise RuntimeError


def get_len_of_object(func_returns_countable, *args) -> int:
    """
    :param func_returns_countable: a function that returns a countable object
    :param args: optional args that can be passed with func_returns_countable
    :return: number of elements in func_returns_countable's return
    """
    return len(func_returns_countable(*args))


def process_mana_cost(mana_string) -> int:
    """
    :param mana_string: a string representing a card's mana cost
    :return: a raw mana total
    """
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
    """
    :param card_color: the colors of the card
    :param colors: the colors the user has requested
    :return: True if the colors the user has requested are ALL present in colors of the card
    """
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
    """
    :param list_of_strings:
    :return: alphabetical and uppercase string
    """
    try:
        return ''.join(sorted(list_of_strings)).upper()
    except IndexError:
        raise IndexError


def _decimal_difference(start_time: str, stop_time: str) -> Decimal:
    """
    :param start_time: a timestamp
    :param stop_time: a timestamp
    :return: diff between timestamps
    """
    ml.log_event('taking decimal difference of {} from {}'.format(stop_time, start_time))
    try:
        dec_start = Decimal(start_time)
        dec_stop = Decimal(stop_time)
        return dec_stop - dec_start
    except ValueError:
        raise ValueError


def _get_sha256_local() -> str:
    """
    :return: sha256 string calculated on local pc
    """
    ml.log_event('get local sha256')
    if DEBUG:
        ml.log_event('debug mode, skipping local hash check')
        return 'DEBUG'
    with open(str(Path(DATA_PATH, CACHE))) as c:
        checksum = sha256(c.read().encode('utf-8')).hexdigest()
        ml.log_event('hash fetched as {}'.format(checksum))
        return checksum


def _get_sha256_remote() -> str:
    """
    :return: sha256 string fetched from remote url
    """
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


def _is_metadata_valid(local_sha256='', remote_sha_256='') -> bool:
    """
    :return: boolean, False if json data is out-of-date
    """
    ml.log_event('check metadata validity')
    l_sha256, r_sha256 = local_sha256, remote_sha_256
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
    :param color_string: a string representing the colors of a card
    :return: color_string -> remove non-alpha chars -> remove duplicates -> sort alphabetically -> uppercase
    """
    sanitized_string = \
        ''.join(sorted(''.join(set(''.join([letter for letter in color_string if letter.isalpha()]))).upper()))
    # ml.log_event('color string {} sanitized to {}'.format(color_string, sanitized_string))
    return sanitized_string


def _timer_action(start_timer: bool, time_start=None, event=''):
    try:
        if start_timer:
            time_start = round(float(perf_counter()), 3)
            time_stop = None
        else:
            time_start = time_start
            time_stop = round(float(perf_counter()), 3)
        if time_start and time_stop:
            time_elapsed = time_stop - time_start
            ml.log_event('{} elapsed_time : {}'.format(event, time_elapsed))
            return
        ml.log_event('timer started for {}'.format(event))
        return time_start
    except TypeError:
        raise TypeError


print('importing {}'.format(__name__))
ml.log_event('importing {}'.format(__name__))
