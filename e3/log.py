"""Extensions to the standard Python logging system."""
from __future__ import absolute_import, division, print_function

import logging
import re
import sys
import time

from colorama import Fore, Style
from tqdm import tqdm

# Define default format for StreamHandler and FileHandler
DEFAULT_STREAM_FMT = '%(levelname)-8s %(message)s'
DEFAULT_FILE_FMT = '%(asctime)s: %(name)-24s: %(levelname)-8s %(message)s'

# Default output stream (sys.stdout by default, or a file descriptor if
# activate() is called with a filename.
default_output_stream = sys.stdout

# If sys.stdout is a terminal then enable "pretty" output for user
# This includes progress bars and colors
if sys.stdout.isatty():
    pretty_cli = True
else:
    pretty_cli = False


def progress_bar(it, **kwargs):
    """Create a tqdm progress bar.

    :param it: an interator
    :type it: collections.Iterator
    :param kwargs: see tqdm documentation
    :type kwargs: dict
    :return: a tqdm progress bar iterator
    """
    if pretty_cli:
        return tqdm(it, **kwargs)
    else:
        # When pretty cli is disabled return a progress bar that do nothing.
        # returning just the iterator will break calls to tqdm method
        # otherwise.
        return tqdm(it, disable=True, **kwargs)


__null_handler_set = set()


class TqdmHandler(logging.StreamHandler):
    """Logging handler when used when progress bars are enabled."""

    color_subst = ((re.compile(r'(OK|PASSED)', re.I), Fore.GREEN),
                   (re.compile(r'(INFO)', re.I), Fore.BLUE),
                   (re.compile(r'(ERROR|FAILED)', re.I), Fore.RED),
                   (re.compile(r'(CRITICAL)', re.I), Fore.RED + Style.BRIGHT))

    def __init__(self):
        logging.StreamHandler.__init__(self)

    def emit(self, record):
        msg = self.format(record)

        # Handle logging on several lines
        msg = msg.replace(
            '\n',
            '\n_' + ' ' * (len(msg) - len(record.message) - 1))

        # Add color
        for reg, color in self.color_subst:
            msg = re.sub(reg,
                         color + r'\1' + Fore.RESET + Style.RESET_ALL,
                         msg)

        tqdm.write(msg)


def getLogger(name=None, prefix='e3'):
    """Get a logger with a default handler doing nothing.

    Calling this function instead of logging.getLogger will avoid warnings
    such as::

        'No handler could be found for logger...'

    :param name: logger name, if not specified return the root logger
    :type name: str
    :param prefix: application prefix, will be prepended to the name
    :type prefix:  str
    :rtype: logging.Logger
    """
    class NullHandler(logging.Handler):
        """Handler doing nothing."""

        def emit(self, _):
            pass

    logger = logging.getLogger('%s.%s' % (prefix, name))

    if prefix not in __null_handler_set:
        # Make sure that the root logger has at least an handler attached to
        # it to avoid warnings.
        logging.getLogger(prefix).addHandler(NullHandler())
        __null_handler_set.add(prefix)
    return logger


def __add_handlers(level, fmt, filename=None):
    """Add log handlers using GMT.

    :param level: set the root logger level to the specified level
    :type level: int
    :param fmt: log formatter
    :type fmt: logging.Formatter
    :param filename: use of a FileHandler, using the specified filename,
        instead of a StreamHandler. Set default_output_stream to write in this
        file.
    :type filename: str
    """
    global default_output_stream
    if filename is None:
        if pretty_cli:
            handler = TqdmHandler()
        else:
            handler = logging.StreamHandler()
    else:
        handler = logging.FileHandler(filename)
        default_output_stream = handler.stream

    fmt.converter = time.gmtime
    handler.setFormatter(fmt)

    handler.setLevel(level)
    logging.getLogger('').addHandler(handler)


def activate(
        stream_format=DEFAULT_STREAM_FMT,
        file_format=DEFAULT_FILE_FMT,
        datefmt=None,
        level=logging.INFO,
        filename=None,
        e3_debug=False):
    """Activate default E3 logging.

    :param level: set the root logger level to the specified level
    :type level: int
    :param datefmt: date/time format for the log handler
    :type datefmt: str
    :param stream_format: format string for the stream handler
    :type stream_format: str
    :param file_format: format string for the file handler
    :type file_format: str
    :param filename: redirect logs to a file in addition to the StreamHandler
    :type filename: str
    :param e3_debug: activate full debug of the e3 library
    :type e3_debug: bool
    """
    # By default do not filter anything. What is effectively logged
    # will be defined by setting/unsetting handlers
    logging.getLogger('').setLevel(logging.DEBUG)
    fmt = logging.Formatter(stream_format, datefmt)

    # Set logging handlers
    __add_handlers(level=level, fmt=fmt)

    # Log to a file if necessary
    if filename is not None:
        __add_handlers(
            level=min(level, logging.DEBUG),
            fmt=logging.Formatter(file_format, datefmt),
            filename=filename)

    if e3_debug:
        getLogger('debug').setLevel(logging.DEBUG)


# Provide a logger than will provides full debug information when a program
# using e3.main.Main is called with -v -v

e3_debug_logger = getLogger('debug')
e3_debug_logger.setLevel(logging.CRITICAL + 1)

debug = e3_debug_logger.debug
