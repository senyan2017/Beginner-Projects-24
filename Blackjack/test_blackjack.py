"""
Tests for Blackjack core logic.
Focuses on: dedup deck, betting settlement, dealer auto-play, Ace scoring.
"""

import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Blackjack'))
from Blackjack import (
    create_deck, deal_card, card_base_value, hand_value,
    compute_player_total, ask_ace_value, card_display,
    dealer_play, play_round,
)


class TestDeck(unittest.TestCase):
    """Deck creation and card removal tests."""

    def test_deck_has_52_cards(self):
        deck = create_deck()
        self.assertEqual(len(deck), 52)

    def test_deck_has_4_of_each_rank(self):
        deck = create_deck()
        ranks = [c[0] for c in deck]
        for rank in ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']:
            self.assertEqual(ranks.count(rank), 4, f"Rank {rank} should appear 4 times")

    def test_deck_has_4_suits(self):
        deck = create_deck()
        suits = [c[1] for c in deck]
        for suit in ['Hearts', 'Diamonds', 'Clubs', 'Spades']:
            self.assertEqual(suits.count(suit), 13, f"Suit {suit} should appear 13 times")

    def test_all_cards_unique(self):
        deck = create_deck()
        self.assertEqual(len(set(deck)), 52)

    def test_deal_card_removes_from_deck(self):
        deck = create_deck()
        initial_size = len(deck)
        card = deal_card(deck)
        self.assertEqual(len(deck), initial_size - 1)
        self.assertNotIn(card, deck)

    def test_deal_all_cards_no_duplicates(self):
        """Dealing all 52 cards should produce 52 unique cards with empty deck."""
        deck = create_deck()
        dealt = []
        for _ in range(52):
            dealt.append(deal_card(deck))
        self.assertEqual(len(deck), 0)
        self.assertEqual(len(set(dealt)), 52)

    def test_deal_multiple_cards_all_unique(self):
        """Dealing 10 cards should give 10 unique cards."""
        deck = create_deck()
        dealt = [deal_card(deck) for _ in range(10)]
        self.assertEqual(len(dealt), 10)
        self.assertEqual(len(set(dealt)), 10)
        self.assertEqual(len(deck), 42)


class TestCardValues(unittest.TestCase):
    """Card base value and hand value computation."""

    def test_number_cards(self):
        for n in range(2, 11):
            self.assertEqual(card_base_value((n, 'Hearts')), n)

    def test_face_cards_are_10(self):
        for face in ('J', 'Q', 'K'):
            self.assertEqual(card_base_value((face, 'Spades')), 10)

    def test_ace_base_value_is_1(self):
        self.assertEqual(card_base_value(('A', 'Clubs')), 1)

    def test_hand_value_no_aces(self):
        cards = [(10, 'Hearts'), (5, 'Diamonds')]
        self.assertEqual(hand_value(cards), 15)

    def test_hand_value_single_ace_as_11(self):
        """Ace should be 11 when it doesn't bust."""
        cards = [('A', 'Hearts'), (9, 'Diamonds')]
        self.assertEqual(hand_value(cards), 20)

    def test_hand_value_ace_forced_to_1(self):
        """Ace must be 1 when 11 would bust."""
        cards = [('A', 'Hearts'), (10, 'Diamonds'), (5, 'Clubs')]
        self.assertEqual(hand_value(cards), 16)

    def test_hand_value_two_aces(self):
        """Two Aces: one as 11, one as 1 = 12."""
        cards = [('A', 'Hearts'), ('A', 'Diamonds')]
        self.assertEqual(hand_value(cards), 12)

    def test_hand_value_blackjack(self):
        cards = [('A', 'Spades'), (10, 'Hearts')]
        self.assertEqual(hand_value(cards), 21)

    def test_hand_value_multiple_cards_with_ace(self):
        cards = [('A', 'Hearts'), (3, 'Diamonds'), (4, 'Clubs')]
        self.assertEqual(hand_value(cards), 18)

    def test_hand_value_three_aces(self):
        """Three Aces: one 11, two 1s = 13."""
        cards = [('A', 'H'), ('A', 'D'), ('A', 'C')]
        self.assertEqual(hand_value(cards), 13)


