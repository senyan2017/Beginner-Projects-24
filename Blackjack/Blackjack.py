# A small terminal Blackjack game.
#
# Rules implemented here:
#   * A fresh 52-card deck (4 of each rank) is built every round.
#   * Every card that gets dealt is REMOVED from the deck, so the same
#     physical card can never be dealt twice in a single round.
#   * The player may choose whether each of their own Aces counts as 1 or 11.
#   * The dealer scores its own hand automatically (no player input): Aces
#     count as 11 unless that would bust, in which case they drop to 1. The
#     dealer keeps drawing while its total is below 17.
#   * A single settlement function decides win / lose / tie, covering player
#     bust, dealer bust and ties.
#
# Randomness uses the standard-library ``random`` module so the game runs
# without any third-party dependencies. ``random.seed`` makes tests
# deterministic.

import random

# Flip to True to see the dealer's hidden state while debugging. Player-facing
# output never depends on this flag, so normal play stays clean.
DEBUG = False

# Dealer stands once its hand reaches this total.
DEALER_STAND = 17

CARD_RANKS = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
FACE_CARDS = ('J', 'Q', 'K')


def debug(message):
    """Print debugging information only when DEBUG is enabled."""
    if DEBUG:
        print('[debug] {}'.format(message))


def build_deck():
    """Return a fresh 52-card deck (four of each rank)."""
    return [rank for rank in CARD_RANKS for _ in range(4)]


def deal_card(deck):
    """Remove a random card from ``deck`` and return it.

    This is the single source of truth for handing out cards: initial deal,
    player hits and dealer draws all go through here, so a card can never be
    dealt twice in the same round.
    """
    if not deck:
        raise ValueError('The deck is empty; cannot deal another card.')
    index = random.randrange(len(deck))
    return deck.pop(index)


def hand_value(cards):
    """Best Blackjack value of ``cards`` with automatic Ace handling.

    Aces start as 11 and are reduced to 1 one at a time while the hand would
    otherwise bust. Used for the dealer and for the final comparison.
    """
    total = 0
    aces = 0
    for card in cards:
        if card == 'A':
            aces += 1
            total += 11
        elif card in FACE_CARDS:
            total += 10
        else:
            total += int(card)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def prompt_ace_value():
    """Ask the player whether their Ace is worth 1 or 11."""
    while True:
        ace_input = input('You got an Ace! Choose a value of 1 or 11: ').strip()
        if ace_input == '1':
            return 1
        if ace_input == '11':
            return 11
        print('Please choose one of the options!')


def player_card_value(card):
    """Value of a single card from the player's point of view.

    Only the player is ever prompted about Aces; the dealer uses
    :func:`hand_value` instead, so the two flows never share input.
    """
    if card == 'A':
        return prompt_ace_value()
    if card in FACE_CARDS:
        return 10
    return int(card)


def dealer_play(deck, cards):
    """Play out the dealer's hand automatically and return its value.

    Never asks for input: Ace handling and drawing decisions are entirely the
    dealer's own rules.
    """
    while hand_value(cards) < DEALER_STAND:
        drawn = deal_card(deck)
        cards.append(drawn)
        debug('Dealer draws a {} -> hand {} (value {})'.format(
            drawn, cards, hand_value(cards)))
    return hand_value(cards)


def settle(player_total, dealer_total):
    """Decide the outcome of a finished round.

    Returns ``'player'``, ``'dealer'`` or ``'tie'`` and covers every case in
    one place: player bust, dealer bust, higher total and ties.
    """
    if player_total > 21:
        return 'dealer'
    if dealer_total > 21:
        return 'player'
    if player_total > dealer_total:
        return 'player'
    if dealer_total > player_total:
        return 'dealer'
    return 'tie'


def announce(result, dealer_total):
    """Print the player-facing result of a settled round."""
    if result == 'player':
        if dealer_total > 21:
            print('Dealer is bust!')
        print('You win!')
    elif result == 'dealer':
        print('Dealer wins!')
    else:
        print("It's a tie!")


def player_turn(deck, player_cards):
    """Run the player's hit/stick loop.

    Returns the player's final total. A total above 21 means the player has
    gone bust (the dealer no longer needs to play).
    """
    player_total = sum(player_card_value(card) for card in player_cards)
    print('The value of your hand is {}'.format(player_total))

    while True:
        if player_total > 21:
            print('Bust! Too bad.')
            return player_total

        choice = input('Hit, or stick? ').strip().lower()
        if choice == 'hit':
            card = deal_card(deck)
            print('Next card is a {}'.format(card))
            player_total += player_card_value(card)
            print('The value of your hand is now {}'.format(player_total))
        elif choice == 'stick':
            print('Stick, got it.')
            return player_total
        else:
            print('Please choose "hit" or "stick"!')


def play_round():
    """Play a single round of Blackjack from deal to result."""
    deck = build_deck()

    player_cards = [deal_card(deck), deal_card(deck)]
    dealer_cards = [deal_card(deck), deal_card(deck)]

    print('Your first card is a {}'.format(player_cards[0]))
    print('Your second card is a {}'.format(player_cards[1]))
    debug('Dealer starts with {} (value {})'.format(
        dealer_cards, hand_value(dealer_cards)))

    player_total = player_turn(deck, player_cards)

    if player_total > 21:
        # Player already busted: the dealer does not need to act.
        print('The value of the dealer\'s hand is {}'.format(
            hand_value(dealer_cards)))
        announce(settle(player_total, hand_value(dealer_cards)), hand_value(dealer_cards))
        return

    dealer_total = dealer_play(deck, dealer_cards)

    print('The value of your hand is {}'.format(player_total))
    print('The value of the dealer\'s hand is {}'.format(dealer_total))
    announce(settle(player_total, dealer_total), dealer_total)


def play_again_option():
    """Ask whether to play again. Returns True to continue, False to stop."""
    while True:
        answer = input('Would you like to play again? (yes/no) ').strip().lower()
        if answer in ('yes', 'y'):
            print('')
            return True
        if answer in ('no', 'n'):
            return False
        print('Please choose one of the options!')


def main():
    """Top-level game loop. No recursion and no quit(); just a clean loop."""
    print('Welcome to Blackjack!')
    print('')
    while True:
        play_round()
        if not play_again_option():
            print('Thanks for playing!')
            break


if __name__ == '__main__':
    main()
