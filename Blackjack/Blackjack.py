"""Terminal Blackjack game.

The code is split into clearly separated layers so a single round is easy to
follow and the core rules can be tested without playing a whole game by hand:

  * Pure rule helpers (`build_deck`, `card_value`, `is_bust`, `dealer_should_hit`,
    `decide_winner`) contain no I/O and are deterministic -> unit testable.
  * `Hand` is a tiny data structure for the cards a player/dealer holds. It keeps
    the raw card labels (handy for a future "suits" feature) and a running total.
  * The interactive prompt helpers (`prompt_*`) are the only place that calls
    `input()`, so the rules above stay free of I/O.
  * The game-flow functions (`play_dealer_turn`, `play_player_decisions`,
    `settle`, `play_round`, `main`) wire everything together and print the
    distinct phases of a round.

Run it with:  python3 Blackjack/Blackjack.py
(Set the BLACKJACK_SEED env var to get a reproducible deal.)

Possible next steps that the structure now makes easy/local:
  * draw without replacement (remove the drawn card in `draw_card`),
  * let the dealer draw a fourth card (raise the dealer loop limit),
  * add betting / suits (extend `Hand`).
"""

import os
import random

# --------------------------------------------------------------------------- #
# Rules / constants  (pure, no I/O)
# --------------------------------------------------------------------------- #

RANKS = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
COPIES_PER_RANK = 4

BLACKJACK = 21            # going above this is a bust
DEALER_HIT_BELOW = 15     # dealer draws one extra card while its total is below this
MAX_PLAYER_CARDS = 4      # 2 dealt + up to 2 hits (matches the original game's cap)
ACE_LOW, ACE_HIGH = 1, 11

WINNER_PLAYER = 'player'
WINNER_DEALER = 'dealer'


def build_deck():
    """Return a fresh 52-card deck: four copies of each rank."""
    return [rank for rank in RANKS for _ in range(COPIES_PER_RANK)]


def card_value(card, ace_value=ACE_HIGH):
    """Numeric Blackjack value of a single card.

    Aces are worth ``ace_value`` (1 or 11 - chosen by the player at the table);
    J/Q/K are worth 10; number cards are worth their face value.
    """
    if card == 'A':
        return ace_value
    if card in ('J', 'Q', 'K'):
        return 10
    return int(card)


def is_bust(total):
    """True if a hand total has gone over 21."""
    return total > BLACKJACK


def dealer_should_hit(total, threshold=DEALER_HIT_BELOW):
    """The dealer takes one more card while its total is below ``threshold``."""
    return total < threshold


def decide_winner(player_total, dealer_total):
    """Decide the winner of a settled round.

    A bust always loses (the player's bust is checked first, matching the
    original behaviour); otherwise the higher total wins and the dealer takes
    ties.
    """
    if is_bust(player_total):
        return WINNER_DEALER
    if is_bust(dealer_total):
        return WINNER_PLAYER
    if player_total > dealer_total:
        return WINNER_PLAYER
    return WINNER_DEALER


# --------------------------------------------------------------------------- #
# Hand data structure
# --------------------------------------------------------------------------- #

class Hand:
    """The cards held by a player or the dealer, plus their running total."""

    def __init__(self):
        self.cards = []   # raw labels, e.g. ['A', 10, 'K'] - kept for display/future use
        self.total = 0

    def add(self, card, value):
        """Add ``card`` (already resolved to ``value``) to the hand."""
        self.cards.append(card)
        self.total += value

    def is_bust(self):
        return is_bust(self.total)

    def describe(self):
        return ', '.join(str(card) for card in self.cards)


# --------------------------------------------------------------------------- #
# Card drawing (with replacement - same as the original game)
# --------------------------------------------------------------------------- #

def draw_card(deck, rng=random):
    """Draw a random card from ``deck`` (with replacement)."""
    return deck[rng.randrange(len(deck))]


# --------------------------------------------------------------------------- #
# Interactive prompts  (the only place we read from the user)
# --------------------------------------------------------------------------- #

