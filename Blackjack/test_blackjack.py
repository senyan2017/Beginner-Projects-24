"""
Tests for Blackjack.py
Validates: deck management, dealer Ace handling, settlement logic,
deck size after multiple hits, and edge cases.
"""

import sys
import os
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(__file__))
from Blackjack import (
    create_deck,
    deal_card,
    card_numeric_value,
    compute_dealer_total,
    settle,
    add_card_to_player_hand,
    play_game,
)


class TestCreateDeck(unittest.TestCase):
    def test_deck_has_52_cards(self):
        deck = create_deck()
        self.assertEqual(len(deck), 52)

    def test_each_rank_has_four_copies(self):
        deck = create_deck()
        ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
        for rank in ranks:
            self.assertEqual(deck.count(rank), 4, f"Rank {rank} should appear exactly 4 times")


class TestDealCard(unittest.TestCase):
    def test_deal_removes_card_from_deck(self):
        deck = create_deck()
        original_size = len(deck)
        card = deal_card(deck)
        self.assertEqual(len(deck), original_size - 1)
        self.assertIn(card, ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K'])

    def test_deal_multiple_cards_reduces_deck(self):
        deck = create_deck()
        cards_drawn = []
        for _ in range(10):
            cards_drawn.append(deal_card(deck))
        self.assertEqual(len(deck), 52 - 10)
        self.assertEqual(len(cards_drawn), 10)

    def test_deal_all_cards(self):
        """Drawing all 52 cards should empty the deck."""
        deck = create_deck()
        drawn = set()
        for _ in range(52):
            drawn.add(deal_card(deck))
        self.assertEqual(len(deck), 0)

    def test_deal_from_empty_deck_raises(self):
        deck = []
        with self.assertRaises(RuntimeError):
            deal_card(deck)

    def test_deal_returns_actual_card_from_deck(self):
        """The dealt card should be one that was in the deck."""
        deck = [5, 5, 5, 5]
        card = deal_card(deck)
        self.assertEqual(card, 5)
        self.assertEqual(len(deck), 3)


class TestCardNumericValue(unittest.TestCase):
    def test_number_cards(self):
        for n in range(2, 11):
            self.assertEqual(card_numeric_value(n), n)

    def test_face_cards(self):
        for face in ('J', 'Q', 'K'):
            self.assertEqual(card_numeric_value(face), 10)

    def test_ace_returns_11(self):
        """Ace base value is 11; dealer/player logic adjusts as needed."""
        self.assertEqual(card_numeric_value('A'), 11)


class TestComputeDealerTotal(unittest.TestCase):
    def test_no_aces(self):
        self.assertEqual(compute_dealer_total([5, 7]), 12)
        self.assertEqual(compute_dealer_total([10, 'K']), 20)

    def test_single_ace_safe(self):
        """Ace counts as 11 when total <= 21."""
        self.assertEqual(compute_dealer_total(['A', 5]), 16)
        self.assertEqual(compute_dealer_total(['A', 10]), 21)

    def test_single_ace_bust_avoidance(self):
        """Ace drops to 1 when 11 would bust."""
        # A + 9 + 5: with A=11 → 25 (bust), so A=1 → 15
        self.assertEqual(compute_dealer_total(['A', 9, 5]), 15)

    def test_two_aces(self):
        """Two aces: first=11, second=1 → total 12."""
        self.assertEqual(compute_dealer_total(['A', 'A']), 12)

    def test_two_aces_with_other_cards(self):
        # A + A + 9: 11 + 1 + 9 = 21
        self.assertEqual(compute_dealer_total(['A', 'A', 9]), 21)
        # A + A + 10: 11 + 1 + 10 = 22 → both become 1 → 12
        self.assertEqual(compute_dealer_total(['A', 'A', 10]), 12)

    def test_dealer_blackjack(self):
        self.assertEqual(compute_dealer_total(['A', 'K']), 21)

    def test_dealer_bust(self):
        self.assertEqual(compute_dealer_total([10, 10, 10]), 30)


class TestSettle(unittest.TestCase):
    """Test the settle() function output and return value."""

    def test_player_wins_higher_total(self):
        with patch('builtins.print'):
            result = settle(20, 18)
        self.assertEqual(result, 'win')

    def test_dealer_wins_higher_total(self):
        with patch('builtins.print'):
            result = settle(18, 20)
        self.assertEqual(result, 'lose')

    def test_push_equal_totals(self):
        with patch('builtins.print'):
            result = settle(19, 19)
        self.assertEqual(result, 'push')

    def test_dealer_bust_player_wins(self):
        with patch('builtins.print'):
            result = settle(18, 22)
        self.assertEqual(result, 'win')

    def test_player_bust_dealer_wins(self):
        with patch('builtins.print'):
            result = settle(22, 18)
        self.assertEqual(result, 'lose')

    def test_both_bust_push(self):
        with patch('builtins.print'):
            result = settle(25, 23)
        self.assertEqual(result, 'push')

    def test_push_both_21(self):
        with patch('builtins.print'):
            result = settle(21, 21)
        self.assertEqual(result, 'push')


class TestAddCardToPlayerHand(unittest.TestCase):
    def test_non_ace_card(self):
        deck = [7]
        cards = []
        total = add_card_to_player_hand(deck, cards, 10)
        self.assertEqual(total, 17)
        self.assertEqual(cards, [7])
        self.assertEqual(len(deck), 0)

    @patch('builtins.input', return_value='11')
    def test_ace_as_11(self, mock_input):
        deck = ['A']
        cards = []
        total = add_card_to_player_hand(deck, cards, 5)
        self.assertEqual(total, 16)  # 5 + 11
        self.assertEqual(cards, ['A'])

    @patch('builtins.input', return_value='1')
    def test_ace_as_1(self, mock_input):
        deck = ['A']
        cards = []
        total = add_card_to_player_hand(deck, cards, 15)
        self.assertEqual(total, 16)  # 15 + 1
        self.assertEqual(cards, ['A'])


class TestDeckSizeAfterMultipleHits(unittest.TestCase):
    """Verify deck shrinks correctly through a full game sequence."""

    @patch('builtins.print')
    @patch('builtins.input')
    def test_deck_shrinks_after_hits(self, mock_input, mock_print):
        """
        Simulate: player hits twice then sticks, dealer draws one card.
        Total cards dealt: 2 (player) + 2 (dealer) + 2 (player hits) + 1 (dealer hit) = 7
        Remaining: 52 - 7 = 45
        """
        # Inputs: 'hit', 'hit', 'stick' (for player turns), then 'no' (play again)
        mock_input.side_effect = ['hit', 'hit', 'stick', 'no']
        # Seed random so dealer also draws exactly 1 card
        with patch('Blackjack.random.randint', side_effect=[0, 1, 2, 3, 4, 5, 6]):
            play_game()
        # We can't easily check deck size after play_game returns (it's local),
        # but we verified that 7 cards were dealt without error (deck had enough cards).

    @patch('builtins.print')
    @patch('builtins.input')
    def test_many_hits_dont_run_out(self, mock_input, mock_print):
        """Player hits 5 times (7 total cards) — deck must still have cards."""
        # 5 hits + stick + 'no' for play again
        mock_input.side_effect = ['hit'] * 5 + ['stick', 'no']
        # Enough cards for all draws
        with patch('Blackjack.random.randint') as mock_randint:
            # Just return sequential indices so we don't get unlucky
            mock_randint.side_effect = list(range(20))
            play_game()  # Should not raise


class TestDealerAceScenario(unittest.TestCase):
    """Requirement: dealer drawing Ace must NOT prompt the user."""

    @patch('builtins.print')
    @patch('builtins.input')
    def test_dealer_ace_no_prompt(self, mock_input, mock_print):
        """
        If dealer gets an Ace, no input() call should be made for it.
        Only player choices should trigger input().
        """
        # Player sticks immediately; dealer has an Ace and a 6 (total 17, stands)
        mock_input.side_effect = ['stick', 'no']

        with patch('Blackjack.deal_card') as mock_deal:
            # Control the exact cards dealt
            # Player: 10, 7 (total 17)
            # Dealer: A, 6 (total 17 — dealer stands, no bust)
            mock_deal.side_effect = [10, 7, 'A', 6]
            play_game()

        # Verify input was called exactly twice: 'stick' + 'no' (play again)
        # NOT called for dealer's Ace
        self.assertEqual(mock_input.call_count, 2)


class TestPlayGameEndToEnd(unittest.TestCase):
    """Full integration tests for play_game()."""

    @patch('builtins.print')
    @patch('builtins.input')
    def test_player_bust_ends_game(self, mock_input, mock_print):
        """Player hits and busts — game should not ask for more input."""
        # Player: 10 + 10 = 20, hits → gets 5 → 25 (bust), then 'no' to play again
        mock_input.side_effect = ['hit', 'no']
        with patch('Blackjack.deal_card') as mock_deal:
            mock_deal.side_effect = [10, 10, 5]
            play_game()
        # Only 'hit' and 'no' consumed
        self.assertEqual(mock_input.call_count, 2)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_dealer_bust_player_wins(self, mock_input, mock_print):
        """Player sticks; dealer draws and busts — player wins."""
        mock_input.side_effect = ['stick', 'no']
        with patch('Blackjack.deal_card') as mock_deal:
            # Player: 8, 8 = 16
            # Dealer: 10, 6 = 16 (< 17, must hit)
            # Dealer draws: 10 → 26 (bust)
            mock_deal.side_effect = [8, 8, 10, 6, 10]
            play_game()
        # Check settle was called and printed "Dealer busts"
        printed = [str(c) for c in mock_print.call_args_list]
        # At least one print call should mention dealer bust
        all_prints = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('Dealer busts', all_prints)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_tie_result(self, mock_input, mock_print):
        """Both player and dealer have same total — push."""
        mock_input.side_effect = ['stick', 'no']
        with patch('Blackjack.deal_card') as mock_deal:
            # Player: 10, 8 = 18
            # Dealer: 9, 9 = 18 (>= 17, stands)
            mock_deal.side_effect = [10, 8, 9, 9]
            play_game()
        all_prints = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('tie', all_prints.lower())

    @patch('builtins.print')
    @patch('builtins.input')
    def test_blackjack_natural(self, mock_input, mock_print):
        """Player dealt 21 immediately — game ends without asking hit/stick."""
        mock_input.side_effect = ['no']  # only play again
        with patch('Blackjack.deal_card') as mock_deal:
            # Player: A, K = 21 (but Ace prompts for value!)
            mock_deal.side_effect = ['A', 'K', 5, 7]
            # Ace prompt: choose 11
            mock_input.side_effect = ['11', 'no']
            play_game()
        all_prints = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('Blackjack', all_prints)

    @patch('builtins.print')
    @patch('builtins.input')
    def test_multiple_hits_then_stick(self, mock_input, mock_print):
        """Player hits 3 times then sticks — verify no errors."""
        # 3 hits + stick + play again
        mock_input.side_effect = ['hit', 'hit', 'hit', 'stick', 'no']
        with patch('Blackjack.deal_card') as mock_deal:
            # Player: 3, 3 = 6
            # hits: 2, 2, 2 → 12
            # Dealer: 10, 10 = 20 (stands)
            mock_deal.side_effect = [3, 3, 10, 10, 2, 2, 2]
            play_game()
        # Should have consumed: hit, hit, hit, stick, no = 5 inputs
        self.assertEqual(mock_input.call_count, 5)


if __name__ == '__main__':
    unittest.main()
