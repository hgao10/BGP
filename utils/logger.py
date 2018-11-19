#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import logging

# logger currently cause deepcopy to fail because it introduces mutex when deepcopy tries to serialized the objects
# Todo devise a deepcopy method for announcement class so that it excludes self.logger when it is invoked.


class DummyLogger:
    def __init__(self):
        pass

    def debug(self, dummy):
        pass

    def error(self, dummy):
        pass

def get_logger(name, loglevel):
    return DummyLogger()


# def get_logger(name, loglevel):
#     # LOGGING
#     if loglevel == 'INFO':
#         log_level = logging.INFO
#     elif loglevel == 'DEBUG':
#         log_level = logging.DEBUG
#     else:
#         log_level = logging.INFO
#
#     # add handler
#     logger = logging.getLogger(name)
#     logger.setLevel(log_level)
#
#     if len(logger.handlers) == 0:
#         handler = logging.StreamHandler()
#         formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#         handler.setFormatter(formatter)
#         logger.addHandler(handler)
#
#     return logger
