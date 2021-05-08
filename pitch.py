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
    suits = 'CHSD'
    ranks = '23456789TJQKA'
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

    def draw(self, cnt=1, suit=None):
        if suit is None:
            if cnt > 0:
                x = Deck(self[-cnt:])
                del self[-cnt:]
            else:
                x = Deck(self[0:-cnt])
                del self[0:-cnt]
        else:
            x = self.suit(suit).draw(cnt)
            self.reduce(x)
            if len(x) < abs(cnt):
                if cnt > 0:
                    cnt -= len(x)
                else:
                    cnt += len(x)
                x.extend(self.draw(cnt))
        return x

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

    def suit(self, suit, inverse=False):
        resp = Deck([])
        for card in self:
            if not card:
                continue
            if card[1] in suit and not inverse:
                resp.append(card)
            elif card[1] not in suit and inverse:
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

    def low(self, suit):
        lowest = None
        for card in self:
            if not card or card[1] not in suit:
                continue
            if not lowest or Deck.ordinal(card) < Deck.ordinal(lowest):
                lowest = card
        return lowest

    def suit_cnts(self):
        cnts = {k: 0 for k in Deck.suits}
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

    def reduce(self, cards_to_remove):
        for card in cards_to_remove:
            self.remove(card)


class Team:
    def __init__(self):
        self.points = 0
        self.score = 0
        self.cards_won = Deck([])
        self.point_cards = Deck([])

    def get_json(self):
        return {
            'points': self.points,
            'score': self.score,
            'cards_won': list(self.cards_won)
        }

    def reset_for_hand(self):
        self.points = 0
        self.cards_won.clear()
        self.point_cards.clear()


