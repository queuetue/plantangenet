from ...topics.message import Message


class FailedMessage(Message):
    subject: str = "Evaluation Failed"
    payload: bytes = b"Evaluation failed."
