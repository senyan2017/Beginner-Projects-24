# Blackjack - a small but playable command line version.
#
# Highlights over the original one-shot script:
#   * Cards are dealt from a single deck and removed once dealt (no duplicates).
#   * Money: you start with a balance and place a bet each round.
#   * The dealer follows real rules (hits until 17, busts/ties resolved) and
#     works out its own Aces automatically - it never asks you to choose for it.
#   * Each round ends with a clear summary (cards dealt, bet, result, balance).
#   * Your balance and win/loss record carry over from round to round.
#
# The pure game logic lives in module level functions so it can be tested
# without any terminal interaction. The interactive loop only runs when the
# file is executed directly (see the __main__ guard at the bottom).

import random

STARTING_BALANCE = 100
DEALER_STANDS_ON = 17  # dealer keeps drawing while its hand is below this value

# One entry per rank; the deck has four of each.
CARD_RANKS = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
FACE_CARDS = ('J', 'Q', 'K')


# --------------------------------------------------------------------------- #
# Pure helpers (no input/print) - these are what the tests exercise.
# --------------------------------------------------------------------------- #
def make_deck():
    """Return a fresh, ordered 52 card deck (four of every rank)."""
    deck = []
    for rank in CARD_RANKS:
        deck.extend([rank] * 4)
    return deck


def shuffle_deck(deck):
    """Shuffle the deck in place (and return it for convenience)."""
    random.shuffle(deck)
    return deck


def deal_card(deck):
    """Remove and return a single card from the deck.

    Cards are taken from the end of the list. Because the card is popped, it
    can never be dealt twice - this is what keeps the deck honest.
    """
    if not deck:
        raise ValueError('The deck is empty - cannot deal another card.')
    return deck.pop()


def card_points(card):
    """Point value of a single card, treating an Ace as 11 by default."""
    if card == 'A':
        return 11
    if card in FACE_CARDS:
        return 10
    return card


def calculate_hand_value(cards):
    """Best total for a hand, demoting Aces from 11 to 1 only as needed.

    This is the standard automatic Ace rule: count every Ace as 11, then while
    the hand is bust and an Ace is still counted high, drop it to 1.
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
            total += card
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def is_bust(cards):
    """True if the hand's best value is over 21."""
    return calculate_hand_value(cards) > 21


def dealer_play(deck, dealer_cards, stands_on=DEALER_STANDS_ON):
    """Let the dealer draw until it reaches ``stands_on`` (Aces handled auto).

    Mutates and returns ``dealer_cards``.
    """
    while calculate_hand_value(dealer_cards) < stands_on:
        dealer_cards.append(deal_card(deck))
    return dealer_cards


def determine_outcome(player_value, dealer_value):
    """Resolve a round from the two final totals.

    Returns one of 'win', 'lose' or 'push' from the player's point of view.
    A player bust always loses; otherwise a dealer bust wins; otherwise the
    higher total wins and equal totals push (tie).
    """
    if player_value > 21:
        return 'lose'
    if dealer_value > 21:
        return 'win'
    if player_value > dealer_value:
        return 'win'
    if player_value < dealer_value:
        return 'lose'
    return 'push'


def settle_balance(balance, bet, outcome):
    """Apply the result of a round to the balance and return the new balance."""
    if outcome == 'win':
        return balance + bet
    if outcome == 'lose':
        return balance - bet
    return balance  # push leaves the balance untouched


# --------------------------------------------------------------------------- #
# Interactive helpers (these talk to the terminal).
# --------------------------------------------------------------------------- #
def ace_choice():
    """Ask the *player* whether their Ace should count as 1 or 11."""
    while True:
        print('You got an Ace! Do you choose a value of 1 or 11?')
        choice = input('?> ').strip()
        if choice == '1':
            return 1
        if choice == '11':
            return 11
        print('Please choose one of the options!')


def get_bet(balance):
    """Prompt for a valid bet (whole number, 1..balance)."""
    while True:
        print('You have {} chips. How much would you like to bet?'.format(balance))
        raw = input('?> ').strip()
        try:
            bet = int(raw)
        except ValueError:
            print('Please enter a whole number.')
            continue
        if bet <= 0:
            print('Your bet must be greater than 0.')
            continue
        if bet > balance:
            print('You cannot bet more than you have!')
            continue
        return bet


