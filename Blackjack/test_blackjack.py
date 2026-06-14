"""Tests for Blackjack pure game logic."""

import sys
sys.path.insert(0, '/home/huang/ali/project/project-24/work-3')

from Blackjack.Blackjack import (
    card_base_value,
    hand_value,
    is_bust,
    dealer_should_hit,
    determine_outcome,
    resolve_dealer_card,
    build_deck,
)


def test_card_base_value():
    """Test card value calculation."""
    assert card_base_value('A') == 11
    assert card_base_value('K') == 10
    assert card_base_value('Q') == 10
    assert card_base_value('J') == 10
    assert card_base_value(10) == 10
    assert card_base_value(5) == 5
    assert card_base_value(2) == 2
    print('✓ card_base_value')


def test_hand_value():
    """Test hand total calculation."""
    assert hand_value([10, 11]) == 21  # Blackjack
    assert hand_value([10, 5, 6]) == 21
    assert hand_value([10, 10, 10]) == 30  # Bust
    assert hand_value([2, 3]) == 5
    print('✓ hand_value')


def test_is_bust():
    """Test bust detection."""
    assert is_bust([10, 10, 10]) is True  # 30
    assert is_bust([10, 10, 2]) is True  # 22
    assert is_bust([10, 10, 1]) is False  # 21
    assert is_bust([5, 5]) is False  # 10
    print('✓ is_bust')


def test_dealer_should_hit():
    """Test dealer hit policy."""
    assert dealer_should_hit([10, 6]) is True  # 16 < 17
    assert dealer_should_hit([10, 5]) is True  # 15 < 17
    assert dealer_should_hit([10, 7]) is False  # 17
    assert dealer_should_hit([10, 10]) is False  # 20
    print('✓ dealer_should_hit')


def test_determine_outcome():
    """Test win/loss/push determination."""
    assert determine_outcome([10, 10], [10, 9]) == 'player_win'  # 20 vs 19
    assert determine_outcome([10, 8], [10, 9]) == 'dealer_win'  # 18 vs 19
    assert determine_outcome([10, 9], [10, 9]) == 'push'  # 19 vs 19
    assert determine_outcome([10, 11], [10, 10]) == 'player_win'  # 21 vs 20
    print('✓ determine_outcome')


def test_resolve_dealer_card():
    """Test dealer ace resolution (auto-adjust)."""
    # Ace with low hand -> should be 11
    assert resolve_dealer_card('A', [5]) == 11  # 5 + 11 = 16
    # Ace with high hand -> should be 1 to avoid bust
    assert resolve_dealer_card('A', [10, 5]) == 1  # 15 + 11 = 26 (bust), so 1
    assert resolve_dealer_card('A', [10, 10]) == 1  # 20 + 11 = 31 (bust), so 1
    # Non-ace cards
    assert resolve_dealer_card('K', [5]) == 10
    assert resolve_dealer_card(7, [5]) == 7
    print('✓ resolve_dealer_card')


def test_build_deck():
    """Test deck construction."""
    deck = build_deck()
    assert len(deck) == 52
    # Check all ranks present
    ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
    for rank in ranks:
        assert deck.count(rank) == 4, f'Expected 4 {rank}s, got {deck.count(rank)}'
    print('✓ build_deck')


if __name__ == '__main__':
    print('Running Blackjack tests...\n')
    test_card_base_value()
    test_hand_value()
    test_is_bust()
    test_dealer_should_hit()
    test_determine_outcome()
    test_resolve_dealer_card()
    test_build_deck()
    print('\n✅ All tests passed!')
