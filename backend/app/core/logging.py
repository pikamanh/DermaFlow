import logging

class CustomColorFormatter(logging.Formatter):
    # ANSI escape sequences for text formatting
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    # Define custom string structure
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Map levels to corresponding color styles
    COLORS = {
        logging.DEBUG: grey,
        logging.INFO: grey,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelno, self.reset)
        # Apply the color to the format structure
        formatter = logging.Formatter(f"{log_color}{self.log_format}{self.reset}")
        return formatter.format(record)

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Tránh add nhiều handler
    if not logger.handlers:
        console_handler = logging.StreamHandler()

        console_handler.setFormatter(
            CustomColorFormatter()
        )

        logger.addHandler(console_handler)

    return logger