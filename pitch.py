#!/usr/bin/python3
import abc
import random
import pprint
from enum import Enum, unique, auto

from abc import ABC


class Deck(list):
    card_set = [f'{x}{y}' for y in 'CHSD' for x in '23456789TJQKA']

    def __init__(self, cards=None):
        if cards is None:
            self.reset()
        else:
            self.extend(cards)

    def reset(self):
        self.clear()
        self.extend(Deck.card_set)
        self.shuffle()

    def shuffle(self):
        random.shuffle(self)

    def draw(self, cnt=1):
        x = self[-cnt:]
        del self[-cnt:]
        return x

    def sort(self):
        super().sort(key=lambda x: Deck.ordinal(x))

    @staticmethod
    def ordinal(card):
        return Deck.card_set.index(card)


class Seat:
    def __init__(self, idx=None, id=None):
        self.hand = Deck([])
        self.played = None
        self.bid = 0
        self.idx = idx
        self.id = id
        self.kept = 0
        self.player = None

    def get_table_json(self):
        return {
            'hand': len(self.hand),
            'played': self.played,
            'bid': self.bid,
            'kept': self.kept,
            'name': self.player.username if self.player else None
        }

    def get_hand_json(self):
        return {
            'cards': list(self.hand)
        }

    def tx(self, event, args):
        if self.player:
            self.player.tx(event, args)

    def tx_hand(self):
        self.tx('hand', self.get_hand_json())


class Table:
    @unique
    class State(Enum):
        WaitBid = auto()
        WaitSuit = auto()
        WaitDiscard = auto()
        WaitPlay = auto()
        WaitTrick = auto()
        WaitDeal = auto()

    def tx(self, event, args):
        for seat in self.seats:
            seat.tx(event, args)

    def __init__(self, id=None):
        self.trump = None
        self.dealer = 0
        self.lead = None
        self.seats = [Seat(idx=0), Seat(idx=1), Seat(idx=2), Seat(idx=3)]
        self.points = [0, 0]
        self.score = [0, 0]
        self.deck = Deck()
        self.state = Table.State.WaitDeal
        self.id = id
        self.kitty = Deck([])

    def get_json(self):
        return {
            'trump': self.trump,
            'seats': [
                self.seats[0].get_table_json(),
                self.seats[1].get_table_json(),
                self.seats[2].get_table_json(),
                self.seats[3].get_table_json()
            ],
            'score': self.score,
            'points': self.points,
            'deck_cnt': len(self.deck),
            'kitty_cnt': len(self.kitty)
        }

    def add_bots(self):
        for seat in self.seats:
            if not seat.player:
                seat.player = BotPlayer()
        self.update()

    def deal(self):
        self.deck.reset()
        self.deck.shuffle()

        self.kitty.clear()

        for seat in self.seats:
            seat.hand.clear()
            seat.hand.extend(self.deck.draw(6))
            seat.hand.sort()

        self.kitty.extend(self.deck.draw(4))
        self.kitty.sort()

        self.points[0] = 0
        self.points[1] = 0
        self.trump = None

        self.update()
        # self.send('req_bid', {'min': 1})

        self.state = Table.State.WaitBid

    def end_hand(self):
        if self.dealer is None or self.dealer >= 3:
            self.dealer = 0
        else:
            self.dealer += 1

    def suit(self):
        pass

    def bid(self, data):
        pass

    def discard(self):
        pass

    def play_card(self, seat, card):
        pass

    def get_seat(self, uid):
        for seat in self.seats:
            if seat.id == uid:
                return seat
        return None

    def update(self, seat_idx=None):
        self.tx('table', self.get_json())
        if seat_idx:
            # send hand to that seat
            self.seats[seat_idx].tx_hand()
        else:
            # send hands to all seats
            for seat in self.seats:
                seat.tx_hand()


class Player(ABC):
    def __init__(self):
        self.username = None

    @abc.abstractmethod
    def tx(self, event, args):
        pass


class BotPlayer(Player):
    inc = 1

    def __init__(self, username=None):
        if not username:
            username = f"Bot{BotPlayer.inc}"
            BotPlayer.inc += 1
        self.username = username

    def tx(self, event, args):
        pass


if __name__ == '__main__':
    t = Table()
    t.deal()
    pprint.pprint(t.get_json())
    pprint.pprint(t.seats[0].get_hand_json())
