from ...topics.message import Message


class SuccessfulMessage(Message):
    subject: str = "Evaluation Successful"
    payload: bytes = b"Evaluation passed successfully."
