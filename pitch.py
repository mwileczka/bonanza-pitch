#!/usr/bin/python3
import abc
import random
import pprint
from enum import Enum, unique, auto
from abc import ABC

def next_seat(idx):
    return 0 if idx >= 3 else idx + 1

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
        self.bid = -1
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

    def get_lobby_json(self):
        return {
            'name': self.id,
            'seats': [x.player.username if x.player else None for x in self.seats]
        }

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
        self.turn = 0

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
            'kitty_cnt': len(self.kitty),
            'turn': self.turn
        }

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

        self.turn = next_seat(self.dealer)

        self.update()

        self.req_bid()

    def req_bid(self):
        highest_bid = max([ x.bid for x in self.seats])

        min_bid = max(highest_bid + 1, 1)

        self.state = Table.State.WaitBid

        self.seats[self.turn].player.req_bid(min_bid)


    def end_hand(self):
        if self.dealer is None or self.dealer >= 3:
            self.dealer = 0
        else:
            self.dealer += 1

    def suit(self):
        pass

    def bid(self, seat_idx, bid):
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

    def req_bid(self, min):
        self.tx('req_bid', {'min': min})


class OldBotPlayer(Player):
    inc = 1

    def __init__(self, table, seat_idx, username=None):
        if not username:
            username = f"Bot{BotPlayer.inc}"
            BotPlayer.inc += 1
        self.username = username
        self.table = table
        self.seat_idx = seat_idx


    def rx(self, event, args):
        # if event == 'req_bid':
        #     bid = args['min']
        #     if bid < 7:
        #         bid = random.random() < .70
        #     elif bid < 11:
        #         bid = random.random() < .30
        #     else:
        #         bid = random.random() < .10
        #
        #     if bid:
        #         t.bid(self.seat_idx, args['min'])
        #     else:
        #         t.bid(self.seat_idx, 0)

        pass

    def tx(self, event, args):
        pass
