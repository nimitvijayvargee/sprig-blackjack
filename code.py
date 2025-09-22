import time, random
import board, digitalio, displayio, terminalio
from adafruit_display_text import label

display = board.DISPLAY

# --- Buttons ---
def init_buttons():
    buttons = {}
    for name in ["W","A","S","D","I","J","K","L"]:
        b = digitalio.DigitalInOut(getattr(board, f"BUTTON_{name}"))
        b.direction = digitalio.Direction.INPUT
        b.pull = digitalio.Pull.UP
        buttons[name] = b
    return buttons

buttons = init_buttons()

# --- Load Suit Bitmaps ---
suits_bmp = {
    "♥": displayio.OnDiskBitmap("/suitsbmp/heart.bmp"),
    "♦": displayio.OnDiskBitmap("/suitsbmp/diamond.bmp"),
    "♣": displayio.OnDiskBitmap("/suitsbmp/club.bmp"),
    "♠": displayio.OnDiskBitmap("/suitsbmp/spade.bmp"),
}

# --- Calculate hand total ---
def calculate_hand(cards):
    total, aces = 0, 0
    for c in cards:
        rank = c.split(" ")[0]
        if rank == "A":
            total += 11
            aces += 1
        elif rank in ["J","Q","K"]:
            total += 10
        else:
            total += int(rank)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total

# --- Shuffle deck ---
def shuffle_deck(deck):
    for i in range(len(deck)-1,0,-1):
        j = random.randint(0,i)
        deck[i], deck[j] = deck[j], deck[i]
    return deck

# --- Draw a card ---
def draw_card(group, rank, suit, x, y):
    group.append(label.Label(terminalio.FONT, text="[", color=0xFFFFFF, x=x, y=y))
    group.append(label.Label(terminalio.FONT, text=rank, color=0xFFFFFF, x=x+6, y=y))
    bmp = None
    if suit is not None: bmp = suits_bmp[suit]

    if rank == "10":
        if bmp is not None: group.append(displayio.TileGrid(bmp, pixel_shader=bmp.pixel_shader, x=x+18, y=y-4))
        group.append(label.Label(terminalio.FONT, text="]", color=0xFFFFFF, x=x+26, y=y))
        return x + 30  # next card position
    else:
        if bmp is not None: group.append(displayio.TileGrid(bmp, pixel_shader=bmp.pixel_shader, x=x+12, y=y-4))
        group.append(label.Label(terminalio.FONT, text="]", color=0xFFFFFF, x=x+20, y=y))
        return x + 24  # next card position

# --- Draw a hand ---
def draw_hand(prefix, cards, y, max_cards_per_row=2):
    group = displayio.Group()
    x = 5
    # prefix
    if prefix == "Dealer: ":
        color = 0xFFAAAA
    else:
        color = 0xAAAAFF
    group.append(label.Label(terminalio.FONT, text=prefix, color=color, x=x, y=y))
    x += len(prefix)*6
    count = 0
    for c in cards:
        rank, suit = c.split(" ")
        x = draw_card(group, rank, suit, x, y)
        count += 1
        if count >= max_cards_per_row:
            count = 0
            y += 12
            x = len(prefix)*6 +5
    return group, y+12

# --- Draw Screen from group ---
def draw_screen(group):
    group.append(label.Label(terminalio.FONT, text=f"Total Wins: {current_wins}", color=0xAAFFAA, x=5, y=120))
    display.root_group = group
    
current_wins = 0

