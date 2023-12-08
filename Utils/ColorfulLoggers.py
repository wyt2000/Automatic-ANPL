import coloredlogs

__all__ = ['ColoredFormatter']

class ColoredFormatter(coloredlogs.ColoredFormatter):
    # Colored log formatter.
    def __init__(self, fmt=None, datefmt=None, style='%'):
        # Match coloredlogs.ColoredFormatter arguments with logging.Formatter
        coloredlogs.ColoredFormatter.__init__(self, fmt=fmt, datefmt=datefmt)
