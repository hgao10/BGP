#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import argparse
import datetime
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import rc_file
# rc_file('matplotlibrc')

from collections import defaultdict


''' main '''
if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('log_path', help='path to log file')
    # args = parser.parse_args()

    # read data - the data is arranged according to the following heading:
    #    0      1    2
    # Scenario|Run|Time


    scenarios = list()
    routemapsizetest_files =["./evaluation/logs/time_Scenario.RoutemapSizeTest_1_100_20190114-161511.log",
                                "./evaluation/logs/time_Scenario.RoutemapSizeTest_2_100_20190114-161529.log",
                                "./evaluation/logs/time_Scenario.RoutemapSizeTest_3_100_20190114-161547.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_4_100_20190114-161620.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_5_100_20190114-161730.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_6_100_20190114-161740.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_7_100_20190114-161954.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_8_100_20190114-162008.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_9_100_20190114-162142.log",
                             "./evaluation/logs/time_Scenario.RoutemapSizeTest_10_100_20190114-162202.log"]



    itemsizetest_files =["./evaluation/logs/time_Scenario.ItemSizeTest_1_100_20190114-150029.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_2_100_20190114-150059.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_3_100_20190114-150206.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_4_100_20190114-150224.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_5_100_20190114-150245.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_6_100_20190114-150311.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_7_100_20190114-150332.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_8_100_20190114-150402.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_9_100_20190114-150504.log",
                         "./evaluation/logs/time_Scenario.ItemSizeTest_10_100_20190114-150534.log"]

    networksizetest_files = ["./evaluation/logs/time_Scenario.NetworkSizeTest_1_100_20190114-170035.log",
                             "./evaluation/logs/time_Scenario.NetworkSizeTest_2_100_20190114-165959.log",
                             "./evaluation/logs/time_Scenario.NetworkSizeTest_4_100_20190114-165935.log"

    ]



    fieldtest_files = ["./evaluation/logs/time_FieldTest_AS_PATH_MATCH_DENY_EQUAL_100_20190114-174726.log ",
                       "./evaluation/logs/time_FieldTest_AS_PATH_MATCH_PERMIT_EQUAL_100_20190114-174902.log ",
                       "./evaluation/logs/time_FieldTest_AS_PATH_SET_100_20190114-203534.log ",
                       "./evaluation/logs/time_FieldTest_COMMUNITIES_MATCH_DENY_EQUAL_100_20190114-175115.log ",
                       "./evaluation/logs/time_FieldTest_COMMUNITIES_MATCH_PERMIT_EQUAL_100_20190114-175108.log ",
                       "./evaluation/logs/time_FieldTest_COMMUNITIES_SET_100_20190109-165552.log ",
                       "./evaluation/logs/time_FieldTest_IP_PREFIX_MATCH_DENY_EQUAL_100_20190114-174609.log ",
                       "./evaluation/logs/time_FieldTest_IP_PREFIX_MATCH_DENY_GE_100_20190114-174539.log ",
                       "./evaluation/logs/time_FieldTest_IP_PREFIX_MATCH_DENY_LE_100_20190114-174547.log ",
                       "./evaluation/logs/time_FieldTest_IP_PREFIX_MATCH_PERMIT_EQUAL_100_20190114-174604.log ",
                       "./evaluation/logs/time_FieldTest_IP_PREFIX_MATCH_PERMIT_GE_100_20190114-174510.log ",
                       "./evaluation/logs/time_FieldTest_IP_PREFIX_MATCH_PERMIT_LE_100_20190114-174554.log ",
                       "./evaluation/logs/time_FieldTest_LOCAL_PREF_SET_100_20190114-203522.log ",
                       "./evaluation/logs/time_FieldTest_MED_MATCH_DENY_GE_100_20190114-203419.log ",
                       "./evaluation/logs/time_FieldTest_MED_MATCH_PERMIT_GE_100_20190114-203223.log ",

                       "./evaluation/logs/time_FieldTest_MED_SET_100_20190114-203452.log ",
                       "./evaluation/logs/time_FieldTest_NEXT_HOP_MATCH_DENY_GE_100_20190114-175150.log ",
                       "./evaluation/logs/time_FieldTest_NEXT_HOP_MATCH_PERMIT_GE_100_20190114-175158.log ",
                       "./evaluation/logs/time_FieldTest_NEXT_HOP_SET_100_20190114-203508.log "

    ]
    times = defaultdict(list)



    mean = list()
    std = list()
    rects = list()
    for i in fieldtest_files:
        first = True
        with open(i, 'r') as infile:
            for line in infile:
                data = line.strip().split(',')

                # skip the header row
                if first:
                    first = False
                    tmp_scenario = data[0]
                    scenarios.append(tmp_scenario)

                    # FieldTest, IP_PREFIX, MATCH, PERMIT, LE, 100
                    # FieldTest, COMMUNITIES, SET,100
                    if data[0] == 'FieldTest':
                        field = data[1]
                        item_type = data[2]
                        if item_type == "MATCH":
                            routemaptype = data[3]
                            filtertype = data[4]
                            variable = str(field) +"_" + str(item_type) +"_" + str(routemaptype) +"_" +str(filtertype)
                            # run_rep = data[5]
                        else:
                            # run_rep = data[3]
                            variable = str(field) +"_" + str(item_type)
                        print("variable: %s" % variable)
                    else:
                        variable = data[1]
                        print("variable: %s" % variable)
                    continue

                # tmp_scenario = data[0]
                # tmp_run = int(data[1])
                # tmp_time = float(data[2])
                tmp_run = int(data[0])
                tmp_time = float(data[1])

                # if tmp_scenario not in scenarios:
                #     scenarios.append(tmp_scenario)

                times[variable].append(tmp_time)


            mean.append(np.mean(times[variable]))
            print("mean %s" % np.mean(times[variable]))
            std.append(np.std(times[variable]))
            print("std: %s" % np.std(times[variable]))

    N = len(fieldtest_files)
    # calculate means?

    # mean = [np.mean(times[tmp_scenario])]

    # calculate std
    # std = [np.std(times[tmp_scenario])]
    # print ("mean: %s, std:%s" % (mean, std))

    ind = np.arange(N)  # the x locations for the groups
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    ax.set_ylabel('Execution Time')
    ax.set_title('Execution Time by Number of Items in Route MAP')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(('1', '2'))

    for i in range(0, N):
        rects.append(ax.bar(ind, mean[i], width, color='r', yerr=std[i]))
    # rects1 = ax.bar(ind, mean, width, color='r', yerr=std)

    # add some text for labels, title and axes ticks



    ax.legend((rects[0], rects[1]), ('1', '2'))


    # def autolabel(rect_s):
    #     """
    #     Attach a text label above each bar displaying its height
    #     """
    #     for rect in rect_s:
    #         height = rect.get_height()
    #         ax.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
    #                 '%d' % int(height),
    #                 ha='center', va='bottom')
    #
    #
    # autolabel(rects)


    plt.show()




    #
    # # start plotting how the samples affect the number of questions asked
    # fig, ax = plt.subplots(sharex=False, sharey=True)
    #
    # plot_objects = dict()
    # for key in sorted(scenarios):
    #     values = times[key]
    #     plot_objects[key] = ax.plot(range(1, len(values) + 1), values)
    #
    # ax.set_title('Timing')
    # # ax.set_xlim((0, 100))
    # ax.set_ylabel('Run Time [s]')
    # ax.set_xlabel('Iteration')
    #
    # ps = [p[0] for tmp_key, p in sorted(plot_objects.items(), key=lambda x: x[0])]
    # ss = [tmp_key for tmp_key in sorted(plot_objects.keys())]
    # ax.legend(ps, ss, loc='lower right', ncol=1)
    #
    # plt.tight_layout(pad=0.0, w_pad=1.0, h_pad=0.0)

    if tmp_scenario == 'FieldTest':
        if item_type == "MATCH":

            fig.savefig('timing_%s_%s_%s_%s_%s.pdf' % (field, item_type, routemaptype, run_rep,'{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now() )),
                                                       bbox_inches='tight')

        else:
            fig.savefig('timing_%s_%s_%s_%s.pdf' % (field, item_type, run_rep, '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())), bbox_inches='tight')
    else:
        fig.savefig('timing_%s_%s.pdf' % (tmp_scenario, '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())), bbox_inches='tight')