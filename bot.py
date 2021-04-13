#!/usr/bin/python3
import random
from time import sleep

import socketio
import requests
from pprint import pprint
from pitch import Deck

bot_client_inc = 1


def bot_client_proc(table, seat, username, url=None):
    bot = BotPlayerClient(table=table, seat=seat, username=username, url=url)
    bot.sio.wait()


def bot_client_username():
    global bot_client_inc
    username = f"Bot{bot_client_inc}"
    bot_client_inc += 1
    return username


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

        print("connecting")
        self.sio.connect(self.url, namespaces=self.ns,
                         headers={'Cookie': 'session=' + self.cookie_session})

    def disconnect(self):
        self.sio.disconnect()

    def tx(self, event, args):
        self.sio.emit(event, args, namespace=self.ns)

    def on_connect(self):
        print('connection established')

    def on_disconnect(self):
        print('disconnected from server')

    def on_table(self, args):
        self.table = args
        pprint(args)

    def on_hand(self, args):
        self.hand = Deck(args['cards'])
        pprint(args)

    def on_req_bid(self, args):
        bid = args.get('min', 1)
        r = random.random()
        if bid < 7:
            if r > .80:
                bid = 0
        elif bid < 11:
            if r > .40:
                bid = 0
        elif r > .20:
            bid = 0
        self.tx('bid', bid)

    def on_req_suit(self, args):
        self.tx('suit', self.hand.suit_highest_cnt())

    def on_req_play(self, args):
        self.tx('play', args[random.randint(0, len(args) - 1)])

    def on_req_discard(self, args):
        self.tx('discard', self.hand[random.randint(0, len(self.hand) - 1)])

    def on_req_deal(self, args):
        # TODO
        pass
