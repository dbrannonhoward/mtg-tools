from alive_progress import alive_bar
from card_utils import *
from data_src.CONSTANTS import MCACHE, DATA_PATH
from decimal import Decimal
from decimal import getcontext
from minimalog.minimal_log import MinimalLog
from os import mknod
from os.path import exists
from pathlib2 import Path
from string import digits
from timeit import default_timer
getcontext().prec = 4
ml = MinimalLog()


class CardEngine:
    def __init__(self):
        self.cname = self.__class__.__name__
        ml.log_event('begin init {}'.format(self.cname))
        self.l_sha256, self.r_sha256 = '', ''
        self.data, self.l_sha256 = fetch_cache_and_local_sha()
        self.metadata_valid = self._is_metadata_valid()
        self.all_cards = self._get_all_cards()
        ml.log_event('end init {}'.format(self.cname))

    def _get_all_cards(self) -> dict:
        ml.log_event('get all cards')
        card_dict, sorted_card_dict = dict(), dict()
        delimiter = '_'
        length = self._get_card_data_set_length()
        with alive_bar(length) as get_card_progress:
            for set_key in self.data['data'].keys():
                for card in self.data['data'][set_key]['cards']:
                    card_dict[card['name'] + delimiter +
                              card['setCode'] + delimiter +
                              card['uuid']] = card
                    get_card_progress()
            for k, v in sorted(card_dict.items()):
                sorted_card_dict[k] = v
        return sorted_card_dict

    def _get_all_cards_belonging_to_color_variation(self, search_color_variation: str,
                                                    search_pool=None, only_count=False):
        ml.log_event('get all cards belonging to color variation {}'.format(search_color_variation))
        list_of_cards_with_color_variation = list()
        # TODO move to engine
        if search_pool is None:
            ml.log_event('no search pool provided, starting')
            try:
                for card_id in self.all_cards:
                    card_color_variation = \
                        convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                    if search_color_variation == card_color_variation:
                        list_of_cards_with_color_variation.append(self.all_cards[card_id])
                if only_count:
                    return int(len(list_of_cards_with_color_variation))
                return list_of_cards_with_color_variation
            except RuntimeError:
                raise RuntimeError
        try:
            ml.log_event('search pool provided, starting')
            list_of_cards_in_search_pool_with_color_variation = list()
            for card_id in search_pool:
                card_color_variation = \
                    convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                if search_color_variation == card_color_variation:
                    list_of_cards_in_search_pool_with_color_variation.append(self.all_cards[card_id])
            if only_count:
                return int(len(list_of_cards_in_search_pool_with_color_variation))
            return list_of_cards_in_search_pool_with_color_variation
        except RuntimeError:
            raise RuntimeError

    def _get_all_cards_belonging_to_set(self, set_name_to_find: str, only_count=False):
        ml.log_event('get all cards belonging to set {}'.format(set_name_to_find))
        # TODO move to engine
        cards_belonging_to_set = list()
        set_id = self._get_id_from_set_name(set_name_to_find)
        if set_id:
            for card in self.data['data'][set_id]['cards']:
                cards_belonging_to_set.append(card)
            if only_count:
                return len(cards_belonging_to_set)
            return cards_belonging_to_set
        return None

    def _get_all_cards_with_converted_mana_cost(self, cmc: int, only_count=False):
        ml.log_event('getting all cards with cmc {}'.format(cmc))
        cards_with_search_cmc = list()
        for card_id in self.all_cards.keys():
            mana_cost = self._process_mana_cost(self.all_cards[card_id].get('manaCost'))
            if mana_cost == cmc:
                cards_with_search_cmc.append(self.all_cards[card_id])
        if only_count:
            return len(cards_with_search_cmc)
        return cards_with_search_cmc

    def _get_all_unique_color_variations(self) -> list:
        ml.log_event('get all unique color variations')
        unique_color_variations = list()
        try:
            for card_id in self.all_cards.keys():
                card_color_variation = \
                    convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id]['colors'])
                if card_color_variation not in unique_color_variations:
                    unique_color_variations.append(card_color_variation)
            unique_color_variations.sort()
            return unique_color_variations
        except IndexError:
            raise IndexError

    def _get_cache_date(self) -> str:
        ml.log_event('get cache date')
        return self.data['meta']['date']

    def _get_cache_version(self) -> str:
        ml.log_event('get cache version')
        return self.data['meta']['version']

    def _get_card_data_set_length(self) -> int:
        ml.log_event('get card data set length')
        set_length = 0
        try:
            for set_id in self.data['data'].keys():
                for _ in self.data['data'][set_id]['cards']:
                    set_length += 1
            return set_length
        except ArithmeticError:
            raise ArithmeticError

    def _get_id_from_set_name(self, set_name_to_convert: str) -> str:
        ml.log_event('get id for set name {}'.format(set_name_to_convert))
        try:
            for set_id in self.data['data'].keys():
                set_name_for_id = self.data['data'][set_id].get('mcmName')
                if set_name_to_convert == set_name_for_id:
                    return set_id
        except IndexError:
            raise IndexError

    def _get_list_of_set_ids(self) -> list:
        ml.log_event('get list of set ids')
        list_of_set_ids = list()
        try:
            for set_id in self.data['data'].keys():
                list_of_set_ids.append(set_id)
            return list_of_set_ids
        except RuntimeError:
            raise RuntimeError

    def _get_set_name_from_id(self, id_to_convert: str) -> str:
        ml.log_event('get set name from id {}'.format(id_to_convert))
        for set_id in self.data['data'].keys():
            if id_to_convert == set_id:
                return self.data['data'][set_id]['name']

    def _is_metadata_valid(self) -> bool:
        ml.log_event('check metadata validity')
        self.r_sha256 = get_sha256_remote()
        try:
            mcache = str(Path(DATA_PATH, MCACHE))
            if not exists(mcache):
                try:
                    mknod(path=mcache)
                except OSError:
                    raise OSError
                generate_mcache()
            if not self.r_sha256 and self.l_sha256:
                return False
            if not self.r_sha256 == self.l_sha256:
                return False
            return True
        except OSError:
            raise OSError

    @staticmethod
    def _process_mana_cost(mana_string) -> int:
        ml.log_event('processing mana cost for {}'.format(mana_string))
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


if __name__ == '__main__':
    ce = CardEngine()
else:
    print('importing ' + __name__)
