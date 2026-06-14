"""Tests for the core (non-interactive) Blackjack logic.

Run from the Blackjack directory with:

    python -m unittest test_blackjack

These focus on the high-risk areas called out for this game: deduplicated
dealing, bet settlement, the dealer's automatic draw rules, and Ace scoring.

``deal_card`` pops from the *end* of the deck, so a deck is laid out with the
first card to be drawn placed last. That makes dealer behaviour deterministic
without needing to seed any randomness.
"""

import unittest

import Blackjack as bj


class DeckDealingTests(unittest.TestCase):
    def test_fresh_deck_has_52_cards(self):
        self.assertEqual(len(bj.make_deck()), 52)

    def test_four_of_every_rank(self):
        deck = bj.make_deck()
        for rank in bj.CARD_RANKS:
            self.assertEqual(deck.count(rank), 4, 'rank {!r} not present 4x'.format(rank))

    def test_dealing_removes_the_card(self):
        deck = bj.make_deck()
        before = len(deck)
        bj.deal_card(deck)
        self.assertEqual(len(deck), before - 1)

    def test_dealing_whole_deck_is_a_permutation_with_no_duplicates(self):
        original = bj.make_deck()
        deck = bj.make_deck()
        dealt = [bj.deal_card(deck) for _ in range(52)]
        # Every card came out exactly once -> the multiset matches the original.
        self.assertEqual(sorted(map(str, dealt)), sorted(map(str, original)))
        self.assertEqual(len(deck), 0)
        # No rank appears more than its four copies.
        for rank in bj.CARD_RANKS:
            self.assertEqual(dealt.count(rank), 4)

    def test_dealing_from_empty_deck_raises(self):
        with self.assertRaises(ValueError):
            bj.deal_card([])

    def test_deal_card_is_deterministic_from_the_end(self):
        deck = ['A', 5, 'K']
        self.assertEqual(bj.deal_card(deck), 'K')
        self.assertEqual(bj.deal_card(deck), 5)
        self.assertEqual(bj.deal_card(deck), 'A')


class CardPointsTests(unittest.TestCase):
    def test_face_cards_are_ten(self):
        for rank in ('J', 'Q', 'K'):
            self.assertEqual(bj.card_points(rank), 10)

    def test_number_cards_are_themselves(self):
        self.assertEqual(bj.card_points(2), 2)
        self.assertEqual(bj.card_points(10), 10)

    def test_ace_defaults_to_eleven(self):
        self.assertEqual(bj.card_points('A'), 11)


class HandValueTests(unittest.TestCase):
    def test_blackjack(self):
        self.assertEqual(bj.calculate_hand_value(['A', 'K']), 21)

    def test_ace_high_when_it_fits(self):
        self.assertEqual(bj.calculate_hand_value(['A', 9]), 20)

    def test_two_aces_count_as_twelve(self):
        self.assertEqual(bj.calculate_hand_value(['A', 'A']), 12)

    def test_two_aces_plus_nine(self):
        self.assertEqual(bj.calculate_hand_value(['A', 'A', 9]), 21)

    def test_three_aces(self):
        self.assertEqual(bj.calculate_hand_value(['A', 'A', 'A']), 13)

    def test_ace_demotes_to_avoid_bust(self):
        self.assertEqual(bj.calculate_hand_value(['A', 9, 5]), 15)

    def test_plain_hands(self):
        self.assertEqual(bj.calculate_hand_value([10, 6]), 16)
        self.assertEqual(bj.calculate_hand_value(['K', 'Q']), 20)
        self.assertEqual(bj.calculate_hand_value([7, 7, 7]), 21)

    def test_bust_without_aces(self):
        self.assertEqual(bj.calculate_hand_value([10, 'J', 'Q']), 30)
        self.assertTrue(bj.is_bust([10, 'J', 'Q']))
        self.assertFalse(bj.is_bust(['A', 'K']))


