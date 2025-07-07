from typing import Self
from pyparsing import Any


class Line():
    """
    Protocol for a line-like object.
    This is used to define the interface for objects that can be represented as lines.
    """

    def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """
        Initialize the line with start point (x1, y1) and end point (x2, y2).
        """
        self._line_x1 = x1
        self._line_y1 = y1
        self._line_x2 = x2
        self._line_y2 = y2

    def copy(self) -> Self:
        """
        Copy the line.
        """
        return self.__class__(self._line_x1, self._line_y1, self._line_x2, self._line_y2)


class Rect():
    """
    Protocol for a rectangle-like object.
    This is used to define the interface for objects that can be represented as rectangles.
    """

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        """
        Initialize the rectangle with position (x, y) and size (width, height).
        """
        self._rect_x = x
        self._rect_y = y
        self._rect_width = width
        self._rect_height = height

    def copy(self) -> Self:
        """
        Copy the rectangle.
        """
        return self.__class__(self._rect_x, self._rect_y, self._rect_width, self._rect_height)

    def move(self, dx: float, dy: float) -> None:
        """
        Move the rectangle by (dx, dy).
        """
        self._rect_x += dx
        self._rect_y += dy

    def inflate(self, dwidth: float, dheight: float) -> None:
        """
        Grow or shrink the rectangle size.

        """
        self._rect_width += dwidth
        self._rect_height += dheight

    def scale(self, factor: float) -> None:
        """
        Scale the rectangle by a given multiplier.
        """
        if factor <= 0:
            raise ValueError("Scale factor must be positive")
        self._rect_width *= factor
        self._rect_height *= factor

    def update(self, x: float, y: float, width: float, height: float) -> None:
        """
        Set the position and size of the rectangle.
        """
        self._rect_x = x
        self._rect_y = y
        self._rect_width = width
        self._rect_height = height

    def clamp(self, other: Any) -> None:
        """
        Moves the rectangle inside another.
        """
        if not isinstance(other, Rect):
            try:
                other = other.__rect__
            except AttributeError:
                raise TypeError("clip requires another Rect-like object")
        if self._rect_x < other._rect_x:
            self._rect_x = other._rect_x
        if self._rect_y < other._rect_y:
            self._rect_y = other._rect_y
        if self._rect_x + self._rect_width > other._rect_x + other._rect_width:
            self._rect_x = other._rect_x + other._rect_width - self._rect_width
        if self._rect_y + self._rect_height > other._rect_y + other._rect_height:
            self._rect_y = other._rect_y + other._rect_height - self._rect_height

    def clip(self, other: Any) -> None:
        """
        Crops a rectangle inside another.
        """
        if not isinstance(other, Rect):
            try:
                other = other.__rect__
            except AttributeError:
                raise TypeError("clip requires another Rect-like object")
        if self._rect_x < other._rect_x:
            self._rect_x = other._rect_x
        if self._rect_y < other._rect_y:
            self._rect_y = other._rect_y
        if self._rect_x + self._rect_width > other._rect_x + other._rect_width:
            self._rect_x = other._rect_x + other._rect_width - self._rect_width
        if self._rect_y + self._rect_height > other._rect_y + other._rect_height:
            self._rect_y = other._rect_y + other._rect_height - self._rect_height

    def clipline(self, line: Line) -> None:
        """
        Crops a line inside a rectangle.
        """
        if not isinstance(line, Line):
            try:
                line = line.__line__()
            except AttributeError:
                raise TypeError("clipline requires a Line-like object")

        # Clip the line to the rectangle bounds
        x1, y1, x2, y2 = line._line_x1, line._line_y1, line._line_x2, line._line_y2
        if x1 < self._rect_x:
            x1 = self._rect_x
        if y1 < self._rect_y:
            y1 = self._rect_y
        if x2 > self._rect_x + self._rect_width:
            x2 = self._rect_x + self._rect_width
        if y2 > self._rect_y + self._rect_height:
            y2 = self._rect_y + self._rect_height

        line._line_x1, line._line_y1, line._line_x2, line._line_y2 = x1, y1, x2, y2

    def union(self, other: Any) -> Self:
        """
        Joins two rectangles into one.
        """

        if not isinstance(other, Rect):
            try:
                other = other.__rect__
            except AttributeError:
                raise TypeError("union requires another Rect-like object")

        x = min(self._rect_x, other._rect_x)
        y = min(self._rect_y, other._rect_y)
        width = max(self._rect_x + self._rect_width,
                    other._rect_x + other._rect_width) - x
        height = max(self._rect_y + self._rect_height,
                     other._rect_y + other._rect_height) - y
        return self.__class__(x, y, width, height)

    def unionall(self, others: list[Any]) -> Self:
        """
        The union of many rectangles, returns a new rectangle that contains all.
        """
        others = [rect.__rect__ for rect in others if isinstance(
            rect, Rect) or hasattr(rect, '__rect__')]
        if not others:
            return self.__class__(self._rect_x, self._rect_y, self._rect_width, self._rect_height)

        x = min(self._rect_x, others[0]._rect_x)
        y = min(self._rect_y, others[0]._rect_y)
        width = max(self._rect_x + self._rect_width,
                    others[0]._rect_x + others[0]._rect_width) - x
        height = max(self._rect_y + self._rect_height,
                     others[0]._rect_y + others[0]._rect_height) - y

        for rect in others[1:]:
            x = min(x, rect._rect_x)
            y = min(y, rect._rect_y)
            width = max(width, rect._rect_x + rect._rect_width - x)
            height = max(height, rect._rect_y + rect._rect_height - y)

        return self.__class__(x, y, width, height)

    def fit(self, width: float, height: float) -> None:
        """
        Resize and move a rectangle with aspect ratio.
        """
        aspect_ratio = self._rect_width / self._rect_height
        if width / height > aspect_ratio:
            width = height * aspect_ratio
        else:
            height = width / aspect_ratio
        self._rect_width = width
        self._rect_height = height

    def normalize(self) -> None:
        """
        Correct negative sizes.
        """
        if self._rect_width < 0:
            self._rect_x += self._rect_width
            self._rect_width = -self._rect_width
        if self._rect_height < 0:
            self._rect_y += self._rect_height
            self._rect_height = -self._rect_height

    def contains(self, other: Any) -> bool:
        """
        Test if one rectangle is inside another.
        """
        if not isinstance(other, Rect):
            try:
                other = other.__rect__
            except AttributeError:
                raise TypeError(
                    "colliderect requires another Rect-like object")

        return (self._rect_x <= other._rect_x and
                self._rect_y <= other._rect_y and
                self._rect_x + self._rect_width >= other._rect_x + other._rect_width and
                self._rect_y + self._rect_height >= other._rect_y + other._rect_height)

    def collidepoint(self, point: tuple) -> bool:
        """
        Test if a point is inside a rectangle.
        """
        return (self._rect_x <= point[0] < self._rect_x + self._rect_width and
                self._rect_y <= point[1] < self._rect_y + self._rect_height)

    def colliderect(self, other: Any) -> bool:
        """
        Test if two rectangles overlap.
        """
        if not isinstance(other, Rect):
            try:
                other = other.__rect__
            except AttributeError:
                raise TypeError(
                    "colliderect requires another Rect-like object")
        return (self._rect_x < other._rect_x + other._rect_width and
                self._rect_x + self._rect_width > other._rect_x and
                self._rect_y < other._rect_y + other._rect_height and
                self._rect_y + self._rect_height > other._rect_y)

    def collidelist(self, others: list[Any]) -> bool:
        """
        Test if any one rectangle in a list intersects.
        """
        for other in others:
            if self.colliderect(other):
                return True
        return False

    def collidelistall(self, others: list[Any]) -> bool:
        """
        Test if all rectangles in a list intersect.
        """
        for other in others:
            if not self.colliderect(other):
                return False
        return True

    def collideobjects(self, others: list[object]) -> bool:
        """
        Test if any object in a list intersects.
        """
        for other in others:
            if self.colliderect(other):
                return True
        return False

    def collideobjectsall(self, others: list[object]) -> bool:
        """
        Test if all objects in a list intersect.
        """
        for other in others:
            if not self.colliderect(other):
                return False
        return True

    def collidedict(self, others: dict) -> bool:
        """
        Test if one rectangle in a dictionary intersects.
        """
        if not isinstance(others, dict):
            raise TypeError(
                "collidedict requires a dictionary of Rect-like objects")
        if not all(isinstance(other, Rect) or hasattr(other, '__rect__') for other in others.values()):
            raise TypeError(
                "collidedict requires Rect-like objects in the dictionary")
        for key, other in others.items():
            if self.colliderect(other):
                return True
        return False

    def collidedictall(self, others: dict) -> bool:
        """
        Test if all rectangles in a dictionary intersect.
        """
        if not isinstance(others, dict):
            raise TypeError(
                "collidedictall requires a dictionary of Rect-like objects")
        if not all(isinstance(other, Rect) or hasattr(other, '__rect__') for other in others.values()):
            raise TypeError(
                "collidedictall requires Rect-like objects in the dictionary")
        for key, other in others.items():
            if not self.colliderect(other):
                return False
        return True

    @property
    def __rect__(self) -> Self:
        """
        Returns the rectangle itself.
        This is used to provide a consistent interface for objects that can be represented as rectangles.
        """
        return self
