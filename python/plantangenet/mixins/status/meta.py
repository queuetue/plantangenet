from typing import Optional, Callable


class StatusMeta:
    def __init__(
        self,
        description: str = "",
        transform: Optional[Callable] = None,
        sensitive: bool = False,
        include_in_dict: bool = True
    ):
        self.description = description
        self.transform = transform or (lambda x: x)
        self.sensitive = sensitive
        self.include_in_dict = include_in_dict