# --- Main game loop ---
while True:
    # build and shuffle deck
    ranks = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]
    suits = ["♥","♦","♣","♠"]
    deck = [r+" "+s for r in ranks for s in suits]
    print(deck)
    shuffle_deck(deck)

    dealer_cards = [deck.pop(), deck.pop()]
    player_cards = [deck.pop(), deck.pop()]
    print(player_cards, dealer_cards)
    # initial display
    group = displayio.Group()
    y = 10
    group.append(label.Label(terminalio.FONT, text="Blackjack on da Sprig", color=0xAAFFAA, x=5, y=y))
    y += 12
    group.append(label.Label(terminalio.FONT, text="Dealer:", color=0xFFAAAA, x=5, y=y))
    card_x = draw_card(group, dealer_cards[0].split(" ")[0], dealer_cards[0].split(" ")[1], 54, y)
    card_x = draw_card(group, "??", None, card_x, y)
    y += 12
    hand_group, y = draw_hand("Player: ", player_cards, y)
    group.append(hand_group)
    group.append(label.Label(terminalio.FONT, text=f"Player sum: {calculate_hand(player_cards)}", color=0xAAAAFF, x=5, y=y))
    y+= 24
    group.append(label.Label(terminalio.FONT, text="D = Hit  J = Stand", color=0xAAAAAA, x=5, y=y))
    group.append(label.Label(terminalio.FONT, text="K = Restart after win/loss", color=0xAAAAAA, x=5, y=y+12))
    draw_screen(group)
    time.sleep(1)

    player_sum = calculate_hand(player_cards)

    # --- Player turn ---
    while True:
        if not buttons["D"].value:  # Hit
            player_cards.append(deck.pop())
            player_sum = calculate_hand(player_cards)
            group = displayio.Group()
            y = 10
            group.append(label.Label(terminalio.FONT, text="Player hits!", color=0xFFFFFF, x=5, y=y))
            y += 12
            group.append(label.Label(terminalio.FONT, text="Dealer:", color=0xFFAAAA, x=5, y=y))
            card_x = draw_card(group, dealer_cards[0].split(" ")[0], dealer_cards[0].split(" ")[1], 54, y)
            card_x = draw_card(group, "??", None, card_x, y)
            y += 12
            hand_group, y = draw_hand("Player: ", player_cards, y)
            group.append(hand_group)
            group.append(label.Label(terminalio.FONT, text=f"Player sum: {player_sum}", color=0xAAAAFF, x=5, y=y))
            draw_screen(group)
            time.sleep(0.5)
            if player_sum > 21:
                result = "Player busts! Dealer wins! Press K to restart"
                break
        elif not buttons["J"].value:  # Stand
            break
        time.sleep(0.1)

    if player_sum > 21:
        group = displayio.Group()
        y = 10
        group.append(label.Label(terminalio.FONT, text="Dealer:", color=0xFFAAAA, x=5, y=y))
        card_x = draw_card(group, dealer_cards[0].split(" ")[0], dealer_cards[0].split(" ")[1], 54, y)
        card_x = draw_card(group, "??", None, card_x, y)
        y += 12
        hand_group, y = draw_hand("Player: ", player_cards, y)
        group.append(hand_group)
        group.append(label.Label(terminalio.FONT, text=f"Player sum: {player_sum}", color=0xAAAAFF, x=5, y=y))
        y += 12  
        group.append(label.Label(terminalio.FONT, text=result, color=0xFFAAAA, x=5, y=y))
        group.append(label.Label(terminalio.FONT, text="Press K to restart", color=0xAAAAAA, x=5, y=y+12))
        draw_screen(group)

        while buttons["K"].value:
            pass
        time.sleep(0.3)
        continue

    # --- Dealer turn ---
    dealer_sum = calculate_hand(dealer_cards)
    while dealer_sum < 17:
        dealer_cards.append(deck.pop())
        dealer_sum = calculate_hand(dealer_cards)
        group = displayio.Group()
        y = 10
        hand_group, y = draw_hand("Dealer: ", dealer_cards, y)
        group.append(hand_group)
        hand_group2, y = draw_hand("Player: ", player_cards, y)
        group.append(hand_group2)
        draw_screen(group)
        time.sleep(0.5)

    # --- Determine result ---
    if (player_sum > dealer_sum or dealer_sum > 21) and player_sum <= 21:
        result = "Player wins!"
    elif (dealer_sum > player_sum or player_sum > 21) and dealer_sum <= 21:
        result = "Dealer wins!"
    else:
        result = "It's a tie!"

    # --- Display final hands and result ---
    group = displayio.Group()
    y = 10
    hand_group, y = draw_hand("Dealer: ", dealer_cards, y)
    group.append(hand_group)
    group.append(label.Label(terminalio.FONT, text=f"Dealer sum: {dealer_sum}", color=0xFFAAAA, x=5, y=y))
    y += 12
    hand_group2, y = draw_hand("Player: ", player_cards, y)
    group.append(hand_group2)
    group.append(label.Label(terminalio.FONT, text=f"Player sum: {player_sum}", color=0xAAAAFF, x=5, y=y))
    y += 12
    result_color = 0xFFFFFF
    if result == "Player wins!":
        current_wins += 1
        result_color = 0xAAFFAA
    elif result == "Dealer wins!":
        result_color = 0xFFAAAA
    elif result == "It's a tie!":
        result_color = 0xFFFFAA

    group.append(label.Label(terminalio.FONT, text=result, color=result_color, x=5, y=y))
    group.append(label.Label(terminalio.FONT, text="Press K to restart", color=0xAAAAAA, x=5, y=y+12))
    draw_screen(group)

    while buttons["K"].value:
        pass
    time.sleep(0.3)
