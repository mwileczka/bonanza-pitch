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
        if cnt > 0:
            x = self[-cnt:]
            del self[-cnt:]
        else:
            x = self[0:-cnt]
            del self[0:-cnt]
        return x

    def sort(self):
        super().sort(key=lambda x: Deck.ordinal(x))

    @staticmethod
    def ordinal(card):
        return Deck.card_set.index(card)

    def keep_suit(self, suit):
        idx = 0
        discarded = Deck([])
        while idx < len(self):
            if self[idx][1] == suit:
                # is suit
                idx += 1
            else:
                # not suit
                discarded.append(self.pop(idx))
        return discarded


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

    def reset_for_hand(self):
        self.played = None
        self.hand.clear()
        self.bid = -1
        self.kept = -1


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

    def reset_for_hand(self):
        self.turn = -1
        self.kitty.clear()
        self.trump = None
        self.lead = None
        self.points[0] = 0
        self.points[1] = 0
        for seat in self.seats:
            seat.reset_for_hand()

    def deal(self):
        self.reset_for_hand()

        self.deck.reset()
        self.deck.shuffle()

        self.kitty.clear()

        for seat in self.seats:
            seat.hand.extend(self.deck.draw(6))
            seat.hand.sort()

        self.kitty.extend(self.deck.draw(4))

        self.turn = next_seat(self.dealer)

        self.update()

        self.req_bid()

    def req_bid(self):
        highest_bid = max([ x.bid for x in self.seats])

        min_bid = max(highest_bid + 1, 1)
        max_bid = 19

        self.state = Table.State.WaitBid

        self.seats[self.turn].player.req_bid(min_bid, max_bid)


    def end_hand(self):
        if self.dealer is None or self.dealer >= 3:
            self.dealer = 0
        else:
            self.dealer += 1

    def suit(self, s):
        self.trump = s

        self.seats[self.turn].hand.extend(self.kitty)
        self.kitty.clear()

        for seat in self.seats:
            seat.hand.keep_suit(self.trump)
            seat.kept = len(seat.hand)

        discard = self.seats[self.turn].kept - 6
        if discard > 0:
            self.seats[self.turn].hand.sort()
            self.seats[self.turn].hand.draw(-discard)
            # TODO notify trump was discarded

        for seat in self.seats:
            draw = 6 - len(seat.hand)
            seat.hand.extend(self.deck.draw(draw))
            seat.hand.sort()
            seat.played = None

        self.update()

        self.req_play()

    def req_play(self):
        self.state = Table.State.WaitPlay
        self.seats[self.turn].player.req_play()

    @property
    def bids(self):
        return [x.bid for x in self.seats]

    @property
    def turn_seat(self):
        return self.seats[self.turn]

    def bid(self, seat_idx, bid):
        self.seats[seat_idx].bid = bid
        self.turn = next_seat(self.turn)

        win_bid = 0
        win_idx = -1
        bidding = 0
        for idx in range(0,4):
            b = self.seats[idx].bid
            if b < 0:
                # hasn't bid yet
                bidding += 1
            elif b == 0:
                # passed
                pass
            elif b <= 18:
                # still bidding
                bidding += 1
                if b > win_bid:
                    win_bid = b
                    win_idx = idx
            else:
                # moon
                win_bid = b
                win_idx = idx
                bidding = 1
                break

        if bidding > 1:
            # more than one still bidding
            print(f"There are {bidding} seats left bidding")
            while self.seats[self.turn].bid == 0:
                self.turn = next_seat(self.turn)

            self.req_bid()
        else:
            # there is a winning bid
            print(f'Seat {win_idx} won the bid for {win_bid}')
            self.turn = win_idx
            self.req_suit()

    def req_suit(self):
        self.state = Table.State.WaitSuit
        self.seats[self.turn].player.req_suit()

    def discard(self):
        pass

    def play_card(self, seat_idx, card):
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

    def req_bid(self, min, max):
        self.tx('req_bid', {
            'min': min,
            'max': max
        })

    def req_suit(self):
        self.tx('req_suit', {})

    def req_play(self):
        self.tx('req_play', {

        })
