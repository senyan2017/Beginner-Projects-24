"""Unit tests for the Blackjack game.

Run with:  python3 -m unittest discover Blackjack
       or:  python3 Blackjack/test_blackjack.py
"""

import io
import random
import unittest
from contextlib import redirect_stdout
from unittest import mock

import Blackjack as bj


class RuleTests(unittest.TestCase):
    """The pure, I/O-free rule helpers."""

    def test_build_deck_has_52_cards_four_per_rank(self):
        deck = bj.build_deck()
        self.assertEqual(len(deck), 52)
        for rank in bj.RANKS:
            self.assertEqual(deck.count(rank), 4, rank)

    def test_card_value_number_cards(self):
        for n in range(2, 11):
            self.assertEqual(bj.card_value(n), n)

    def test_card_value_face_cards(self):
        for face in ('J', 'Q', 'K'):
            self.assertEqual(bj.card_value(face), 10)

    def test_card_value_ace_default_and_choices(self):
        self.assertEqual(bj.card_value('A'), 11)          # default is the high value
        self.assertEqual(bj.card_value('A', bj.ACE_LOW), 1)
        self.assertEqual(bj.card_value('A', bj.ACE_HIGH), 11)

    def test_is_bust_boundary(self):
        self.assertFalse(bj.is_bust(21))
        self.assertTrue(bj.is_bust(22))
        self.assertFalse(bj.is_bust(0))

    def test_dealer_should_hit(self):
        self.assertTrue(bj.dealer_should_hit(14))
        self.assertFalse(bj.dealer_should_hit(15))
        self.assertFalse(bj.dealer_should_hit(21))
        # threshold is configurable
        self.assertTrue(bj.dealer_should_hit(16, threshold=17))

    def test_decide_winner_normal(self):
        self.assertEqual(bj.decide_winner(20, 18), bj.WINNER_PLAYER)
        self.assertEqual(bj.decide_winner(18, 20), bj.WINNER_DEALER)

    def test_decide_winner_ties_go_to_dealer(self):
        self.assertEqual(bj.decide_winner(19, 19), bj.WINNER_DEALER)

    def test_decide_winner_busts(self):
        self.assertEqual(bj.decide_winner(22, 18), bj.WINNER_DEALER)   # player bust loses
        self.assertEqual(bj.decide_winner(18, 25), bj.WINNER_PLAYER)   # dealer bust loses
        self.assertEqual(bj.decide_winner(30, 30), bj.WINNER_DEALER)   # both bust -> player loses


class HandTests(unittest.TestCase):

    def test_add_accumulates_total_and_cards(self):
        hand = bj.Hand()
        hand.add('K', 10)
        hand.add(5, 5)
        self.assertEqual(hand.cards, ['K', 5])
        self.assertEqual(hand.total, 15)
        self.assertFalse(hand.is_bust())

    def test_is_bust(self):
        hand = bj.Hand()
        hand.add('K', 10)
        hand.add('Q', 10)
        hand.add(5, 5)
        self.assertTrue(hand.is_bust())

    def test_describe(self):
        hand = bj.Hand()
        hand.add('A', 11)
        hand.add(10, 10)
        self.assertEqual(hand.describe(), 'A, 10')


class DrawTests(unittest.TestCase):

    def test_draw_card_returns_card_from_deck(self):
        deck = bj.build_deck()
        rng = random.Random(0)
        for _ in range(100):
            self.assertIn(bj.draw_card(deck, rng), deck)


class RoundSmokeTests(unittest.TestCase):
    """End-to-end checks that a full round runs and returns a valid winner,
    without any manual input (prompts are patched, RNG is seeded)."""

    def _run_round(self):
        random.seed(0)
        buf = io.StringIO()
        with redirect_stdout(buf):
            winner = bj.play_round()
        return winner, buf.getvalue()

    @mock.patch.object(bj, 'prompt_ace_value', return_value=bj.ACE_HIGH)
    @mock.patch.object(bj, 'prompt_hit_or_stick', return_value='stick')
    def test_round_with_stick_completes(self, _hit, _ace):
        winner, output = self._run_round()
        self.assertIn(winner, (bj.WINNER_PLAYER, bj.WINNER_DEALER))
        self.assertIn('--- New round ---', output)
        self.assertIn("--- Dealer's turn ---", output)

    @mock.patch.object(bj, 'prompt_ace_value', return_value=bj.ACE_HIGH)
    @mock.patch.object(bj, 'prompt_hit_or_stick', side_effect=['hit', 'stick'] * 5)
    def test_round_with_hit_then_stick_completes(self, _hit, _ace):
        winner, _output = self._run_round()
        self.assertIn(winner, (bj.WINNER_PLAYER, bj.WINNER_DEALER))

    def test_player_never_exceeds_card_cap(self):
        # Always hit: the player must stop at MAX_PLAYER_CARDS (no infinite draw).
        random.seed(1)
        with mock.patch.object(bj, 'prompt_ace_value', return_value=bj.ACE_HIGH), \
             mock.patch.object(bj, 'prompt_hit_or_stick', return_value='hit'):
            player = bj.Hand()
            # seed the opening two cards directly, then run the decision loop
            deck = bj.build_deck()
            player.add('2', 2)
            player.add('3', 3)
            buf = io.StringIO()
            with redirect_stdout(buf):
                bj.play_player_decisions(player, deck)
            self.assertLessEqual(len(player.cards), bj.MAX_PLAYER_CARDS)


if __name__ == '__main__':
    unittest.main()