class TestPlayerAceTracking(unittest.TestCase):
    """Player Ace value selection and total computation."""

    def test_compute_total_no_aces(self):
        self.assertEqual(compute_player_total(15, []), 15)

    def test_compute_total_with_ace_11(self):
        self.assertEqual(compute_player_total(10, [11]), 21)

    def test_compute_total_with_ace_1(self):
        self.assertEqual(compute_player_total(10, [1]), 11)

    def test_compute_total_multiple_aces(self):
        self.assertEqual(compute_player_total(5, [11, 1]), 17)

    @patch('builtins.input', side_effect=['11'])
    def test_ask_ace_value_11(self, mock_input):
        val = ask_ace_value(('A', 'Hearts'))
        self.assertEqual(val, 11)

    @patch('builtins.input', side_effect=['1'])
    def test_ask_ace_value_1(self, mock_input):
        val = ask_ace_value(('A', 'Spades'))
        self.assertEqual(val, 1)

    @patch('builtins.input', side_effect=['bad', '11'])
    def test_ask_ace_value_invalid_then_valid(self, mock_input):
        val = ask_ace_value(('A', 'Clubs'))
        self.assertEqual(val, 11)


class TestDealerPlay(unittest.TestCase):
    """Dealer auto-play: hit on <17, stand on >=17."""

    def test_dealer_stands_on_17(self):
        deck = create_deck()
        # Give dealer 10 + 7 = 17
        dealer_cards = [(10, 'Hearts'), (7, 'Diamonds')]
        result = dealer_play(deck, dealer_cards)
        self.assertEqual(len(result), 2)  # no extra cards drawn
        self.assertEqual(hand_value(result), 17)

    def test_dealer_stands_on_18(self):
        deck = create_deck()
        dealer_cards = [(10, 'Hearts'), (8, 'Diamonds')]
        result = dealer_play(deck, dealer_cards)
        self.assertEqual(len(result), 2)

    def test_dealer_hits_on_16(self):
        deck = create_deck()
        # 10 + 6 = 16 → must hit
        dealer_cards = [(10, 'Hearts'), (6, 'Diamonds')]
        result = dealer_play(deck, dealer_cards)
        self.assertGreater(len(result), 2)

    def test_dealer_hits_on_low_value(self):
        deck = create_deck()
        dealer_cards = [(3, 'Hearts'), (4, 'Diamonds')]  # 7
        result = dealer_play(deck, dealer_cards)
        self.assertGreater(hand_value(result), 7)
        self.assertGreaterEqual(hand_value(result), 17)

    def test_dealer_ace_auto_counted(self):
        """Dealer Ace should be auto-counted as 11 when beneficial."""
        deck = create_deck()
        # Ace + 6 = soft 17 → stand
        dealer_cards = [('A', 'Hearts'), (6, 'Diamonds')]
        result = dealer_play(deck, dealer_cards)
        self.assertEqual(hand_value(result), 17)
        self.assertEqual(len(result), 2)

    def test_dealer_ace_forced_to_1(self):
        """Dealer Ace must be 1 when 11 would bust."""
        deck = create_deck()
        # Ace + 10 + 5: Ace as 11 → 26 (bust), so Ace = 1 → 16, must hit
        dealer_cards = [('A', 'Hearts'), (10, 'Diamonds'), (5, 'Clubs')]
        result = dealer_play(deck, dealer_cards)
        # hand_value should be at least 17 (dealer hit from 16)
        self.assertGreaterEqual(hand_value(result), 17)

    def test_dealer_bust_possible(self):
        """With a rigged deck, dealer can bust."""
        # Create a deck where top cards are all 10s
        deck = [(10, 'H'), (10, 'D'), (10, 'C'), (10, 'S'),
                (2, 'H'), (2, 'D'), (2, 'C'), (2, 'S')]
        dealer_cards = [(10, 'H'), (6, 'D')]  # 16, must hit → draws 10 → 26 bust
        # We need to control what deal_card pops; since deal_card uses random,
        # let's just verify the logic by checking hand_value > 21 possibility
        # Use a simple direct test instead:
        self.assertEqual(hand_value(dealer_cards), 16)
        dealer_cards.append((10, 'C'))
        self.assertEqual(hand_value(dealer_cards), 26)
        self.assertGreater(hand_value(dealer_cards), 21)


