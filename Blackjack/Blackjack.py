"""
Blackjack - a simple terminal Blackjack game.

Structure
---------
- Deck helpers     : build a shuffled shoe, draw cards
- Pure game logic  : hand value, bust check, dealer policy, outcome
- I/O helpers      : prompts and display functions
- Round orchestration: deal_initial, player_turn, dealer_turn, settle
- main()           : top-level play-again loop
"""

import random

DEALER_HIT_THRESHOLD = 17  # Dealer draws until hand >= this value


# ---------------------------------------------------------------------------
# Deck
# ---------------------------------------------------------------------------

def build_deck():
    """Return a freshly shuffled 52-card shoe (4 copies of each rank)."""
    ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
    deck = [rank for rank in ranks for _ in range(4)]
    random.shuffle(deck)
    return deck


def draw(deck):
    """Pop and return the top card rank from *deck*."""
    return deck.pop()


def deal_initial(deck, n=2):
    """Draw *n* cards from *deck* and return them as a list of ranks."""
    return [draw(deck) for _ in range(n)]


# ---------------------------------------------------------------------------
# Pure game logic  (no I/O, easy to test)
# ---------------------------------------------------------------------------

def card_base_value(rank):
    """Return the default numeric value for a card rank.

    Ace defaults to 11; J/Q/K are 10; number cards keep their face value.
    """
    if rank == 'A':
        return 11
    if rank in ('J', 'Q', 'K'):
        return 10
    return int(rank)


def hand_value(cards):
    """Return the total value of a hand (list of resolved int values)."""
    return sum(cards)


def is_bust(cards):
    """Return True if the hand's value exceeds 21."""
    return hand_value(cards) > 21


def dealer_should_hit(cards):
    """Return True if the dealer must draw another card (hand < threshold)."""
    return hand_value(cards) < DEALER_HIT_THRESHOLD


def determine_outcome(player_cards, dealer_cards):
    """Return 'player_win', 'dealer_win', or 'push'.

    Assumes neither hand is bust — bust cases are handled before calling this.
    """
    pv, dv = hand_value(player_cards), hand_value(dealer_cards)
    if pv > dv:
        return 'player_win'
    if dv > pv:
        return 'dealer_win'
    return 'push'


def resolve_dealer_card(rank, current_hand):
    """Resolve a rank into a numeric value for the dealer.

    Aces count as 11 unless that would immediately bust the hand, in which
    case they count as 1.
    """
    if rank == 'A':
        return 11 if hand_value(current_hand) + 11 <= 21 else 1
    return card_base_value(rank)


# ---------------------------------------------------------------------------
# I/O helpers  (all user interaction is isolated here)
# ---------------------------------------------------------------------------

def ask_ace_value():
    """Prompt the player to choose an Ace value (1 or 11). Returns int."""
    while True:
        print('You got an Ace! Do you choose a value of 1 or 11?')
        choice = input('?> ').strip()
        if choice in ('1', '11'):
            return int(choice)
        print('Please choose one of the options!')


def ask_hit_or_stick():
    """Prompt the player for hit or stick. Returns 'hit' or 'stick'."""
    while True:
        print('Hit, or stick?')
        choice = input('?> ').strip().lower()
        if choice in ('hit', 'stick'):
            return choice
        print('Please choose one of the options!')


def ask_play_again():
    """Prompt the player to play another round. Returns bool."""
    while True:
        print('Would you like to play again? (yes/no)')
        choice = input('?> ').strip().lower()
        if choice in ('yes', 'no'):
            return choice == 'yes'
        print('Please choose one of the options!')


def display_card(label, rank):
    """Print a single card event, e.g. 'First card is a K'."""
    print(f'{label} card is a {rank}')


def display_hand_value(label, cards):
    """Print the current total of a hand, e.g. 'The value of your hand is 17'."""
    print(f'The value of {label} hand is {hand_value(cards)}')


# ---------------------------------------------------------------------------
# Card resolution (bridges I/O and logic)
# ---------------------------------------------------------------------------

def resolve_player_card(rank):
    """Resolve a rank into a numeric value for the player.

    Prompts the user when the rank is an Ace; face cards become 10.
    """
    if rank == 'A':
        return ask_ace_value()
    return card_base_value(rank)


# ---------------------------------------------------------------------------
# Round orchestration
# ---------------------------------------------------------------------------

def player_turn(deck, player_cards):
    """Run the player's turn: loop hit/stick until the player sticks or busts.

    Mutates *player_cards* in place.
    Returns True if the player is still in the game (not bust).
    """
    while True:
        choice = ask_hit_or_stick()
        if choice == 'stick':
            print('Stick, got it')
            display_hand_value('your', player_cards)
            return True

        rank = draw(deck)
        display_card('You drew a', rank)
        value = resolve_player_card(rank)
        player_cards.append(value)
        display_hand_value('your', player_cards)

        if is_bust(player_cards):
            print('Bust! Too bad.')
            return False


def dealer_turn(deck, dealer_cards):
    """Run the dealer's turn: draw until the hand reaches the threshold.

    Mutates *dealer_cards* in place.
    Returns True if the dealer is still in the game (not bust).
    """
    print("--- Dealer's turn ---")
    while dealer_should_hit(dealer_cards):
        rank = draw(deck)
        display_card('Dealer draws a', rank)
        value = resolve_dealer_card(rank, dealer_cards)
        dealer_cards.append(value)
        display_hand_value("dealer's", dealer_cards)

    if is_bust(dealer_cards):
        print('Dealer is bust!')
        return False
    return True


def settle(player_cards, dealer_cards):
    """Announce the final result of a round (neither side busted)."""
    display_hand_value('your', player_cards)
    display_hand_value("dealer's", dealer_cards)
    outcome = determine_outcome(player_cards, dealer_cards)
    if outcome == 'player_win':
        print('You win!')
    elif outcome == 'dealer_win':
        print('Dealer wins!')
    else:
        print("It's a push (tie)!")


def play_round():
    """Play one complete round of Blackjack."""
    deck = build_deck()

    # ── Initial deal ──────────────────────────────────────────────────────
    player_ranks = deal_initial(deck, 2)
    dealer_ranks = deal_initial(deck, 2)

    display_card('First', player_ranks[0])
    display_card('Second', player_ranks[1])

    # Resolve to numeric values
    player_cards = [resolve_player_card(r) for r in player_ranks]
    display_hand_value('your', player_cards)

    dealer_cards = []
    for rank in dealer_ranks:
        value = resolve_dealer_card(rank, dealer_cards)
        dealer_cards.append(value)
    display_hand_value("dealer's", dealer_cards)

    # ── Player turn ───────────────────────────────────────────────────────
    if not player_turn(deck, player_cards):
        # Player busted; round over.
        return

    # ── Dealer turn ───────────────────────────────────────────────────────
    if not dealer_turn(deck, dealer_cards):
        # Dealer busted; player wins.
        print('You win!')
        return

    # ── Showdown ──────────────────────────────────────────────────────────
    settle(player_cards, dealer_cards)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print('Welcome to Blackjack!')
    while True:
        print()
        play_round()
        if not ask_play_again():
            print('Thanks for playing!')
            break


if __name__ == '__main__':
    main()