def deal_to_player(deck, player_cards):
    """Deal one card to the player, asking about Aces, and return its value."""
    card = deal_card(deck)
    player_cards.append(card)
    if card == 'A':
        value = ace_choice()
    else:
        value = card_points(card)
    return card, value


def run_player_turn(deck, player_cards, player_value):
    """Hit/stick loop for the player. Returns (player_value, busted)."""
    while True:
        if player_value > 21:
            print('Bust! Too bad.')
            return player_value, True
        print('Hit, or stick?')
        choice = input('?> ').strip().lower()
        if choice == 'hit':
            print('Ok partner, another card coming up.')
            card, value = deal_to_player(deck, player_cards)
            player_value += value
            print('You were dealt a {}.'.format(card))
            print('The value of your hand is now {}.'.format(player_value))
        elif choice == 'stick':
            print('Stick, got it.')
            return player_value, False
        else:
            print('Please choose either "hit" or "stick"!')


def describe_hand(cards):
    """Readable 'A, 10, K' style listing of a hand."""
    return ', '.join(str(card) for card in cards)


def play_round(deck, balance, stats):
    """Play a single round interactively. Returns the updated balance."""
    bet = get_bet(balance)
    print('')

    player_cards = []
    dealer_cards = []
    player_value = 0

    # Opening deal: two cards each.
    for _ in range(2):
        card, value = deal_to_player(deck, player_cards)
        player_value += value
        print('You were dealt a {}.'.format(card))
    print('The value of your hand is {}.'.format(player_value))

    dealer_cards.append(deal_card(deck))
    dealer_cards.append(deal_card(deck))
    print('The dealer is showing a {} (other card face down).'.format(dealer_cards[0]))
    print('')

    player_value, busted = run_player_turn(deck, player_cards, player_value)

    if busted:
        dealer_value = calculate_hand_value(dealer_cards)
    else:
        # Dealer reveals and plays out its hand automatically.
        dealer_play(deck, dealer_cards)
        dealer_value = calculate_hand_value(dealer_cards)

    outcome = determine_outcome(player_value, dealer_value)
    balance = settle_balance(balance, bet, outcome)

    if outcome == 'win':
        stats['wins'] += 1
    elif outcome == 'lose':
        stats['losses'] += 1
    else:
        stats['pushes'] += 1
    stats['rounds'] += 1

    print('')
    print('------------------------------ Round summary ------------------------------')
    print('Your hand:   {}  (value {})'.format(describe_hand(player_cards), player_value))
    print('Dealer hand: {}  (value {})'.format(describe_hand(dealer_cards), dealer_value))
    if outcome == 'win':
        print('Result: You win! You gained {} chips.'.format(bet))
    elif outcome == 'lose':
        print('Result: Dealer wins. You lost {} chips.'.format(bet))
    else:
        print('Result: Push (tie). Your bet of {} chips is returned.'.format(bet))
    print('Bet: {}   Balance: {}'.format(bet, balance))
    print('Record so far - wins: {}, losses: {}, pushes: {} (over {} rounds)'.format(
        stats['wins'], stats['losses'], stats['pushes'], stats['rounds']))
    print('---------------------------------------------------------------------------')
    print('')
    return balance


def play_again_option():
    """Ask whether to keep playing. Returns True to continue, False to stop."""
    while True:
        print('Would you like to play again?')
        choice = input('?> ').strip().lower()
        if choice in ('yes', 'y'):
            print('')
            return True
        if choice in ('no', 'n'):
            return False
        print('Please choose one of the options!')


def main():
    """Run the interactive game, carrying balance and record across rounds."""
    print('Welcome to Blackjack!')
    balance = STARTING_BALANCE
    stats = {'wins': 0, 'losses': 0, 'pushes': 0, 'rounds': 0}

    while True:
        if balance <= 0:
            print('You are out of chips! Game over.')
            break

        # A freshly shuffled deck each round keeps the game self contained
        # while still guaranteeing no duplicate cards within the round.
        deck = shuffle_deck(make_deck())
        balance = play_round(deck, balance, stats)

        if not play_again_option():
            break

    print('Thanks for playing! Final balance: {} chips.'.format(balance))
    print('Final record - wins: {}, losses: {}, pushes: {} (over {} rounds).'.format(
        stats['wins'], stats['losses'], stats['pushes'], stats['rounds']))


if __name__ == '__main__':
    main()
