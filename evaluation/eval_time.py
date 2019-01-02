#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import datetime
import random
import time

from utils.logger import get_logger


# initialize logging
logger = get_logger('Option2Eval', 'INFO')


class TimingStats(object):
    def __init__(self, scenario, run, time):
        self.scenario = scenario
        self.run = run
        self.time = time

    def __str__(self):
        return "%s,%s,%f" % (self.scenario, self.run, self.time)

    @staticmethod
    def get_heading():
        return "Scenario,Run,Time"


def run_eval(scenario, tag, repetitions):
    file_name = 'evaluation/logs/time_%s_%s_%s.log' % (scenario, tag, '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))

    with open(file_name, 'w') as outfile:
        outfile.write("%s\n" % TimingStats.get_heading())

    logger.info("Starting evaluation for %s." % scenario)

    # create all the general state: network model, route-map etc.

    for i in range(0, repetitions):
        # create all the specific things: for example the routing announcement
        #
        #

        # time measurement
        start_time = time.time()

        #
        # run whatever we need to measure - at the moment just some sleep
        random_time = random.uniform(0.0, 2.0)
        time.sleep(random_time)
        #
        #

        run_time = time.time() - start_time

        tmp_stats = TimingStats(scenario, i, run_time)
        with open(file_name, 'a') as outfile:
            outfile.write("%s\n" % tmp_stats)

        if i % 10 == 0:
            logger.info('Done with iteration %d out of %d' % (i + 1, repetitions))

    logger.info('Done with everything')
