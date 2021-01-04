from alive_progress import alive_bar
from card_utils import count_len_of_input_function_return
from card_utils import fetch_cache
from card_utils import filter_duplicate_cards_by_key
from card_utils import process_mana_cost
from card_utils import _card_contains_all_colors
from card_utils import _convert_list_of_strings_to_alphabetical_string
from card_utils import _get_sha256_local
from card_utils import _get_sha256_remote
from card_utils import _is_metadata_valid
from card_utils import _sanitize_colors
from decimal import getcontext
from minimalog.minimal_log import MinimalLog
getcontext().prec = 4
ml = MinimalLog()


class CardEngine:
    def __init__(self):
        self.cname = self.__class__.__name__
        ml.log_event('begin init {}'.format(self.cname))
        self.l_sha256, self.r_sha256 = _get_sha256_local(), _get_sha256_remote()
        self.data = fetch_cache()
        self.metadata_valid = _is_metadata_valid()
        self.all_cards = self._get_all_cards()
        self.all_unique_cards = filter_duplicate_cards_by_key(self.all_cards, 'name')
        ml.log_event('end init {}'.format(self.cname))

    def _get_all_cards(self) -> dict:
        ml.log_event('get all cards')
        card_dict, sorted_card_dict = dict(), dict()
        delimiter = '_'
        try:
            for set_key in self.data['data'].keys():
                for card in self.data['data'][set_key]['cards']:
                    card_dict[card['name'] + delimiter +
                              card['setCode'] + delimiter +
                              card['uuid']] = card
            for k, v in sorted(card_dict.items()):
                sorted_card_dict[k] = v
            return sorted_card_dict
        except RuntimeError:
            raise RuntimeError

    def _get_all_cards_with_colors(self, colors: str, search_pool=None) -> list:
        """
        :param colors: a color variation string, for example: 'BW' for 'black and white'
        :param search_pool: a user-specified list() of card object dict() through which to apply this search
        :return: a list() of card object dict()
        """
        ml.log_event('get all cards that have at least color variation {}'.format(colors))
        list_of_cards_with_colors = list()
        colors = _sanitize_colors(colors)
        if search_pool is None:
            ml.log_event('no search pool provided, starting')
            try:
                for card_id in self.all_cards:
                    card_color = \
                        _convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                    if _card_contains_all_colors(card_color, colors):
                        # ml.log_event('inclusive search color {} matches card color {}'.format(colors, card_color))
                        list_of_cards_with_colors.append(self.all_cards[card_id])
                return list_of_cards_with_colors
            except RuntimeError:
                raise RuntimeError
        ml.log_event('search pool provided, starting')
        try:
            for card_id in search_pool:
                card_color = \
                    _convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
                if _card_contains_all_colors(card_color, colors):
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
        colors = _sanitize_colors(colors)
        if search_pool is None:
            ml.log_event('no search pool provided, starting')
            try:
                for card_id in self.all_cards:
                    card_color = \
                        _convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
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
                    _convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id].get('colors'))
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
            mana_cost = process_mana_cost(self.all_cards[card_id].get('manaCost'))
            if mana_cost == cmc:
                cards_with_search_cmc.append(self.all_cards[card_id])
        return cards_with_search_cmc

    def _get_all_unique_color_variations(self) -> list:
        ml.log_event('get all unique color variations')
        unique_color_variations = list()
        try:
            for card_id in self.all_cards.keys():
                card_color_variation = \
                    _convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id]['colors'])
                if card_color_variation not in unique_color_variations:
                    unique_color_variations.append(card_color_variation)
            unique_color_variations.sort()
            return unique_color_variations
        except IndexError:
            raise IndexError

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
        try:
            for set_id in self.data['data'].keys():
                if id_to_convert == set_id:
                    return self.data['data'][set_id]['name']
        except RuntimeError:
            raise RuntimeError

    @staticmethod
    def _get_top_count_ranked_cards(count: int, search_pool=None) -> list:
        ml.log_event('searching for top {} ranked cards'.format(count))
        top_ranked_cards = list()
        ranks_found = list()
        try:
            for card_id in search_pool.keys():
                if 'edhrecRank' in search_pool[card_id].keys():
                    edhrec_rank = search_pool[card_id].get('edhrecRank')
                    if 0 < edhrec_rank < count + 1:
                        if edhrec_rank not in ranks_found:
                            ml.log_event('found card {} at rank {}'.format(search_pool[card_id]['name'], edhrec_rank))
                            ranks_found.append(edhrec_rank)
                            top_ranked_cards.append(search_pool[card_id])
                            continue
            return top_ranked_cards
        except RuntimeError:
            raise RuntimeError

    def debug(self) -> None:
        pass


if __name__ == '__main__':
    ce = CardEngine()
    ce.debug()
else:
    print('importing {}'.format(__name__))
    ml.log_event('importing {}'.format(__name__))
