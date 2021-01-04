from alive_progress import alive_bar
from card_utils import *
from decimal import getcontext
from minimalog.minimal_log import MinimalLog
from string import digits
getcontext().prec = 4
ml = MinimalLog()


class CardEngine:
    def __init__(self):
        self.cname = self.__class__.__name__
        ml.log_event('begin init {}'.format(self.cname))
        self.l_sha256, self.r_sha256 = '', ''
        self.data = fetch_cache()
        self.metadata_valid = is_metadata_valid()
        self.all_cards = self._get_all_cards()
        ml.log_event('end init {}'.format(self.cname))

    def _count_all_cards(self) -> int:
        """
        :return: a count of all cards in magic the gathering, with no uniqueness checking
        """
        try:
            return self._count_len_of_return(self._count_all_cards)
        except RuntimeError:
            raise RuntimeError

    def _count_all_cards_in_set(self, *args) -> int:
        """
        :param args: set name string
        :return: count of cards in set
        """
        try:
            return self._count_len_of_return(self._count_all_cards_in_set, *args)
        except Exception:
            raise Exception

    def _count_all_cards_with_colors(self, *args) -> int:
        """
        :param args: a list of colors
        :return: a count of all cards sharing all of the colors, exclusive
        """
        try:
            return self._count_len_of_return(self._get_all_cards_with_exact_colors, *args)
        except RuntimeError:
            raise RuntimeError

    def _count_all_cards_with_converted_mana_cost(self, *args):
        """
        :param args: converted mana cost, an integer
        :return: count of all cards with that converted mana cost, not filtered for uniqueness
        """
        return self._count_len_of_return(self._get_all_cards_with_converted_mana_cost, *args)

    @staticmethod
    def _count_len_of_return(function_that_returns_object_with_length, *args) -> int:
        """
        :param function_that_returns_object_with_length: a function that returns a countable
        :param args: any input arguments that function may need
        :return: the length of the passed function's return
        """
        return len(function_that_returns_object_with_length(*args))

    def _debug(self) -> None:
        pass

    @staticmethod
    def _filter_duplicate_cards_by_key(cards: list, key: str) -> list:
        unique_card_names = list()
        for card in cards:
            if card[key] not in unique_card_names:
                # ml.log_event('unique card {} found'.format(card[key]))
                unique_card_names.append(card[key])
        return unique_card_names

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

    def _get_all_cards_with_colors(self, colors: str, search_pool=None) -> list:
        """
        :param colors: a color variation string, for example: 'BW' for 'black and white'
        :param search_pool: a user-specified list() of card object dict() through which to apply this search
        :return: a list() of card object dict()
        """
        ml.log_event('get all cards that have at least color variation {}'.format(colors))
        list_of_cards_with_colors = list()
        colors = sanitize_colors(colors)
        if search_pool is None:
            ml.log_event('no search pool provided, starting')
            try:
                for card_id in self.all_cards:
                    card_color = \
                        convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                    if card_contains_all_colors(card_color, colors):
                        # ml.log_event('inclusive search color {} matches card color {}'.format(colors, card_color))
                        list_of_cards_with_colors.append(self.all_cards[card_id])
                return list_of_cards_with_colors
            except RuntimeError:
                raise RuntimeError
        ml.log_event('search pool provided, starting')
        try:
            for card_id in search_pool:
                card_color = \
                    convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                if card_contains_all_colors(card_color, colors):
                    # ml.log_event('inclusive search color {} matches card color {}'.format(colors, card_color))
                    list_of_cards_with_colors.append(self.all_cards[card_id])
            return list_of_cards_with_colors
        except RuntimeError:
            raise RuntimeError

    def _get_all_cards_with_exact_colors(self, colors: str, search_pool=None) -> list:
        """
        :param colors: a color variation string, for example: 'BW' for 'black and white'
        :param search_pool: a user-specified list() of card object dict() through which to apply this search
        :return: a list() of card object dict()
        """
        ml.log_event('get all cards belonging to color variation {}'.format(colors))
        list_of_cards_with_colors = list()
        colors = sanitize_colors(colors)
        if search_pool is None:
            ml.log_event('no search pool provided, starting')
            try:
                for card_id in self.all_cards:
                    card_color = \
                        convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                    if colors == card_color:
                        # ml.log_event('exclusive search color {} matches card color {}'.format(colors, card_color))
                        list_of_cards_with_colors.append(self.all_cards[card_id])
                return list_of_cards_with_colors
            except RuntimeError:
                raise RuntimeError
        try:
            ml.log_event('search pool provided, starting')
            list_of_cards_in_search_pool_with_color_variation = list()
            for card_id in search_pool:
                card_color = \
                    convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                if colors == card_color:
                    # ml.log_event('exclusive search color {} matches card color {}'.format(colors, card_color))
                    list_of_cards_in_search_pool_with_color_variation.append(self.all_cards[card_id])
            return list_of_cards_in_search_pool_with_color_variation
        except RuntimeError:
            raise RuntimeError

    def _get_all_cards_in_set(self, set_name: str) -> list:
        """
        :param set_name: find cards in set_name
        :return: cards in set_name
        """
        ml.log_event('get all cards belonging to set {}'.format(set_name))
        cards_belonging_to_set = list()
        set_id = self._get_id_from_set_name(set_name)
        try:
            if set_id:
                for card in self.data['data'][set_id]['cards']:
                    cards_belonging_to_set.append(card)
                return cards_belonging_to_set
        except RuntimeError:
            raise RuntimeError

    def _get_all_cards_with_converted_mana_cost(self, cmc: int) -> list:
        ml.log_event('getting all cards with cmc {}'.format(cmc))
        cards_with_search_cmc = list()
        for card_id in self.all_cards.keys():
            mana_cost = self._process_mana_cost(self.all_cards[card_id].get('manaCost'))
            if mana_cost == cmc:
                cards_with_search_cmc.append(self.all_cards[card_id])
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

    @staticmethod
    def _process_mana_cost(mana_string) -> int:
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


if __name__ == '__main__':
    ce = CardEngine()
    ce._debug()
else:
    print('importing {}'.format(__name__))
    ml.log_event('importing {}'.format(__name__))
