import tkinter as tk
from tkinter import messagebox
import random

ROWS, COLS = 10, 10
CARD_SUITS = ['♠', '♥', '♦', '♣']
CARD_RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
CARDS = [r + s for r in CARD_RANKS for s in CARD_SUITS]

DECK = CARDS * 2
random.seed(42)
non_corner_positions = 96
CARDS_NO_JACKS = [r + s for r in CARD_RANKS if r != 'J' for s in CARD_SUITS]
DECK_NO_JACKS = CARDS_NO_JACKS * 2

BOARD_CARDS = random.sample(DECK_NO_JACKS, non_corner_positions)

grid = [['' for _ in range(COLS)] for _ in range(ROWS)]
idx = 0
for r in range(ROWS):
    for c in range(COLS):
        if (r, c) in [(0,0), (0,COLS-1), (ROWS-1,0), (ROWS-1,COLS-1)]:
            continue
        grid[r][c] = BOARD_CARDS[idx]
        idx += 1


print("Board cards:", BOARD_CARDS)
print(len(BOARD_CARDS), "cards in the deck.")
class SequenceGame:
    def __init__(self, num_players=2, board_layout=None):
        # split board layout into 10×10 grid
        self.boards = {
            'A': [row.copy() for row in board_layout],
            'B': [row.copy() for row in board_layout]
        }   
        # empty occupancy states
        self.states = { b: [['' for _ in range(COLS)] for _ in range(ROWS)]
                        for b in self.boards }
        # Set corners as wild (occupied by 'wild' — not a real player)
        for b in self.states:
            self.states[b][0][0] = 'wild'
            self.states[b][0][COLS-1] = 'wild'
            self.states[b][ROWS-1][0] = 'wild'
            self.states[b][ROWS-1][COLS-1] = 'wild'

        # players & colors
        base = ['P1','P2','P3','P4'][:num_players]
        palette = ['blue','red','green','purple']
        self.players = base
        self.colors = {p: palette[i] for i,p in enumerate(base)}
        self.current = 0

        # deal hands
        self.deck = DECK.copy()
        random.shuffle(self.deck)
        self.hands = { p: [self.deck.pop() for _ in range(7)] for p in self.players }

    def play_card(self, player, card, board_id, r, c):
        """Attempt to play `card` on boards[board_id][r][c]."""
        # 1. Ownership
        if card not in self.hands[player]:
            return False, "You don't have that card."
        layout = self.boards[board_id]
        state  = self.states[board_id]

        # Block wild corner usage
        if (r, c) in [(0,0), (0,COLS-1), (ROWS-1,0), (ROWS-1,COLS-1)]:
            return False, "Cannot play on a wild corner."

        # 2. Cell free unless removal
        if state[r][c] and not (card.startswith('J') and card.endswith(('♥','♣'))):
            return False, "Cell already occupied."

        # 3. Non-Jack must match layout
        if not card.startswith('J'):
            if layout[r][c] != card:
                return False, "Card doesn't match that spot."
            state[r][c] = player

        else:
            # Two-eyed Jacks (♠, ♦) are wild → place on any empty
            if card.endswith(('♠','♦')):
                if state[r][c] == '':
                    state[r][c] = player
                else:
                    return False, "Cell already occupied."

            # One-eyed Jacks (♥, ♣) remove opponent's marker
            else:
                if state[r][c] not in ['', player, 'wild']:
                    state[r][c] = ''
                else:
                    return False, "Must remove an opponent’s marker."


        # 4. Remove from hand, draw new if possible
        self.hands[player].remove(card)
        if self.deck:
            self.hands[player].append(self.deck.pop())
        return True, "Move OK."

    def next_player(self):
        self.current = (self.current + 1) % len(self.players)


