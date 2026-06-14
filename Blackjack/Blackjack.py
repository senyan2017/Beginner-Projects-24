import random


def create_deck():
    """Create a standard 52-card deck."""
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    ranks = ['A', 2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K']
    return [(rank, suit) for rank in ranks for suit in suits]


def card_display(card):
    """Return a human-readable string for a card."""
    rank, suit = card
    return f"{rank} of {suit}"


def card_base_value(card):
    """Return the base numeric value of a card (Ace counted as 1)."""
    rank = card[0]
    if rank == 'A':
        return 1
    elif rank in ('J', 'Q', 'K'):
        return 10
    else:
        return int(rank)


def hand_value(cards):
    """Calculate hand value, automatically counting Aces as 11 when possible."""
    total = sum(card_base_value(c) for c in cards)
    aces = sum(1 for c in cards if c[0] == 'A')
    # Upgrade Aces from 1 to 11 where it won't bust
    for _ in range(aces):
        if total + 10 <= 21:
            total += 10
    return total


def compute_player_total(non_ace_sum, ace_values):
    """Compute player total from non-ace sum and list of chosen ace values."""
    return non_ace_sum + sum(ace_values)


def ask_ace_value(card):
    """Ask the player to choose 1 or 11 for a single Ace. Returns chosen value."""
    print(f'  You drew an Ace ({card_display(card)})! Count it as 1 or 11?')
    while True:
        choice = input('  ?> ').strip()
        if choice == '11':
            return 11
        elif choice == '1':
            return 1
        else:
            print('  Please enter 1 or 11.')


def get_bet(balance):
    """Prompt the player for a valid bet amount."""
    while True:
        print(f'Your balance: ${balance}')
        print('How much would you like to bet?')
        raw = input('?> ').strip()
        try:
            bet = int(raw)
        except ValueError:
            print('Please enter a valid number.')
            continue
        if bet <= 0:
            print('Bet must be greater than zero.')
        elif bet > balance:
            print(f'You only have ${balance}. Bet a smaller amount.')
        else:
            return bet


def deal_card(deck):
    """Draw one card from the deck (removes it). Returns the card."""
    return deck.pop(random.randint(0, len(deck) - 1))


def dealer_play(deck, dealer_cards):
    """Dealer draws until hand value >= 17. Returns final cards list."""
    while hand_value(dealer_cards) < 17:
        card = deal_card(deck)
        dealer_cards.append(card)
        print(f'  Dealer draws: {card_display(card)}')
    return dealer_cards


def print_round_summary(player_cards, dealer_cards, player_total, dealer_total,
                        bet, result, balance):
    """Print a summary of the round."""
    print('\n' + '=' * 44)
    print('  ROUND SUMMARY')
    print('=' * 44)
    print(f'  Your cards:   {", ".join(card_display(c) for c in player_cards)}')
    print(f'  Your total:   {player_total}')
    print(f'  Dealer cards: {", ".join(card_display(c) for c in dealer_cards)}')
    print(f'  Dealer total: {dealer_total}')
    print(f'  Bet:          ${bet}')
    print(f'  Result:       {result}')
    print(f'  Balance:      ${balance}')
    print('=' * 44 + '\n')


def play_round(balance):
    """Play one round of Blackjack. Returns (new_balance, keep_playing)."""
    # --- Betting ---
    bet = get_bet(balance)
    print(f'You bet ${bet}.\n')

    # --- Create and shuffle deck ---
    deck = create_deck()
    random.shuffle(deck)

    # --- Deal initial cards ---
    player_cards = [deal_card(deck), deal_card(deck)]
    dealer_cards = [deal_card(deck), deal_card(deck)]

    # Show dealer's up-card only
    print(f'Dealer shows: {card_display(dealer_cards[0])}')
    print(f'Your cards:   {card_display(player_cards[0])}, {card_display(player_cards[1])}')

    # --- Build player hand value, tracking Ace choices ---
    non_ace_sum = 0
    ace_values = []
    for c in player_cards:
        if c[0] == 'A':
            ace_values.append(ask_ace_value(c))
        else:
            non_ace_sum += card_base_value(c)

    player_total = compute_player_total(non_ace_sum, ace_values)
    print(f'Your hand value: {player_total}\n')

    # Check for natural blackjack
    player_blackjack = (player_total == 21 and len(player_cards) == 2)

    # --- Player turn: hit or stick ---
    busted = False
    if not player_blackjack:
        while True:
            print('Hit or stick?')
            choice = input('?> ').strip().lower()
            if choice == 'hit':
                card = deal_card(deck)
                player_cards.append(card)
                print(f'You drew: {card_display(card)}')

                if card[0] == 'A':
                    ace_values.append(ask_ace_value(card))
                else:
                    non_ace_sum += card_base_value(card)

                player_total = compute_player_total(non_ace_sum, ace_values)
                print(f'Your hand value: {player_total}\n')

                if player_total > 21:
                    print('Bust! You went over 21.')
                    busted = True
                    break
            elif choice == 'stick':
                print(f'You stick with {player_total}.\n')
                break
            else:
                print('Please type "hit" or "stick".')

    # --- Dealer turn ---
    print("--- Dealer's turn ---")
    print(f'Dealer reveals: {card_display(dealer_cards[1])}')

    if player_blackjack:
        print('You got a Blackjack!')
        dealer_cards = dealer_play(deck, dealer_cards)
        dealer_total = hand_value(dealer_cards)
        if dealer_total == 21 and len(dealer_cards) == 2:
            result = 'Push (both Blackjack)'
            balance += 0  # bet returned
        else:
            result = 'Blackjack! You win!'
            balance += int(bet * 1.5)  # 3:2 payout
    elif busted:
        dealer_total = hand_value(dealer_cards)
        # Still reveal dealer cards for summary
        result = 'You lose (bust)'
        balance -= bet
    else:
        dealer_cards = dealer_play(deck, dealer_cards)
        dealer_total = hand_value(dealer_cards)

        if dealer_total > 21:
            result = 'Dealer busts! You win!'
            balance += bet
        elif player_total > dealer_total:
            result = 'You win!'
            balance += bet
        elif player_total < dealer_total:
            result = 'Dealer wins'
            balance -= bet
        else:
            result = 'Push (tie)'
            # bet returned, no change

    # --- Round summary ---
    print_round_summary(player_cards, dealer_cards, player_total, dealer_total,
                        bet, result, balance)

    # --- Play again? ---
    if balance <= 0:
        print('You are out of money! Game over.')
        return balance, False

    print('Play another round? (yes/no)')
    while True:
        answer = input('?> ').strip().lower()
        if answer in ('yes', 'y'):
            return balance, True
        elif answer in ('no', 'n'):
            print(f'You walk away with ${balance}. Thanks for playing!')
            return balance, False
        else:
            print('Please type yes or no.')


def main():
    print('Welcome to Blackjack!\n')
    balance = 1000
    keep_playing = True
    round_num = 0
    while keep_playing:
        round_num += 1
        print(f'\n{"#" * 44}')
        print(f'  Round {round_num}')
        print(f'{"#" * 44}\n')
        balance, keep_playing = play_round(balance)


if __name__ == '__main__':
    main()