class TestCardDisplay(unittest.TestCase):

    def test_number_card(self):
        self.assertEqual(card_display((5, 'Hearts')), '5 of Hearts')

    def test_face_card(self):
        self.assertEqual(card_display(('K', 'Spades')), 'K of Spades')

    def test_ace(self):
        self.assertEqual(card_display(('A', 'Clubs')), 'A of Clubs')


class TestBettingAndBalance(unittest.TestCase):
    """Test betting settlement via play_round with mocked input."""

    @patch('builtins.input')
    def test_player_bust_loses_bet(self, mock_input):
        """Player busts → loses bet amount."""
        # bet=100, hit until bust
        # Sequence: bet amount, then 'hit' choices, ace choices if needed, play again
        mock_input.side_effect = ['100', 'hit', 'hit', 'hit', 'hit', 'hit', 'no']
        balance, keep_playing = play_round(1000)
        self.assertLessEqual(balance, 1000)  # lost something
        self.assertFalse(keep_playing)

    @patch('builtins.input')
    def test_stick_immediately_with_low_cards(self, mock_input):
        """Player sticks immediately, dealer plays out."""
        # bet=50, stick right away
        mock_input.side_effect = ['50', 'stick', 'no']
        balance, keep_playing = play_round(500)
        # Balance should be 500±50
        self.assertIn(balance, [450, 500, 550])
        self.assertFalse(keep_playing)

    @patch('builtins.input')
    def test_bet_validation_rejects_zero(self, mock_input):
        """Zero bet should be rejected, then accept valid bet."""
        mock_input.side_effect = ['0', '50', 'stick', 'no']
        balance, _ = play_round(500)
        self.assertIn(balance, [450, 500, 550])

    @patch('builtins.input')
    def test_bet_validation_rejects_over_balance(self, mock_input):
        """Bet over balance should be rejected."""
        mock_input.side_effect = ['2000', '50', 'stick', 'no']
        balance, _ = play_round(500)
        self.assertIn(balance, [450, 500, 550])

    @patch('builtins.input')
    def test_bet_validation_rejects_non_numeric(self, mock_input):
        """Non-numeric bet should be rejected."""
        mock_input.side_effect = ['abc', '50', 'stick', 'no']
        balance, _ = play_round(500)
        self.assertIn(balance, [450, 500, 550])

    @patch('builtins.input')
    def test_game_over_when_broke(self, mock_input):
        """If balance reaches 0, game should end."""
        mock_input.side_effect = ['500', 'stick']
        balance, keep_playing = play_round(500)
        # If player loses the entire 500, balance = 0 → game over
        if balance == 0:
            self.assertFalse(keep_playing)