class SequenceGUI:
    def __init__(self, root, num_players=2):
        self.root = root
        self.root.title("Dual Sequence")
        self.game = SequenceGame(num_players, board_layout=grid)
        self.selected = None
        self.last_btn = None

        self.info = tk.Label(root, text="")
        self.info.pack(pady=5)

        self.hand_frame = tk.Frame(root)
        self.hand_frame.pack(pady=5)
        self.card_btns = [
            tk.Button(self.hand_frame, text="", width=5,
                      command=lambda i=i: self.select_card(i))
            for i in range(7)
        ]
        for b in self.card_btns:
            b.pack(side=tk.LEFT, padx=2)

        # Boards A & B
        self.btns = {}  # btns['A',r,c] → Button
        for bid in ['A','B']:
            frame = tk.LabelFrame(root, text=f"Board {bid}")
            frame.pack(side=tk.LEFT, padx=10)
            for r in range(ROWS):
                for c in range(COLS):
                    b = tk.Button(frame, text=self.game.boards[bid][r][c],
                                  width=4, height=2,
                                  command=lambda r=r,c=c,bid=bid: self.on_click(bid,r,c))
                    b.grid(row=r, column=c, padx=1, pady=1)
                    self.btns[(bid,r,c)] = b
        any_btn = next(iter(self.btns.values()))
        self.default_bg = any_btn.cget('bg')
        self.default_active = any_btn.cget('activebackground')
        self.refresh()

    def select_card(self, idx):
        p = self.game.players[self.game.current]
        hand = self.game.hands[p]
        if idx >= len(hand):
            return
        self.selected = hand[idx]
        self.info.config(text=f"{p} selected {self.selected}")
        self.show_highlights()

    def show_highlights(self):
        """Color valid cells yellow or orange depending on the move."""
        self.clear_highlights()

        p = self.game.players[self.game.current]
        card = self.selected
        if not card:
            return

        for bid in ['A','B']:
            layout = self.game.boards[bid]
            state  = self.game.states[bid]
            for r in range(ROWS):
                for c in range(COLS):
                    btn = self.btns[(bid,r,c)]
                    print(f"Checking {bid} {r},{c} for {card}")
                    if card.startswith('J'):
                        # Two-eyed Jacks: place on any empty cell
                        if card.endswith(('♠','♦')) and state[r][c] == '':
                            btn.config(bg='yellow', activebackground='yellow')
                        # One-eyed Jacks: remove opponent marker
                    elif card.endswith(('♥','♣')) and state[r][c] not in ['', p, 'wild']:
                        btn.config(bg='orange', activebackground='orange')

                    else:
                        if layout[r][c] == card and state[r][c] == '':
                            print(f"Highlighting {bid} {r},{c} for {card}")
                            btn.config(bg='#FFD700', activebackground='#FFD700', highlightthickness=3, 
                                       highlightbackground='yellow', highlightcolor='yellow')


    def on_click(self, board_id, r, c):
        p = self.game.players[self.game.current]
        
        if not self.selected:
            messagebox.showwarning("No Card", "Select a card first.")
            return

        self.clear_highlights()

        ok, msg = self.game.play_card(p, self.selected, board_id, r, c)
        if not ok:
            messagebox.showerror("Invalid Move", msg)
            return

        # 1) clear the old border
        if self.last_btn:
            self.last_btn.config(highlightthickness=0)

        # 2) highlight only if not a one-eyed Jack (♥, ♣)
        if not (self.selected.startswith('J') and self.selected.endswith(('♥', '♣'))):
            btn = self.btns[(board_id, r, c)]
            player_color = self.game.colors[p]
            btn.config(
                highlightthickness=3,
                highlightbackground=player_color,
                highlightcolor=player_color
            )
            self.last_btn = btn
        else:
            self.last_btn = None  # Don’t retain highlight

        # 3) Finish the turn
        self.selected = None
        self.game.next_player()
        self.refresh()



    def clear_highlights(self):
        """Reset all non-occupied cells to default."""
        for (bid, r, c), btn in self.btns.items():
            owner = self.game.states[bid][r][c]
            if owner == 'wild':
                btn.config(bg='black', fg='white', state=tk.DISABLED)
            elif owner:
                col = self.game.colors[owner]
                btn.config(bg=col, activebackground=col)
            else:
                btn.config(bg=self.default_bg,
                        activebackground=self.default_active,
                        fg='black', state=tk.NORMAL)


    def refresh(self):
        """Update info label, hand buttons, and board btn colors."""
        p = self.game.players[self.game.current]
        self.info.config(text=f"{p}'s turn")
        
        # Hand
        hand = self.game.hands[p]
        for i, btn in enumerate(self.card_btns):
            if i < len(hand):
                btn.config(text=hand[i], bg='white', state=tk.NORMAL)
            else:
                btn.config(text='', bg='SystemButtonFace', state=tk.DISABLED)

        # Boards
        for (bid, r, c), btn in self.btns.items():
            owner = self.game.states[bid][r][c]
            if owner == 'wild':
                btn.config(bg='black', fg='white', state=tk.DISABLED)
            elif owner:
                col = self.game.colors[owner]
                btn.config(bg=col, activebackground=col, fg='black', state=tk.NORMAL)
            else:
                btn.config(bg=self.default_bg,
                        activebackground=self.default_active,
                        fg='black', state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    SequenceGUI(root, num_players=2)
    root.mainloop()
