import random


def create_deck():
    """Return a fresh 52-card deck (4 of each rank)."""
    ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
    return [card for card in ranks for _ in range(4)]


def deal_card(deck):
    """Draw one random card from the deck and remove it."""
    if not deck:
        raise RuntimeError("Deck is empty — cannot deal.")
    idx = random.randint(0, len(deck) - 1)
    return deck.pop(idx)


def card_numeric_value(card):
    """Return the base numeric value of a non-Ace card. Ace returns 11 (caller adjusts)."""
    if card in ('J', 'Q', 'K', 'A'):
        return 11 if card == 'A' else 10
    return card


def prompt_ace_value(current_total):
    """Ask the player to choose 1 or 11 for an Ace. Hint if 11 would bust."""
    while True:
        if current_total + 11 > 21:
            print('  You drew an Ace! (Choosing 11 would bust — only 1 is safe.)')
        else:
            print('  You drew an Ace! Choose its value: 1 or 11?')
        choice = input('  ?> ').strip()
        if choice == '1':
            return 1
        if choice == '11':
            return 11
        print('  Please enter 1 or 11.')


def compute_dealer_total(cards):
    """Compute dealer hand total. Each Ace counts as 11 if it keeps total <= 21, else 1."""
    total = 0
    aces = 0
    for card in cards:
        if card == 'A':
            aces += 1
        else:
            total += card_numeric_value(card)
    for _ in range(aces):
        if total + 11 <= 21:
            total += 11
        else:
            total += 1
    return total


def add_card_to_player_hand(deck, player_cards, player_total):
    """Draw a card for the player, handle Ace prompt, update total. Returns new total."""
    card = deal_card(deck)
    player_cards.append(card)
    print(f'  You drew: {card}')
    if card == 'A':
        value = prompt_ace_value(player_total)
        player_total += value
    else:
        player_total += card_numeric_value(card)
    return player_total


def settle(player_total, dealer_total):
    """Print final result and return one of: 'win', 'lose', 'push'."""
    print('')
    print('=' * 32)
    print('           RESULTS')
    print('=' * 32)
    print(f'  Your total  : {player_total}')
    print(f'  Dealer total: {dealer_total}')

    if player_total > 21 and dealer_total > 21:
        print('  Both bust — push (tie)!')
        return 'push'
    if dealer_total > 21:
        print('  Dealer busts! You win!')
        return 'win'
    if player_total > 21:
        print('  Bust! You lose.')
        return 'lose'
    if player_total > dealer_total:
        print('  You win!')
        return 'win'
    if dealer_total > player_total:
        print('  Dealer wins!')
        return 'lose'
    print('  Push — it\'s a tie!')
    return 'push'


def play_game():
    """Run a single round of Blackjack."""
    deck = create_deck()

    # --- Deal player's first two cards ---
    print('Dealing your cards...')
    player_cards = []
    player_total = 0
    for _ in range(2):
        player_total = add_card_to_player_hand(deck, player_cards, player_total)
    print(f'  Your hand: {player_cards}  (total: {player_total})')

    # --- Deal dealer's first two cards (hidden from player, just reveal first) ---
    dealer_cards = [deal_card(deck) for _ in range(2)]
    print(f'  Dealer shows: {dealer_cards[0]}  (one card hidden)')

    dealer_total = compute_dealer_total(dealer_cards)

    # --- Early termination: natural blackjack ---
    if player_total == 21 and dealer_total == 21:
        print(f'  Both have Blackjack!')
        settle(player_total, dealer_total)
        return
    if player_total == 21:
        print('  Blackjack!')
        settle(player_total, dealer_total)
        return
    if dealer_total == 21:
        print(f'  Dealer has Blackjack!')
        settle(player_total, dealer_total)
        return

    # --- Player's turn: hit or stick loop ---
    while True:
        if player_total > 21:
            print(f'  Bust! Your total is {player_total}.')
            break

        action = input('  Hit or stick? > ').strip().lower()
        if action == 'hit':
            player_total = add_card_to_player_hand(deck, player_cards, player_total)
            print(f'  Your hand: {player_cards}  (total: {player_total})')
        elif action == 'stick':
            print(f'  You stick with {player_total}.')
            break
        else:
            print('  Please type "hit" or "stick".')

    # --- Dealer's turn: hit until total >= 17 ---
    print('')
    print(f'  Dealer reveals: {dealer_cards}')
    dealer_total = compute_dealer_total(dealer_cards)
    print(f'  Dealer total: {dealer_total}')

    while dealer_total < 17:
        card = deal_card(deck)
        dealer_cards.append(card)
        dealer_total = compute_dealer_total(dealer_cards)
        print(f'  Dealer drew: {card}  (total: {dealer_total})')

    # --- Settlement ---
    settle(player_total, dealer_total)


def main():
    """Main loop: play rounds until the player quits."""
    print('=== Welcome to Blackjack ===')
    while True:
        print('')
        play_game()
        print('')
        while True:
            again = input('Play again? (yes/no) > ').strip().lower()
            if again in ('yes', 'no'):
                break
            print('Please type "yes" or "no".')
        if again == 'no':
            print('Thanks for playing!')
            break


if __name__ == '__main__':
    main()
