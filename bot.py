#!/usr/bin/python3
import random
from time import sleep

import socketio
import requests
from pprint import pprint


class BotPlayerClient:
    inc = 1

    def __init__(self, table, seat, username=None, url='http://localhost:5000/table'):
        if not username:
            username = f"Bot{BotPlayerClient.inc}"
            BotPlayerClient.inc += 1
        self.username = username
        self.table_name = table
        self.seat = seat
        self.sio = socketio.Client()
        self.url = url
        self.ns = '/table'
        self.table = None
        self.hand = None

        r = requests.post(self.url, {
            'username': self.username,
            'table': self.table_name,
            'seat': str(self.seat)
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

        print("connecting")
        self.sio.connect('http://localhost:5000', namespaces=self.ns, headers={'Cookie': 'session=' + self.cookie_session})


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
        self.hand = args
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
        self.tx('suit', 'H')

    def on_req_play(self, args):
        pass


if __name__ == '__main__':
    bot = BotPlayerClient('Matrix',2)
    sleep(5)
    bot.disconnect()