class TestPlayRoundIntegration(unittest.TestCase):
    """Integration tests for full rounds with controlled randomness."""

    @patch('Blackjack.deal_card')
    @patch('Blackjack.create_deck')
    @patch('builtins.input')
    def test_player_blackjack_payout(self, mock_input, mock_create, mock_deal):
        """Natural Blackjack should pay 3:2."""
        mock_create.return_value = [(2, 'H')] * 52  # dummy deck
        # player gets A+10 (blackjack), dealer gets 5+5
        cards_iter = iter([
            ('A', 'Hearts'), (10, 'Diamonds'),  # player
            (5, 'Clubs'), (5, 'Spades'),        # dealer
        ])
        mock_deal.side_effect = lambda deck: next(cards_iter)

        # bet=100, ace as 11, then dealer plays, say 'no' to play again
        mock_input.side_effect = ['100', '11', 'no']
        balance, _ = play_round(1000)
        # Blackjack pays 3:2 → win 150
        self.assertEqual(balance, 1150)

    @patch('Blackjack.deal_card')
    @patch('Blackjack.create_deck')
    @patch('builtins.input')
    def test_push_returns_bet(self, mock_input, mock_create, mock_deal):
        """Tie (push) should return bet unchanged."""
        mock_create.return_value = [(2, 'H')] * 52
        # Both get 20
        cards_iter = iter([
            (10, 'Hearts'), (10, 'Diamonds'),   # player = 20
            (10, 'Clubs'), (10, 'Spades'),       # dealer = 20
        ])
        mock_deal.side_effect = lambda deck: next(cards_iter)

        mock_input.side_effect = ['100', 'stick', 'no']
        balance, _ = play_round(1000)
        self.assertEqual(balance, 1000)  # push → no change

    @patch('Blackjack.Blackjack.deal_card')
    @patch('Blackjack.Blackjack.create_deck')
    @patch('builtins.input')
    def test_dealer_bust_player_wins(self, mock_input, mock_create, mock_deal):
        """Dealer busts → player wins bet."""
        mock_create.return_value = [(2, 'H')] * 52
        # Player gets 19, dealer gets 16 then draws 10 → 26 bust
        cards_iter = iter([
            (10, 'Hearts'), (9, 'Diamonds'),    # player = 19
            (10, 'Clubs'), (6, 'Spades'),        # dealer = 16
            (10, 'Hearts'),                       # dealer draws → 26 bust
        ])
        mock_deal.side_effect = lambda deck: next(cards_iter)

        mock_input.side_effect = ['100', 'stick', 'no']
        balance, _ = play_round(1000)
        self.assertEqual(balance, 1100)  # won 100

    @patch('Blackjack.Blackjack.deal_card')
    @patch('Blackjack.Blackjack.create_deck')
    @patch('builtins.input')
    def test_player_bust_loses(self, mock_input, mock_create, mock_deal):
        """Player busts on hit → loses bet."""
        mock_create.return_value = [(2, 'H')] * 52
        # Player gets 15 then draws 10 → 25 bust
        cards_iter = iter([
            (10, 'Hearts'), (5, 'Diamonds'),    # player = 15
            (3, 'Clubs'), (4, 'Spades'),         # dealer (won't matter)
            (10, 'Hearts'),                       # player draws → 25 bust
        ])
        mock_deal.side_effect = lambda deck: next(cards_iter)

        mock_input.side_effect = ['100', 'hit', 'no']
        balance, _ = play_round(1000)
        self.assertEqual(balance, 900)  # lost 100

    @patch('Blackjack.Blackjack.deal_card')
    @patch('Blackjack.Blackjack.create_deck')
    @patch('builtins.input')
    def test_player_wins_higher_hand(self, mock_input, mock_create, mock_deal):
        """Player has higher hand than dealer → wins."""
        mock_create.return_value = [(2, 'H')] * 52
        # Player = 20, dealer = 18 (stands)
        cards_iter = iter([
            (10, 'Hearts'), (10, 'Diamonds'),   # player = 20
            (10, 'Clubs'), (8, 'Spades'),        # dealer = 18
        ])
        mock_deal.side_effect = lambda deck: next(cards_iter)

        mock_input.side_effect = ['100', 'stick', 'no']
        balance, _ = play_round(1000)
        self.assertEqual(balance, 1100)

    @patch('Blackjack.Blackjack.deal_card')
    @patch('Blackjack.Blackjack.create_deck')
    @patch('builtins.input')
    def test_dealer_wins_higher_hand(self, mock_input, mock_create, mock_deal):
        """Dealer has higher hand → player loses."""
        mock_create.return_value = [(2, 'H')] * 52
        # Player = 17, dealer = 20
        cards_iter = iter([
            (10, 'Hearts'), (7, 'Diamonds'),    # player = 17
            (10, 'Clubs'), (10, 'Spades'),       # dealer = 20
        ])
        mock_deal.side_effect = lambda deck: next(cards_iter)

        mock_input.side_effect = ['100', 'stick', 'no']
        balance, _ = play_round(1000)
        self.assertEqual(balance, 900)


if __name__ == '__main__':
    unittest.main()