class Seat:
    @unique
    class State(Enum):
        Disconnected = 0
        Ready = 1
        Waiting = 2

    def __init__(self, idx=None, id=None):
        self.hand = Deck([])
        self.played = None
        self.bid = -1
        self.idx = idx
        self.id = id
        self.kept = 0
        self.player = None
        self.playable = Deck([])
        self.state = Seat.State.Disconnected

    def get_table_json(self):
        return {
            'hand': len(self.hand),
            'played': self.played,
            'bid': self.bid,
            'kept': self.kept,
            'name': self.player.username if self.player else None,
            'state': self.state.value
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
    class Rules:
        def __init__(self, kitty_size=4, winning_score=64, hand_size=6, moon_cutoff=46, min_bid=1):
            self.kitty_size = kitty_size
            self.winning_score = winning_score
            self.hand_size = hand_size
            self.min_bid = min_bid
            self.moon_cutoff = moon_cutoff

    @unique
    class State(Enum):
        WaitPlayers = 0
        WaitDeal = 1
        WaitBid = 2
        WaitSuit = 3
        WaitDiscard = 4
        WaitPlay = 5
        WaitHand = 6

    @unique
    class TestMode(Enum):
        Discard = 1

    def get_lobby_json(self):
        return {
            'name': self.id,
            'seats': [x.player.username if x.player else None for x in self.seats]
        }

    def tx(self, event, args):
        for seat in self.seats:
            seat.tx(event, args)

    def __init__(self, id=None, rules=None):
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
        self.hand_cnt = 0
        self.hand_scores = []
        self.trump_high = None
        self.trump_low = None
        self.discarded = Deck([])
        self.win_team = None
        if rules is None:
            rules = Table.Rules()
        self.rules = rules
        self.test_mode = None

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
            'dealer': self.dealer,
            'winner': self.winner,
            'bid': self.seats[self.bidder].bid if self.bidder else None,
            'state': self.state.value,
            'hand_cnt': self.hand_cnt
        }

    def check(self):
        if self.state == Table.State.WaitHand:
            if self.wait_end and datetime.datetime.now() >= self.wait_end:
                self.wait_end = None

                bid_team = self.bidder % 2
                other_team = 0 if bid_team == 1 else 1

                if len(self.turn_seat.hand) > 0:
                    bid_team_trump = self.seats[bid_team].hand.suit_cnt(self.trump) + self.seats[
                        bid_team + 2].hand.suit_cnt(self.trump)
                    other_team_trump = self.seats[other_team].hand.suit_cnt(self.trump) + self.seats[
                        other_team + 2].hand.suit_cnt(self.trump)

                    if bid_team_trump and other_team_trump:
                        self.reset_for_trick()
                        self.update()
                        self.req_play()
                        return

                    for seat in self.seats:
                        self.teams[bid_team if bid_team_trump else other_team].cards_won.extend(seat.hand)
                        seat.hand.clear()
                    self.calc_points()
                    self.update()

                if self.bids[self.bidder] == 19:
                    if self.teams[bid_team].points == 18:
                        self.teams[bid_team].score = self.rules.winning_score
                    else:
                        self.teams[bid_team].score = 0
                        self.teams[other_team].score = self.rules.winning_score
                else:
                    if self.teams[bid_team].points >= self.bids[self.bidder]:
                        self.teams[bid_team].score += self.teams[bid_team].points
                    else:
                        self.teams[bid_team].score -= self.bids[self.bidder]

                    self.teams[other_team].score += self.teams[other_team].points

                self.hand_scores.append((self.teams[0].score, self.teams[1].score))

                self.update_score()

                # if both over 64, bidder wins
                self.win_team = None
                if self.teams[bid_team].score >= self.rules.winning_score:
                    # they won
                    self.win_team = bid_team
                elif self.teams[other_team].score >= self.rules.winning_score:
                    # they won
                    self.win_team = other_team

                if self.win_team is None:
                    # nobody won
                    self.hand_cnt += 1
                    self.dealer = next_seat(self.dealer)
                    self.req_deal()
                else:
                    self.dealer = next_seat(self.dealer)
                    if self.dealer % 2 != self.win_team:
                        self.dealer = next_seat(self.dealer)

                    self.req_deal()

    def update_score(self):
        self.tx('score', self.hand_scores)

    def re_request(self, seat_idx):
        if self.turn != seat_idx:
            return
        if self.state == Table.State.WaitPlayers:
            pass
        elif self.state == Table.State.WaitDeal:
            self.req_deal()
        elif self.state == Table.State.WaitBid:
            self.req_bid()
        elif self.state == Table.State.WaitSuit:
            self.req_suit()
        elif self.state == Table.State.WaitDiscard:
            self.req_discard()
        elif self.state == Table.State.WaitPlay:
            self.req_play()
        elif self.state == Table.State.WaitHand:
            pass

    def reset_for_trick(self):
        for seat in self.seats:
            seat.played = None
        self.lead = None
        self.winner = None

    def reset_for_hand(self):
        self.turn = next_seat(self.dealer)
        self.kitty.clear()
        self.discarded.clear()
        self.trump = None
        self.lead = None
        self.winner = None
        self.bidder = None
        for team in self.teams:
            team.reset_for_hand()
        for seat in self.seats:
            seat.reset_for_hand()
        self.trump_high = None
        self.trump_low = None
        self.test_mode = None

    def reset_for_game(self):
        # TODO - add anything else?
        self.hand_cnt = 0
        self.win_team = None
        self.hand_scores.clear()
        for team in self.teams:
            team.score = 0

    def kick(self, seat_idx=None):
        # TODO send something to client to redirect to lobby
        if seat_idx is None:
            for seat in self.seats:
                seat.tx('kick', None)
                seat.player = None
        else:
            self.seats[seat_idx].tx('kick', None)
            self.seats[seat_idx].player = None
        self.update()

    def deal(self, seat_idx, force=False, test_mode=None):
        self.seats[seat_idx].state = Seat.State.Ready

        if force:
            for seat in self.seats:
                seat.state = Seat.State.Ready

        self.update()

        if force or all([x.state == Seat.State.Ready for x in self.seats]):
            pass
        else:
            return

        if not all([x.player for x in self.seats]):
            return

        if self.teams[0].score >= self.rules.winning_score or self.teams[1].score >= self.rules.winning_score:
            self.reset_for_game()

        self.reset_for_hand()

        self.deck.reset()
        self.deck.shuffle()

        self.test_mode = test_mode

        if self.test_mode and self.test_mode == Table.TestMode.Discard.value:
            for seat in self.seats:
                seat.hand.extend(self.deck.draw(self.rules.hand_size, suit=Deck.suits[seat.idx]))
                seat.hand.sort()
        else:
            for seat in self.seats:
                seat.hand.extend(self.deck.draw(self.rules.hand_size))
                seat.hand.sort()

        self.kitty.extend(self.deck.draw(self.rules.kitty_size))

        self.update()

        self.req_bid()

    def req_bid(self):
        highest_bid = max([x.bid for x in self.seats])

        min_bid = max(highest_bid + 1, self.rules.min_bid)

        max_bid = 19
        for team in self.teams:
            if team.score < 0 or team.score >= self.rules.moon_cutoff:
                max_bid = 18

        self.state = Table.State.WaitBid

        self.message(self.turn, 'Request Bid')
        if self.turn_seat.player:
            self.turn_seat.player.req_bid(min_bid, max_bid)

    def message(self, seat_idx, s):
        pass
        # fs = f'{self.seats[seat_idx].player.username}[{seat_idx}]: {s}'
        # self.tx('status', fs)

    def end_hand(self):
        if self.dealer is None or self.dealer >= 3:
            self.dealer = 0
        else:
            self.dealer += 1

    def suit(self, s):
        self.trump = s

        for seat in self.seats:
            seat.hand.keep_suit(self.trump)
            seat.kept = len(seat.hand)

        self.turn_seat.hand.extend(self.kitty.suit(self.trump))

        self.turn_seat.hand.sort()

        self.update()

        self.req_discard()

    def req_discard(self):
        self.state = Table.State.WaitDiscard

        self.turn_seat.tx_hand()

        if self.turn_seat.player:
            self.turn_seat.player.req_discard(
                len(self.turn_seat.hand) - self.rules.hand_size if
                len(self.turn_seat.hand) > self.rules.hand_size else 0,
                list(self.kitty)
            )

    def req_deal(self):
        self.state = Table.State.WaitDeal

        for seat in self.seats:
            seat.state = Seat.State.Waiting

        self.tx('req_deal', {
            'scores': self.hand_scores,
            'game_winner': self.win_team,
            'points': [x.score for x in self.teams],
            'point_cards': [x.point_cards for x in self.teams],
            'hand_cnt': self.hand_cnt,
            'deck_trump': list(self.deck.suit(self.trump)) if self.state == Table.State.WaitDeal else []
        })

    def req_play(self):
        self.state = Table.State.WaitPlay
        if not self.lead:
            if len(self.turn_seat.hand) == self.rules.hand_size:
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
        if self.turn_seat.player:
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

    def dialog(self, msg, cards):
        self.tx('dialog', {
            'msg': msg,
            'cards': cards
        })

    def bid(self, seat_idx, bid):
        self.message(seat_idx, 'Bid {}'.format(bid))

        self.seats[seat_idx].bid = bid
        self.turn = next_seat(self.turn)

        win_bid = 0
        win_idx = -1
        yet_to_bid = 0
        bidding = 0
        passed = 0
        for idx in range(0, 4):
            b = self.seats[idx].bid
            if b < 0:
                # hasn't bid yet
                yet_to_bid += 1
            elif b == 0:
                # passed
                passed += 1
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
                yet_to_bid = 0
                passed = 3
                break

        print(f'bid bidding={bidding} passed={passed} yet={yet_to_bid}')

        if passed == 3 and yet_to_bid == 1:
            print("Dealer forced to bid")
            win_bid = 1
            win_idx = self.dealer
            self.seats[self.dealer].bid = 1
            yet_to_bid = 0
            bidding = 1

        if bidding + yet_to_bid > 1:
            # more than one still bidding
            print(f"There are {bidding} seats left bidding")
            while self.seats[self.turn].bid == 0:
                self.turn = next_seat(self.turn)

            self.update()
            self.req_bid()
        else:
            # there is a winning bid
            print(f'Seat {win_idx} won the bid for {win_bid}')
            for idx in range(0, 4):
                if idx == win_idx:
                    continue
                self.seats[idx].bid = None

            self.bidder = win_idx
            self.turn = win_idx
            self.update()
            self.req_suit()

    def req_suit(self):
        self.state = Table.State.WaitSuit
        if self.turn_seat.player:
            self.turn_seat.player.req_suit()

    def discard(self, seat_idx, card):
        if seat_idx != self.turn:
            print('ERROR: received out of turn discard')
            return
        if card:
            if card not in self.turn_seat.hand:
                print('ERROR: received undiscardable card')
                self.req_discard()
                return
            self.discarded.append(card)
            self.turn_seat.hand.remove(card)

        if len(self.turn_seat.hand) > self.rules.hand_size:
            self.req_discard()
            return

        self.kitty.clear()

        for seat in self.seats:
            if len(seat.hand) < self.rules.hand_size:
                seat.hand.extend(self.deck.draw(self.rules.hand_size - len(seat.hand)))
            seat.hand.sort()
            seat.played = None

        self.update()

        if len(self.discarded) > 0:
            self.dialog(
                f"{self.turn_seat.player.username if self.turn_seat.player else 'Bidder'} discarded trump",
                list(self.discarded)
            )

        self.req_play()

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

        if self.turn_seat.played:
            # everyone has played a card

            trick = Deck(self.played)

            highest_trump = trick.high(self.trump)
            highest_lead = trick.high(self.lead)
            win_card = highest_trump if highest_trump else highest_lead
            self.winner = trick.index(win_card)

            self.teams[self.winner % 2].cards_won.extend(trick)

            self.turn = self.winner

            self.wait_end = datetime.datetime.now() + datetime.timedelta(seconds=2.0)
            self.state = Table.State.WaitHand

            self.calc_points()

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

    def calc_points(self):
        trump_out = Deck([])
        for team in self.teams:
            team.points = 0
            team.point_cards.clear()
            trump_out.extend(team.cards_won.suit(self.trump))
            for (rank, val) in (('9', 9), ('5', 5), ('T', 1), ('J', 1)):
                card = rank + self.trump
                if card in team.cards_won:
                    team.points += val
                    team.point_cards.append(card)
        trump_out.sort()
        self.trump_low = trump_out[0]
        self.trump_high = trump_out[-1]

        for card in (self.trump_low, self.trump_high):
            for team in self.teams:
                if card in team.cards_won:
                    team.points += 1
                    team.point_cards.append(card)


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

    def req_discard(self, cnt, kitty):
        self.tx('req_discard', {
            'cnt': cnt,
            'kitty': kitty
        })
