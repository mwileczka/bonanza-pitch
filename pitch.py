#!/usr/bin/python3
import abc
import random
import pprint
from enum import Enum, unique, auto
from abc import ABC
import datetime

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
        return Deck(x)

    def sort(self):
        super().sort(key=lambda x: Deck.ordinal(x))

    @staticmethod
    def ordinal(card):
        try:
            return Deck.card_set.index(card)
        except ValueError:
            return -1

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

    def suit(self, suit):
        resp = Deck([])
        for card in self:
            if card and card[1] in suit:
                resp.append(card)
        return resp

    def suit_cnt(self, suit):
        cnt = 0
        for card in self:
            if card and card[1] in suit:
                cnt += 1
        return cnt

    def high(self, suit):
        highest = None
        for card in self:
            if not card or card[1] not in suit:
                continue
            if not highest or Deck.ordinal(card) > Deck.ordinal(highest):
                highest = card
        return highest

    def suit_cnts(self):
        cnts = {k: 0 for k in "SCDH"}
        for card in self:
            if not card:
                continue
            cnts[card[1]] += 1
        return cnts

    def suit_highest_cnt(self):
        cnts = self.suit_cnts()
        highest_cnt = 0
        highest_suit = None
        for suit, cnt in cnts.items():
            if cnt > highest_cnt:
                highest_cnt = cnt
                highest_suit = suit
        return highest_suit




class Team:
    def __init__(self):
        self.points = 0
        self.score = 0
        self.cards_won = Deck([])

    def get_json(self):
        return {
            'points': self.points,
            'score': self.score,
            'cards_won': list(self.cards_won)
        }


class Seat:
    def __init__(self, idx=None, id=None):
        self.hand = Deck([])
        self.played = None
        self.bid = -1
        self.idx = idx
        self.id = id
        self.kept = 0
        self.player = None
        self.playable = Deck([])

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
        WaitPlayers = 0
        WaitDeal = 1
        WaitBid = 2
        WaitSuit = 3
        WaitDiscard = 4
        WaitPlay = 5
        WaitHand = 6

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
        self.dealer = 0  # TODO change this to none and assign random on first deal
        self.lead = None
        self.seats = [Seat(idx=0), Seat(idx=1), Seat(idx=2), Seat(idx=3)]
        self.deck = Deck()
        self.state = Table.State.WaitPlayers
        self.id = id
        self.kitty = Deck([])
        self.turn = 0
        self.teams = [Team(), Team()]
        self.bidder = None
        self.winner = None
        self.wait_end = None

    def get_json(self):
        return {
            'trump': self.trump,
            'lead': self.lead,
            'seats': [
                self.seats[0].get_table_json(),
                self.seats[1].get_table_json(),
                self.seats[2].get_table_json(),
                self.seats[3].get_table_json()
            ],
            'teams': [
                self.teams[0].get_json(),
                self.teams[1].get_json()
            ],
            'deck_cnt': len(self.deck),
            'kitty_cnt': len(self.kitty),
            'turn': self.turn,
            'bidder': self.bidder,
            'winner': self.winner,
            'bid': self.seats[self.bidder].bid if self.bidder else None,
            'state': self.state.value
        }

    def check(self):
        if self.state == Table.State.WaitHand:
            if self.wait_end and datetime.datetime.now() <= self.wait_end:
                self.wait_end = None
                if len(self.turn_seat.hand) == 0:
                    # TODO end of hand or game
                    self.dealer = next_seat(self.dealer)
                    self.deal()
                else:
                    self.reset_for_trick()
                    self.update()
                    self.req_play()

    def reset_for_trick(self):
        for seat in self.seats:
            seat.played = None
        self.lead = None

    def reset_for_hand(self):
        self.turn = next_seat(self.dealer)
        self.kitty.clear()
        self.trump = None
        self.lead = None
        self.winner = None
        self.bidder = None
        for team in self.teams:
            team.points = 0
            team.cards_won.clear()
        for seat in self.seats:
            seat.reset_for_hand()

    def deal(self):
        self.reset_for_hand()

        self.deck.reset()
        self.deck.shuffle()

        for seat in self.seats:
            seat.hand.extend(self.deck.draw(6))
            seat.hand.sort()

        self.kitty.extend(self.deck.draw(4))

        self.update()

        self.req_bid()

    def req_bid(self):
        highest_bid = max([x.bid for x in self.seats])

        min_bid = max(highest_bid + 1, 1)
        max_bid = 19

        self.state = Table.State.WaitBid


        self.message(self.turn, 'Request Bid')
        self.seats[self.turn].player.req_bid(min_bid, max_bid)

    def message(self, seat_idx, s):
        fs = f'{self.seats[seat_idx].player.username}[{seat_idx}]: {s}'
        self.tx('status', fs)

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

        # TODO send req discard
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

    def ref_discard(self):
        # TODO
        pass

    def req_play(self):
        self.state = Table.State.WaitPlay
        if not self.lead:
            if len(self.turn_seat.hand) == 6:
                # first play of first trick
                playable = self.turn_seat.hand.suit(self.trump)
            else:
                # first play of other tricks
                playable = self.turn_seat.hand
        else:
            # not first play
            if self.turn_seat.hand.suit_cnt(self.lead):
                # have lead suit
                playable = self.turn_seat.hand.suit(self.lead)
            else:
                # don't have leave suit
                playable = self.turn_seat.hand

        self.turn_seat.playable = playable
        self.turn_seat.player.req_play(playable)

    @property
    def bids(self):
        return [x.bid for x in self.seats]

    @property
    def played(self):
        return [x.played for x in self.seats]

    @property
    def turn_seat(self):
        return self.seats[self.turn]

    def bid(self, seat_idx, bid):
        self.message(seat_idx, 'Bid {}'.format(bid))

        self.seats[seat_idx].bid = bid
        self.turn = next_seat(self.turn)

        win_bid = 0
        win_idx = -1
        bidding = 0
        for idx in range(0, 4):
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
            self.bidder = win_idx
            self.turn = win_idx
            self.req_suit()

    def req_suit(self):
        self.state = Table.State.WaitSuit
        self.seats[self.turn].player.req_suit()

    def discard(self, seat_idx, card):
        if seat_idx != self.turn:
            print('ERROR: received out of turn discard')
            return
        if card not in self.turn_seat.hand:
            print('ERROR: received undiscardable card')
            self.req_discard()
            return
        # TODO process discard

    def play_card(self, seat_idx, card):
        if seat_idx != self.turn:
            print('ERROR: received out of turn play')
            return
        if card not in self.turn_seat.playable or card not in self.turn_seat.hand:
            print('ERROR: received unplayable card')
            self.req_play()
            return
        self.turn_seat.played = card
        self.turn_seat.hand.remove(card)

        self.update(seat_idx=seat_idx)

        self.turn = next_seat(self.turn)

        if self.turn_seat.playable:
            # everyone has played a card

            trick = Deck(self.played)

            highest_trump = trick.high(self.trump)
            highest_lead = trick.high(self.lead)
            win_card = highest_trump if highest_trump else highest_lead
            self.winner = trick.index(win_card)

            self.teams[self.winner].cards_won.extend(trick)

            self.turn = self.winner

            self.wait_end = datetime.datetime.now() + datetime.timedelta(seconds=3.0)
            self.state = Table.State.WaitHand

            self.update()
        else:
            if not self.lead:
                self.lead = card[1]

            self.update()
            self.req_play()

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

    def req_play(self, playable):
        self.tx('req_play', list(playable))