def _ask(prompt='?> '):
    return input(prompt).strip().lower()


def prompt_ace_value(card='A'):
    """Ask the player whether an Ace should count as 1 or 11."""
    while True:
        print('You got an Ace! Do you choose a value of 1 or 11?')
        choice = _ask()
        if choice == '1':
            return ACE_LOW
        if choice == '11':
            return ACE_HIGH
        print('Please choose one of the options!')


def prompt_hit_or_stick():
    """Ask the player to hit or stick; keep asking until it's valid."""
    while True:
        choice = _ask('Hit, or stick? ')
        if choice in ('hit', 'stick'):
            return choice
        print('Please choose "hit" or "stick"!')


def prompt_play_again():
    """Ask whether the player wants another round. Returns True/False."""
    while True:
        print('Would you like to play again?')
        choice = _ask()
        if choice in ('yes', 'y'):
            return True
        if choice in ('no', 'n'):
            return False
        print('Please choose one of the options!')


def resolve_card_value(card):
    """Turn a drawn ``card`` into its numeric value, prompting for Aces."""
    if card == 'A':
        return prompt_ace_value(card)
    return card_value(card)


def _deal_to(hand, deck, message, rng=random):
    """Draw a card, announce it, resolve its value and add it to ``hand``."""
    card = draw_card(deck, rng)
    print(message.format(card=card))
    hand.add(card, resolve_card_value(card))
    return card


# --------------------------------------------------------------------------- #
# Game flow
# --------------------------------------------------------------------------- #

def deal_opening_hand(deck, rng=random):
    """Deal the player's two opening cards and report the total."""
    print('--- New round ---')
    player = Hand()
    for _ in range(2):
        _deal_to(player, deck, 'You were dealt a {card}', rng)
    print('The value of your hand is {}'.format(player.total))
    return player


def play_dealer_turn(deck, rng=random):
    """Play the dealer's hand: two cards, plus one more while below the threshold."""
    print("--- Dealer's turn ---")
    dealer = Hand()
    for _ in range(2):
        _deal_to(dealer, deck, 'Dealer drew a {card}', rng)
    print("The value of the dealer's hand is {}".format(dealer.total))

    if dealer_should_hit(dealer.total):
        _deal_to(dealer, deck, 'Dealer draws another card: {card}', rng)
        print("The value of the dealer's hand is now {}".format(dealer.total))
    return dealer


def play_player_decisions(player, deck, rng=random):
    """Let the player hit (up to the card cap) or stick. Mutates ``player``."""
    print('--- Your turn ---')
    while len(player.cards) < MAX_PLAYER_CARDS:
        if prompt_hit_or_stick() == 'stick':
            print('Stick, got it.')
            return
        _deal_to(player, deck, 'Another card for you: {card}', rng)
        print('The value of your hand is now {}'.format(player.total))
        if player.is_bust():
            print('Bust! Too bad.')
            return


def settle(player, dealer):
    """Print the final hands and announce the winner."""
    print('--- Result ---')
    print('Your hand:   {} (value {})'.format(player.describe(), player.total))
    print('Dealer hand: {} (value {})'.format(dealer.describe(), dealer.total))
    winner = decide_winner(player.total, dealer.total)
    print('You win!' if winner == WINNER_PLAYER else 'Dealer wins!')
    return winner


def play_round(rng=random):
    """Play a single round and return the winner (WINNER_PLAYER/WINNER_DEALER)."""
    deck = build_deck()

    player = deal_opening_hand(deck, rng)

    dealer = play_dealer_turn(deck, rng)
    if dealer.is_bust():
        print('Dealer is bust! You win!')
        return WINNER_PLAYER

    play_player_decisions(player, deck, rng)
    return settle(player, dealer)


def main():
    """Play rounds until the player decides to stop."""
    seed = os.environ.get('BLACKJACK_SEED')
    if seed is not None:
        random.seed(int(seed))

    while True:
        play_round()
        if not prompt_play_again():
            print('Thanks for playing!')
            break
        print('')


if __name__ == '__main__':
    main()
