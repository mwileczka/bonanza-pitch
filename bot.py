#!/usr/bin/python3
import random
from time import sleep

import socketio
import requests
from pprint import pprint
from pitch import Deck
import names


def bot_client_proc(table, seat, username, url=None):
    bot = BotPlayerClient(table=table, seat=seat, username=username, url=url)
    bot.sio.wait()


def bot_client_username():
    return '@' + names.get_first_name()


class BotPlayerClient:
    def __init__(self, table, seat, username, url=None):
        if not url:
            url = 'http://localhost:5000'
        self.username = username
        self.table_name = table
        self.seat = seat
        self.sio = socketio.Client()
        self.url = url
        self.ns = '/table'
        self.table = None  # type: Dict
        self.hand = None  # type: Deck
        self.txq = []

        r = requests.post(self.url + '/table', {
            'username': self.username,
            'table': self.table_name,
            'seat': str(self.seat),
            'bot': "1"
        })
        self.cookie_session = r.cookies.get('session')
        print("Session Cookie", self.cookie_session)

        print("registering")
        self.sio.on('connect', self.on_connect, namespace=self.ns)
        self.sio.on('disconnect', self.on_disconnect, namespace=self.ns)
        self.sio.on('hand', self.on_hand, namespace=self.ns)
        self.sio.on('table', self.on_table, namespace=self.ns)
        self.sio.on('req_bid', self.on_req_bid, namespace=self.ns)
        self.sio.on('req_suit', self.on_req_suit, namespace=self.ns)
        self.sio.on('req_play', self.on_req_play, namespace=self.ns)
        self.sio.on('req_deal', self.on_req_deal, namespace=self.ns)
        self.sio.on('req_discard', self.on_req_discard, namespace=self.ns)
        self.sio.on('req_kitty', self.on_req_kitty, namespace=self.ns)
        self.sio.on('kick', self.on_kick, namespace=self.ns)

        print("connecting")
        self.sio.connect(self.url, namespaces=self.ns,
                         headers={'Cookie': 'session=' + self.cookie_session})

    def disconnect(self):
        self.sio.disconnect()

    def tx(self, event, args):
        if self.ns not in self.sio.namespaces:
            self.txq.append((event, args))
        else:
            self.sio.emit(event, args, namespace=self.ns)

    def on_connect(self):
        print('connection established')
        if self.ns in self.sio.namespaces:
            while len(self.txq):
                (e, a) = self.txq.pop()
                self.sio.emit(e, a, namespace=self.ns)

    def on_disconnect(self):
        print('disconnected from server...exiting')

    def on_table(self, args):
        self.table = args
        # pprint(args)

    def on_hand(self, args):
        self.hand = Deck(args['cards'])
        # pprint(args)

    def on_kick(self):
        self.sio.disconnect()

    def on_req_bid(self, args):
        bid = args.get('min', 1)

        bid_suit = self.hand.suit_highest_cnt()
        bit_suit_cnt = self.hand.suit_cnt(bid_suit)

        r = random.random()
        if bid < 7:
            if r > .75:
                bid = 0
        elif bid < 11:
            if bit_suit_cnt < 3 or r > .5:
                bid = 0
        else:
            if bit_suit_cnt < 4 or r > .5:
                bid = 0
        self.sio.sleep(1)
        self.tx('bid', bid)

    def on_req_suit(self, args):
        self.sio.sleep(1)
        self.tx('suit', self.hand.suit_highest_cnt())

    def on_req_play(self, args):
        playable = Deck(args)
        trump_cards = playable.suit(self.table['trump'])
        non_trump_cards = playable.suit(self.table['trump'], True)
        if len(non_trump_cards):
            non_trump_cards.shuffle()
            self.tx('play', non_trump_cards.pop())
        else:
            playable.shuffle()
            self.tx('play', playable.pop())

    def on_req_kitty(self, args):
        self.sio.sleep(1)
        self.tx('kitty', None)

    def on_req_discard(self, args):
        self.sio.sleep(0.5)
        self.tx('discard', self.hand[random.randint(0, len(self.hand) - 1)])

    def on_req_deal(self, args):
        self.sio.sleep(random.randint(0, 3))
        self.tx('deal', {})

    def is_in_use(self):
        return self.sio.connected
