#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import datetime
import random
from random import getrandbits
from ipaddress import IPv4Address
import time
import cmd
import argparse
from enum import Enum
from model.announcement import RouteMapType, RouteAnnouncementFields, SymbolicField, FilterType
from model.router import RouteMap, RouteMapItems, RouteMapDirection


from model.network import NetworkTopology

from utils.logger import get_logger


class ItemType(Enum):
    MATCH = 1
    SET = 2


class Scenario(Enum):
    FieldTest = 1
    ItemSizeTest = 2
    RoutemapSizeTest = 3


# initialize logging
logger = get_logger('Option2Eval', 'INFO')


class TimingStats(object):
    def __init__(self, scenario, tag, run, time, repetitions):
        self.scenario = scenario
        self.tag = tag
        self.run = run
        self.time = time
        self.repetitions = repetitions

    def __str__(self):
        # scenario:
        # run: # of runs
        # time
        return "%s,%s,%f" % (self.scenario, self.run, self.time)

    def get_heading(self):
        # return "Scenario,Run,Time"
        return "%s,%s,%f" % (self.scenario, self.tag, self.repetitions)


class TestSuite(cmd.Cmd):

    def __init__(self, *args, **kw):
        cmd.Cmd.__init__(self, *args, **kw)

        # current network
        self.network = None
        self.neighbor = None

        self.prompt = '> '
        # self.intro = 'Hi, '

        self.cmdloop()

    def do_load(self, line=''):
        scn_tag = line.split()
        self.scenario = scn_tag[0]
        self.tag = scn_tag[1]
        self.repetitions = scn_tag[2]

        self.neighbor = "in_neighbor"

        print('scenario: %s, tag :%s, repetitons:%s' % (self.scenario, self.tag, self.repetitions))

    def start_run(self):
        """run: Run an analysis on the loaded network model by propagating a symbolic announcement"""
        if self.network:
            if not self.neighbor:
                self.neighbor = random.choice(list(self.network.get_external_routers()))
                print("No neighbor specified, picked %s randomly." % self.neighbor)

            print("Propagate announcement with AS community list :%s" % self.network.AS_community_list)
            outcome = self.network.propagate_announcement(self.neighbor, None, self.network.AS_community_list)

            output = 'From %s the following announcements make it through to the other neighbors:\n\n' % (self.neighbor, )
            for neighbor, announcement in outcome.items():

                output += '\t%s: %s\n' % (neighbor, announcement)

                # Disable as path testing during time measurement
                # self.test_as_path(announcement)
            print(output)
        else:
            print('You need to load a network model before you can run the symbolic execution.')

    def test_as_path(self, announcement):
        for announcement_element in announcement:
            print('announcement %d is %s' % (announcement.index(announcement_element), announcement))

            # Ask user for as path test strings until one is accepted by the fsm
            result = False
            i = 0
            while result is False:
                if i == 0:
                    i = 1
                else:
                    print("test as path %s is not accepted, please input new as path\n" % test_as_path)
                test_as_path = input("Input as path to test the FSM for the as path\n")
                result = announcement_element.as_path.as_path_fsm.accepts(test_as_path)
            print("test as path %s is accepted" % test_as_path)

    # def do_run(self, line=''):
    def do_run(self):
        # scenario: FieldTest, ItemSizeTest, RoutemapSizeTest
        # tag: FieldTest: field name (IP prefix, community, ...)
        #      ItemSizeTest: # of items, 1, 2, 3, 4
        #      RoutemapSizeTest: # of routemaps

        scenario = self.scenario
        tag = self.tag
        repetitions = self.repetitions
        file_name = 'evaluation/logs/time_%s_%s_%s.log' % (scenario, tag, '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))

        # with open(file_name, 'w') as outfile:
        #     outfile.write("%s\n" % TimingStats.get_heading())
        print(scenario, tag, repetitions)

        logger.info("Starting evaluation for %s." % scenario)
        # create all the general state: network model, route-map etc.
        if scenario == Scenario.FieldTest:
            self.network = NetworkTopology('SingleRouterTwoNeighbors')
            tmp_router = self.network.add_internal_router('main', '10.0.0.1/32', 10)
            tmp_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
            tmp_router.add_route_map(tmp_route_map, RouteMapDirection.IN, '9.0.0.1')

            # route map out has zero route map items, would pass anything
            tmp_route_map_out = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
            tmp_router.add_route_map(tmp_route_map_out, RouteMapDirection.OUT, '11.0.0.1')

            # add all neighboring routers that advertise and receive routes
            self.network.add_external_router('in_neighbor', '9.0.0.1', 9)
            self.network.add_external_router('out_neighbor', '11.0.0.1', 11)

            # add the connections between the routers (e.g., full mesh between internal routers and a connection between
            # external routers and their specific counterpart internally
            self.network.add_peering('main', 'in_neighbor')
            self.network.add_peering('main', 'out_neighbor')

        for i in range(0, repetitions):
            # create all the specific things: for example the routing announcement
            #
            # create a match or a set routemapitem and add it to the network
            rm_items = create_route_map_item(tag)
            tmp_route_map.add_item(rm_items, 10)
            # time measurement
            start_time = time.time()

            # run whatever we need to measure - at the moment just some sleep
            # random_time = random.uniform(0.0, 2.0)
            # time.sleep(random_time)

            self.start_run()

            run_time = time.time() - start_time

            # tmp_stats = TimingStats(scenario, i, run_time)
            # with open(file_name, 'a') as outfile:
            #     outfile.write("%s\n" % tmp_stats)
            print(scenario, i, run_time)

            # if i % 10 == 0:
            #     logger.info('Done with iteration %d out of %d' % (i + 1, repetitions))

        logger.info('Done with everything')

        return


# field: IP_Prefix, Next_Hop, AS_Path, Community, MED
# Pattern: IP_Prefix: 100 different IP's
#           Next_Hop: same as above
#           AS_PATH: _x_, _x$, ^x$, ^x_, _x_y$ (x, y random from 1 to 65565, need a function to generate it)
#           Community: randomly pick 2 community (could vary # of communities to match, TODO)
#           MED: Exact match, pick a random MED number
# route map type: Permit or Deny
# Filter type: If its IP_Prefix: GE, LE, Equal
#              for Next_Hop: Equal
#              everything else: Don't care
# Item type: match or set
def field_test_prep(field):
    if field == RouteAnnouncementFields.IP_PREFIX:
        pattern, filtertype = pattern_generate(RouteAnnouncementFields.IP_PREFIX)
        routemaptype = route_map_random()
        itemtype = ItemType.MATCH
        print("pattern : %s, filtertype: %s, routemaptype: %s, itemtype: %s" % (pattern, filtertype, routemaptype, itemtype))

    return field, pattern, filtertype, routemaptype, itemtype


def create_route_map_item(field):
    field, pattern, filtertype, routemaptype, itemtype = field_test_prep(field)
    if field == RouteAnnouncementFields.IP_PREFIX:

        rm_items = RouteMapItems()
        pattern_ip = SymbolicField.create_from_prefix(pattern, RouteAnnouncementFields.IP_PREFIX)
        print("add match: routemaptype: %s, routeannoucementfields: %s, pattern_ip:%s, filtertype:%s" %(routemaptype, field, pattern_ip, filtertype))
        rm_items.add_match(routemaptype, RouteAnnouncementFields.IP_PREFIX, pattern_ip, filtertype)

    return rm_items


def pattern_generate(field):
    if field == RouteAnnouncementFields.IP_PREFIX:
        pattern = ip_network_random()
        filtertype = filter_type_random()

    return pattern, filtertype


def route_map_random():
    list = [RouteMapType.PERMIT, RouteMapType.DENY]

    return list[random.randint(0, 1)]


def filter_type_random():
    list = [FilterType.GE, FilterType.LE, FilterType.EQUAL]
    return list[random.randint(0, 2)]


def item_type_random():
    list = [ItemType.MATCH, ItemType.SET]
    return list[random.randint(0, 1)]


def ip_network_random():
    prefix_len = random.randint(4, 28)
    bits = getrandbits(prefix_len)
    bits_pad_zeros = bits * 2 ** (32 - prefix_len)
    addr = IPv4Address(bits_pad_zeros)
    addr_str = str(addr) + '/' + str(prefix_len)
    # print(prefix_len, bits, addr, addr, addr_str)

    return addr_str


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='enable debug output', action='store_true')

    args = parser.parse_args()

    debug = args.debug

    TestSuite()





