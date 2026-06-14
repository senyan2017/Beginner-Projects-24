"""Automated tests for the Blackjack game.

Run with:  python3 -m unittest -v   (from the Blackjack directory)
       or:  python3 Blackjack/test_blackjack.py

These cover the bugs that were fixed:
  * the deck shrinks as cards are dealt and never hands out the same
    physical card twice (initial deal, hits and dealer draws all share
    ``deal_card``);
  * the dealer scores Aces and draws cards entirely on its own, never
    prompting the player for input;
  * settlement covers player bust, dealer bust, ties and ordinary wins/losses.
"""

import io
import unittest
from collections import Counter
from contextlib import redirect_stdout
from unittest import mock
import random

import Blackjack as bj


class DeckConsistencyTests(unittest.TestCase):
    def test_fresh_deck_has_52_cards(self):
        self.assertEqual(len(bj.build_deck()), 52)

    def test_deal_removes_one_card(self):
        deck = bj.build_deck()
        bj.deal_card(deck)
        self.assertEqual(len(deck), 51)

    def test_repeated_hits_shrink_the_deck_by_one_each_time(self):
        # Covers "连续多次 hit 之后牌堆数量变化".
        random.seed(123)
        deck = bj.build_deck()
        for expected_remaining in range(51, 41, -1):  # ten deals
            bj.deal_card(deck)
            self.assertEqual(len(deck), expected_remaining)

    def test_no_physical_card_is_dealt_twice(self):
        # Dealing out the whole deck must reproduce exactly the original
        # multiset: four of every rank, nothing duplicated or invented.
        random.seed(7)
        deck = bj.build_deck()
        dealt = [bj.deal_card(deck) for _ in range(52)]
        self.assertEqual(len(deck), 0)
        self.assertEqual(Counter(map(str, dealt)), Counter(map(str, bj.build_deck())))

    def test_dealing_from_empty_deck_raises(self):
        with self.assertRaises(ValueError):
            bj.deal_card([])


class HandValueTests(unittest.TestCase):
    def test_number_and_face_cards(self):
        self.assertEqual(bj.hand_value([10, 'K']), 20)
        self.assertEqual(bj.hand_value([2, 3, 'J']), 15)

    def test_ace_counts_as_eleven_when_safe(self):
        self.assertEqual(bj.hand_value(['A', 9]), 20)

    def test_ace_drops_to_one_to_avoid_bust(self):
        self.assertEqual(bj.hand_value(['A', 'K', 5]), 16)  # 11+10+5=26 -> 16

    def test_multiple_aces_are_reduced_independently(self):
        self.assertEqual(bj.hand_value(['A', 'A']), 12)        # 11+1
        self.assertEqual(bj.hand_value(['A', 'A', 'A']), 13)   # 11+1+1
        self.assertEqual(bj.hand_value(['A', 'A', 9]), 21)     # 11+1+9


class DealerTurnTests(unittest.TestCase):
    def test_dealer_never_prompts_even_with_an_ace(self):
        # If the dealer logic ever called input(), this patched input would
        # raise and fail the test. This is the core of the Ace bug fix.
        with mock.patch('builtins.input',
                        side_effect=AssertionError('dealer asked the player for input')):
            random.seed(3)
            deck = bj.build_deck()
            cards = ['A', 5]  # value 16 -> dealer must draw
            total = bj.dealer_play(deck, cards)
        self.assertGreaterEqual(total, bj.DEALER_STAND)

    def test_dealer_stands_on_seventeen_or_more(self):
        deck = bj.build_deck()
        cards = ['K', 7]  # already 17
        before = len(deck)
        total = bj.dealer_play(deck, cards)
        self.assertEqual(total, 17)
        self.assertEqual(len(deck), before)  # no card drawn


class SettlementTests(unittest.TestCase):
    def test_player_bust_loses(self):
        self.assertEqual(bj.settle(22, 18), 'dealer')

    def test_dealer_bust_player_wins(self):
        self.assertEqual(bj.settle(19, 25), 'player')

    def test_higher_total_wins(self):
        self.assertEqual(bj.settle(20, 18), 'player')
        self.assertEqual(bj.settle(17, 20), 'dealer')

    def test_equal_totals_tie(self):
        self.assertEqual(bj.settle(18, 18), 'tie')

    def test_player_bust_takes_priority_over_dealer_bust(self):
        self.assertEqual(bj.settle(23, 24), 'dealer')


class FullRoundTests(unittest.TestCase):
    @mock.patch.object(bj, 'prompt_ace_value', return_value=11)
    @mock.patch('builtins.input', side_effect=['stick'])
    def test_stick_round_completes_without_dealer_input(self, mock_input, _ace):
        # The player provides exactly one input ('stick'). If the dealer turn
        # asked for input, side_effect would be exhausted -> StopIteration.
        random.seed(2)
        out = io.StringIO()
        with redirect_stdout(out):
            bj.play_round()
        text = out.getvalue()
        self.assertIn("dealer's hand is", text)
        self.assertTrue(
            any(phrase in text for phrase in ('You win!', 'Dealer wins!', "It's a tie!")),
            'a final result should be announced',
        )

    @mock.patch.object(bj, 'prompt_ace_value', return_value=11)
    @mock.patch('builtins.input', side_effect=['hit', 'hit', 'hit', 'hit', 'hit', 'hit'])
    def test_player_can_bust_and_dealer_is_skipped(self, mock_input, _ace):
        # Force a deck where the player keeps drawing tens and busts.
        random.seed(0)
        with mock.patch.object(bj, 'build_deck', return_value=[10, 10, 10, 10, 10, 10, 10, 10]):
            out = io.StringIO()
            with redirect_stdout(out):
                bj.play_round()
        text = out.getvalue()
        self.assertIn('Bust!', text)
        self.assertIn('Dealer wins!', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