class DealerPlayTests(unittest.TestCase):
    def test_dealer_stands_on_17_without_drawing(self):
        dealer = [10, 7]
        deck = [5, 5]
        bj.dealer_play(deck, dealer)
        self.assertEqual(dealer, [10, 7])
        self.assertEqual(len(deck), 2)  # untouched

    def test_dealer_hits_until_it_reaches_17(self):
        dealer = [10, 6]          # 16, must hit
        deck = [5]                # draws the 5 -> 21, then stands
        bj.dealer_play(deck, dealer)
        self.assertEqual(dealer, [10, 6, 5])
        self.assertEqual(bj.calculate_hand_value(dealer), 21)
        self.assertEqual(len(deck), 0)

    def test_dealer_can_bust_while_drawing(self):
        dealer = [2, 4]           # 6
        deck = [10, 10]           # draws 10 -> 16, draws 10 -> 26 (bust)
        bj.dealer_play(deck, dealer)
        self.assertEqual(dealer, [2, 4, 10, 10])
        self.assertTrue(bj.is_bust(dealer))

    def test_dealer_stands_on_soft_17_with_an_ace(self):
        dealer = ['A', 6]         # soft 17 -> stands under the "below 17" rule
        deck = [9]
        bj.dealer_play(deck, dealer)
        self.assertEqual(dealer, ['A', 6])
        self.assertEqual(len(deck), 1)

    def test_dealer_keeps_ace_high_after_a_hit(self):
        dealer = ['A', 3]         # 14, must hit
        deck = [3]                # draws 3 -> 11+3+3 = 17, stands
        bj.dealer_play(deck, dealer)
        self.assertEqual(dealer, ['A', 3, 3])
        self.assertEqual(bj.calculate_hand_value(dealer), 17)


class OutcomeTests(unittest.TestCase):
    def test_player_bust_always_loses(self):
        self.assertEqual(bj.determine_outcome(22, 18), 'lose')
        self.assertEqual(bj.determine_outcome(22, 25), 'lose')  # even if dealer also bust

    def test_dealer_bust_wins_for_player(self):
        self.assertEqual(bj.determine_outcome(20, 22), 'win')

    def test_higher_total_wins(self):
        self.assertEqual(bj.determine_outcome(20, 18), 'win')
        self.assertEqual(bj.determine_outcome(18, 20), 'lose')

    def test_equal_totals_push(self):
        self.assertEqual(bj.determine_outcome(19, 19), 'push')


class SettlementTests(unittest.TestCase):
    def test_win_adds_the_bet(self):
        self.assertEqual(bj.settle_balance(100, 20, 'win'), 120)

    def test_loss_subtracts_the_bet(self):
        self.assertEqual(bj.settle_balance(100, 20, 'lose'), 80)

    def test_push_leaves_balance_unchanged(self):
        self.assertEqual(bj.settle_balance(100, 20, 'push'), 100)


class RoundIntegrationTests(unittest.TestCase):
    """Compose the pure pieces to prove a full round resolves correctly."""

    def test_player_sticks_and_beats_a_drawing_dealer(self):
        player = ['K', 9]                     # 19, player sticks
        dealer = [10, 6]                      # 16, must hit
        deck = [2]                            # dealer draws 2 -> 18, stands
        bj.dealer_play(deck, dealer)
        outcome = bj.determine_outcome(
            bj.calculate_hand_value(player),
            bj.calculate_hand_value(dealer),
        )
        self.assertEqual(outcome, 'win')
        self.assertEqual(bj.settle_balance(100, 25, outcome), 125)

    def test_dealer_busts_so_player_wins(self):
        player = ['A', 7]                     # 18
        dealer = [10, 6]                      # 16
        deck = [10]                           # dealer draws 10 -> 26, bust
        bj.dealer_play(deck, dealer)
        outcome = bj.determine_outcome(
            bj.calculate_hand_value(player),
            bj.calculate_hand_value(dealer),
        )
        self.assertEqual(outcome, 'win')


if __name__ == '__main__':
    unittest.main()
