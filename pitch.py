#!/usr/bin/python3
import random
import pprint
from enum import Enum, unique, auto


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

    def get_table_json(self):
        return {
            'hand': len(self.hand),
            'played': self.played,
            'bid': self.bid,
            'kept': self.kept
        }

    def get_hand_json(self):
        return {
            'cards': list(self.hand)
        }


class Table:
    @unique
    class State(Enum):
        WaitBid = auto()
        WaitSuit = auto()
        WaitDiscard = auto()
        WaitPlay = auto()
        WaitTrick = auto()
        WaitDeal = auto()

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

        # TODO send req_bid

        print('req_bid', {
            'min': 1
        })

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

    def play_card(self):
        pass

    def get_seat(self, uid):
        for seat in self.seats:
            if seat.id == uid:
                return seat
        return None


if __name__ == '__main__':

    t = Table()
    t.deal()
    pprint.pprint(t.get_json())
    pprint.pprint(t.seats[0].get_hand_json())
