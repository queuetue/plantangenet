class TurnHelper:
    """
    Utility class for managing turn order, current player, and turn transitions in games.
    """

    def __init__(self, players):
        self.players = list(players)
        self.current_index = 0
        self.turn_count = 0

    def current_player(self):
        if not self.players:
            return None
        return self.players[self.current_index]

    def next_turn(self):
        if not self.players:
            return None
        self.current_index = (self.current_index + 1) % len(self.players)
        self.turn_count += 1
        return self.current_player()

    def previous_turn(self):
        if not self.players:
            return None
        self.current_index = (self.current_index - 1) % len(self.players)
        self.turn_count = max(0, self.turn_count - 1)
        return self.current_player()

    def skip_player(self, player):
        """Skip a specific player's turn"""
        if player in self.players:
            player_index = self.players.index(player)
            if player_index == self.current_index:
                self.next_turn()

    def reset(self):
        self.current_index = 0
        self.turn_count = 0

    def add_player(self, player):
        if player not in self.players:
            self.players.append(player)

    def remove_player(self, player):
        if player in self.players:
            player_index = self.players.index(player)
            self.players.remove(player)
            # Adjust current index if necessary
            if player_index < self.current_index:
                self.current_index -= 1
            elif player_index == self.current_index and self.players:
                self.current_index = self.current_index % len(self.players)

    def get_turn_order(self):
        """Get the full turn order starting from current player"""
        if not self.players:
            return []
        return self.players[self.current_index:] + self.players[:self.current_index]
