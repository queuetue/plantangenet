from plantangenet import GLOBAL_LOGGER
from .assets import Assets


class Brick:
    """
    Represents a brick in the breakout game.
    Holds position, size, and state (e.g., hit status).
    """

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hit = False  # True if the brick has been hit by the ball


class Ball:
    """
    Represents the ball in the breakout game.
    Holds position, velocity, and size.
    """

    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = 0  # Velocity in x direction
        self.vy = 0  # Velocity in y direction


class Bumper:
    """
    Represents the paddle in the breakout game.
    Holds position, size, and movement logic.
    """

    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.vx = 0  # Velocity in x direction (for paddle movement)


class LeftRightBehaviorBumper(Bumper):
    """
    A Bumper that moves repeatedly from left to right and back.
    This is a simple behavior for demonstration purposes.
    """

    def __init__(self, game, x, y, width, height, speed=5):
        super().__init__(x, y, width, height)
        self.speed = speed
        self.direction = 1  # 1 for right, -1 for left
        self.game = game

    def __rect__(self):
        """
        Returns the rectangle representation of the paddle for collision detection.
        """
        return (self.x, self.y, self.width, self.height)

    def update(self):
        # Move paddle left or right
        self.x += self.speed * self.direction
        # Reverse direction if hitting screen edges
        if self.game.border_collision(self):
            # Assuming game.border_collision checks if the paddle is at the edge of the screen
            self.direction *= -1


class GameState:
    """
    Represents the state of a breakout activity/game.
    Holds ball, paddle, bricks, and other game state.
    """

    def __init__(self):
        self.balls = []  # List of Ball objects
        self.bumpers = []  # List of Bumper objects
        self.bricks = []  # List of Brick objects
        self.score = 0
        self.lives = 3
        # Add more state as needed


class Game():
    """
    Represents a breakout game instance (board).
    Manages game state, physics, and rules.
    """

    def __init__(self, namespace, logger=None, benchmark_mode=False):
        self.width = 800  # Example game width
        self.height = 600  # Example game height
        self.namespace = namespace
        self.state = GameState()
        self.__ocean_logger = logger or GLOBAL_LOGGER
        self.benchmark_mode = benchmark_mode
        # Add more initialization as needed

    async def update(self):
        # Implement game update logic (move ball, check collisions, etc.)
        pass

    def border_collision(self, rect):
        """
        Check if the paddle collides with the game borders.
        Returns True if it collides, False otherwise.
        """
        if rect.x < 0 or rect.x + rect.width > self.width:
            return True
        if rect.y < 0 or rect.y + rect.height > self.height:
            return True
        return False
