from plantangenet.logger import Logger


def test_logger_context():
    logger = Logger()
    logger.info("Test message", context={"a": 1})  # Should not error
