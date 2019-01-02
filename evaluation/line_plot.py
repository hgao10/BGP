#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import argparse
import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc_file
rc_file('matplotlibrc')

from collections import defaultdict


''' main '''
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('log_path', help='path to log file')
    args = parser.parse_args()

    # read data - the data is arranged according to the following heading:
    #    0      1    2
    # Scenario|Run|Time
    scenarios = list()

    times = defaultdict(list)

    first = True

    with open(args.log_path, 'r') as infile:
        for line in infile:
            data = line.strip().split(',')

            # skip the header row
            if first:
                first = False
                continue

            tmp_scenario = data[0]
            tmp_run = int(data[1])
            tmp_time = float(data[2])

            if tmp_scenario not in scenarios:
                scenarios.append(tmp_scenario)

            times[tmp_scenario].append(tmp_time)

    # start plotting how the samples affect the number of questions asked
    fig, ax = plt.subplots(sharex=False, sharey=True)

    plot_objects = dict()
    for key in sorted(scenarios):
        values = times[key]
        plot_objects[key] = ax.plot(range(1, len(values) + 1), values)

    ax.set_title('Timing')
    # ax.set_xlim((0, 100))
    ax.set_ylabel('Run Time [s]')
    ax.set_xlabel('Iteration')

    ps = [p[0] for tmp_key, p in sorted(plot_objects.items(), key=lambda x: x[0])]
    ss = [tmp_key for tmp_key in sorted(plot_objects.keys())]
    ax.legend(ps, ss, loc='lower right', ncol=1)

    plt.tight_layout(pad=0.0, w_pad=1.0, h_pad=0.0)
    fig.savefig('bgp_timing_{:%Y%m%d-%H%M%S}.pdf'.format(datetime.datetime.now()), bbox_inches='tight')
