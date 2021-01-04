from alive_progress import alive_bar
from card_utils import card_pool_is_dict
from card_utils import fetch_cache
from card_utils import filter_duplicate_cards_by_key
from card_utils import process_mana_cost
from card_utils import _card_contains_all_colors
from card_utils import _convert_list_of_strings_to_alphabetical_string
from card_utils import _get_sha256_local
from card_utils import _get_sha256_remote
from card_utils import _is_metadata_valid
from card_utils import _sanitize_colors
from card_utils import _timer_action
from minimalog.minimal_log import MinimalLog
ml = MinimalLog()


class CardEngine:
    def __init__(self, get_card_data=False,
                 get_unique_card_data=False,
                 debug=False):
        self.cname = self.__class__.__name__
        ml.log_event('begin init {}'.format(self.cname))
        self.data = fetch_cache()
        self.l_sha256, self.r_sha256 = _get_sha256_local(), _get_sha256_remote()
        self.metadata_valid = _is_metadata_valid()
        if get_card_data:
            self.all_cards = self._get_all_cards()
            if get_unique_card_data:
                self.all_unique_cards = filter_duplicate_cards_by_key(self.all_cards, 'name')
        ml.log_event('end init {}'.format(self.cname))
        if debug:
            self._debug()

    def get_all_cards_in_set(self, card_pool=None, set_name='Tempest') -> dict:
        """
        :param card_pool: custom dictionary created from online json object
        :param set_name: a set name from magic the gathering
        :return:
        """
        ml.log_event('get all cards belonging to set {}'.format(set_name))
        cards_in_set = dict()
        set_id = self._get_id_from_set_name(set_name)
        if card_pool is None:
            ml.log_event('no card pool provided, using all cards')
            card_pool = self.all_cards
        else:
            ml.log_event('card pool provided, starting with object of type {}'. format(type(card_pool)))
        try:
            if not card_pool_is_dict(card_pool):
                raise TypeError
            for card_id in card_pool:
                if set_id in card_id:
                    # TODO bug, false positive returns if card name contains set_id anywhere
                    ml.log_event('{} found for set_name {}'.format(card_id, set_name))
                    cards_in_set[card_id] = card_pool[card_id]
            return cards_in_set
        except RuntimeError:
            raise RuntimeError

    def get_all_cards_with_colors(self, card_pool=None, colors='BW') -> dict:
        """
        :param card_pool: custom dictionary created from online json object
        :param colors: a combination of colors from magic the gathering
        :return:
        """
        ml.log_event('get all cards that have at least color variation {}'.format(colors))
        cards_with_colors = dict()
        colors = _sanitize_colors(colors)
        if card_pool is None:
            ml.log_event('no card pool provided, using all cards')
            card_pool = self.all_cards
        else:
            ml.log_event('card pool provided, starting with object of type {}'.format(type(card_pool)))
        try:
            if not card_pool_is_dict(card_pool):
                raise TypeError
            for card_id in card_pool:
                card_color = \
                    _convert_list_of_strings_to_alphabetical_string(card_pool[card_id].get('colors'))
                if _card_contains_all_colors(card_color, colors):
                    ml.log_event('card id {} found with colors {}'.format(card_id, colors))
                    cards_with_colors[card_id] = card_pool[card_id]
            return cards_with_colors
        except RuntimeError:
            raise RuntimeError

    def get_all_cards_with_converted_mana_cost(self, card_pool=None, cmc=0) -> dict:
        """
        :param card_pool: custom dictionary created from online json object
        :param cmc: a 'total mana cost' from magic the gathering
        :return:
        """
        ml.log_event('getting all cards with cmc {}'.format(cmc))
        cards_with_cmc = dict()
        if card_pool is None:
            ml.log_event('no card pool provided, using all cards')
            card_pool = self.all_cards
        else:
            ml.log_event('card pool provided, starting with object of type {}'.format(type(card_pool)))
        try:
            if not card_pool_is_dict(card_pool):
                raise TypeError
            for card_id in card_pool.keys():
                mana_cost = process_mana_cost(card_pool[card_id].get('manaCost'))
                if mana_cost == cmc:
                    ml.log_event('card {} found with cmc {}'.format(card_id, cmc))
                    cards_with_cmc[card_id] = card_pool[card_id]
            return cards_with_cmc
        except RuntimeError:
            raise RuntimeError

    def get_all_cards_with_exact_colors(self, card_pool=None, colors='BW') -> dict:
        """
        :param card_pool: custom dictionary created from online json object
        :param colors: a combination of colors from magic the gathering
        :return:
        """
        ml.log_event('get all cards belonging to color variation {}'.format(colors))
        cards_matching_color = dict()
        colors = _sanitize_colors(colors)
        if card_pool is None:
            ml.log_event('no card pool provided, using all cards')
            card_pool = self.all_cards
        else:
            ml.log_event('card pool provided, starting with object of type {}'.format(type(card_pool)))
        try:
            if not card_pool_is_dict(card_pool):
                raise TypeError
            for card_id in card_pool:
                card_color = \
                    _convert_list_of_strings_to_alphabetical_string(card_pool[card_id].get('colors'))
                if colors == card_color:
                    ml.log_event('card {} found with exact color(s) {}'.format(card_id, colors))
                    cards_matching_color[card_id] = card_pool[card_id]
            return cards_matching_color
        except RuntimeError:
            raise RuntimeError

    def get_top_count_ranked_cards(self, card_pool=None, count=500) -> dict:
        """
        :param card_pool: custom dictionary created from online json object
        :param count: the number of cards to fetch, each number corresponding to rank
        :return:
        """
        ml.log_event('searching for top {} ranked cards'.format(count))
        top_ranked_cards = dict()
        ranks_found = list()
        if card_pool is None:
            ml.log_event('no card pool provided, using all cards')
            card_pool = self.all_cards
        else:
            ml.log_event('card pool provided, starting with object of type {}'.format(type(card_pool)))
        try:
            if not card_pool_is_dict(card_pool):
                raise TypeError
            for card_id in card_pool.keys():
                if 'edhrecRank' in card_pool[card_id].keys():
                    edhrec_rank = card_pool[card_id].get('edhrecRank')
                    if 0 < edhrec_rank < count + 1:
                        if edhrec_rank not in ranks_found:
                            ml.log_event('card id {} found at rank {}'.format(card_id, edhrec_rank))
                            ranks_found.append(edhrec_rank)
                            top_ranked_cards[card_id] = card_pool[card_id]
                            continue
            return top_ranked_cards
        except RuntimeError:
            raise RuntimeError

    def _get_all_cards(self, sort_dict_before_return=False) -> dict:
        """
        :return:
        """
        ml.log_event('get all cards')
        card_dict, sorted_card_dict = dict(), dict()
        delimiter = '_'
        try:
            for set_key in self.data['data'].keys():
                for card in self.data['data'][set_key]['cards']:
                    card_dict[card['name'] + delimiter +
                              card['setCode'] + delimiter +
                              card['uuid']] = card
            if sort_dict_before_return:
                for k, v in sorted(card_dict.items()):
                    card_dict[k] = v
            return card_dict
        except RuntimeError:
            raise RuntimeError

    def _get_all_possible_color_combinations(self, sort_variations_before_return=False) -> list:
        """
        :return: all color combinations in magic the gathering associated with at least one card
        """
        ml.log_event('get all unique color variations')
        unique_color_variations = list()
        try:
            for card_id in self.all_cards.keys():
                card_color_variation = \
                    _convert_list_of_strings_to_alphabetical_string(self.all_cards[card_id]['colors'])
                if card_color_variation not in unique_color_variations:
                    unique_color_variations.append(card_color_variation)
                    ml.log_event('new color variation {} found on card_id {}'.format(card_color_variation, card_id))
            if sort_variations_before_return:
                unique_color_variations.sort()
            return unique_color_variations
        except IndexError:
            raise IndexError

    def _get_id_from_set_name(self, set_name_to_convert: str) -> str:
        """
        :param set_name_to_convert: a set name from magic the gathering
        :return:
        """
        ml.log_event('get id for set name {}'.format(set_name_to_convert))
        try:
            for set_id in self.data['data'].keys():
                set_name_for_id = self.data['data'][set_id].get('mcmName')
                if set_name_to_convert == set_name_for_id:
                    ml.log_event('set_id {} found for {}'.format(set_id, set_name_to_convert))
                    return set_id
            set_id = ''
            ml.log_event('no set_id found for {}'.format(set_name_to_convert), level=ml.WARN)
            return set_id
        except IndexError:
            raise IndexError

    def _get_list_of_set_ids(self) -> list:
        """
        :return: a list of all set ids present in the json file, a set id corresponds to a set name
        """
        ml.log_event('get list of set ids')
        list_of_set_ids = list()
        try:
            for set_id in self.data['data'].keys():
                ml.log_event('fetched set_id {} from cache'.format(set_id))
                list_of_set_ids.append(set_id)
            ml.log_event('returning list {} of set_ids'.format(list_of_set_ids))
            return list_of_set_ids
        except RuntimeError:
            raise RuntimeError

    def _get_set_name_from_id(self, id_to_convert: str) -> str:
        """
        :param id_to_convert: a set id, great parameter for starting a search in the present json format
        :return:
        """
        ml.log_event('get set name from id {}'.format(id_to_convert))
        try:
            for set_id in self.data['data'].keys():
                if id_to_convert == set_id:
                    set_name = self.data['data'][set_id]['name']
                    ml.log_event('set name {} found for set_id {}'.format(set_name, id_to_convert))
                    return set_name
            ml.log_event('no set name found for set_id {}'.format(id_to_convert))
            set_name = ''
            return set_name
        except RuntimeError:
            raise RuntimeError

    def _debug(self) -> None:
        start_time = _timer_action(start_timer=True)
        ml.log_event('start {} debug routine'.format(self.cname))
        cards_in_set_tempest = self.get_all_cards_in_set()
        cards_with_cmc_zero = self.get_all_cards_with_converted_mana_cost()
        cards_with_exactly_bw = self.get_all_cards_with_exact_colors()
        cards_with_at_least_bw = self.get_all_cards_with_colors()
        top_500_cards = self.get_top_count_ranked_cards()
        ml.log_event('end {} debug routine'.format(self.cname))
        elapsed_time = _timer_action(start_timer=False, time_start=start_time)
        ml.log_event('seconds for {} debug routine : to run {}'.format(self.cname, elapsed_time))


if __name__ == '__main__':
    ce = CardEngine(get_card_data=True,
                    get_unique_card_data=True,
                    debug=True)
    pass
else:
    print('importing {}'.format(__name__))
    ml.log_event('importing {}'.format(__name__))
