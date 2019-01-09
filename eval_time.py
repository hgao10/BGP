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
        self.scenario = None
        self.fieldtype = None
        self.repetitions = 1
        self.filtertype = None
        self.routemaptype = None
        self.itemtype = None

        self.prompt = '> '
        # self.intro = 'Hi, '

        self.cmdloop()

    def do_load(self, line=''):
        scn_tag = line.split()
        self.scenario = Scenario[scn_tag[0]]
        self.fieldtype = RouteAnnouncementFields[scn_tag[1]] # tag: IP_Prefix,

        self.repetitions = int(scn_tag[2])

        self.itemtype = ItemType[scn_tag[3]] # match or set
        if self.itemtype == ItemType.MATCH:
            self.filtertype = FilterType[scn_tag[4]]  # ge, le or equal
            self.routemaptype = RouteMapType[scn_tag[5]]  # deny or permit

        self.neighbor = "in_neighbor"

        print('scenario: %s, fieldtype :%s, repetitons:%s, filtertype: %s, routemaptype: %s, itemtype: %s' % (self.scenario, self.fieldtype,
                                                                                                            self.repetitions, self.filtertype,
                                                                                                              self.routemaptype, self.itemtype))

    def start_run(self):
        """run: Run an analysis on the loaded network model by propagating a symbolic announcement"""
        if self.network:
            if not self.neighbor:
                self.neighbor = random.choice(list(self.network.get_external_routers()))
                print("No neighbor specified, picked %s randomly." % self.neighbor)

            # print("Propagate announcement with AS community list :%s" % self.network.AS_community_list)
            outcome = self.network.propagate_announcement(self.neighbor, None, self.network.AS_community_list)

            output = 'From %s the following announcements make it through to the other neighbors:\n\n' % (self.neighbor, )
            for neighbor, announcement in outcome.items():

                output += '\t%s: %s\n' % (neighbor, announcement)

                # Disable as path testing during time measurement
                # self.test_as_path(announcement)
            print(output)
        else:
            print('You need to load a network model before you can run the symbolic execution.')

    def get_heading(self):
        if self.itemtype == ItemType.MATCH:
            return "%s, %s, %s, %s, %s, %d " % (self.scenario.name, self.fieldtype.name, self.itemtype.name,
                                                         self.routemaptype.name, self.filtertype.name,
                                                      self.repetitions)
        else:
            return "%s, %s, %s,%d " % (self.scenario.name, self.fieldtype.name, self.itemtype.name,

                                                      self.repetitions)

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
    def do_run(self, line=''):
        # scenario: FieldTest, ItemSizeTest, RoutemapSizeTest
        # tag: FieldTest: field name (IP prefix, community, ...)
        #      ItemSizeTest: # of items, 1, 2, 3, 4
        #      RoutemapSizeTest: # of routemaps

        # file_name = 'evaluation/logs/time_%s_%s_%s.log' % (scenario, self.fieldtype, '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))
        if self.itemtype == ItemType.MATCH:
            file_name = 'evaluation/logs/time_%s_%s_%s_%s_%s_%d_%s.log '% (self.scenario.name, self.fieldtype.name, self.itemtype.name,
                                                         self.routemaptype.name, self.filtertype.name,
                                                      self.repetitions,
                                                           '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))
            print("File name: %s_%s_%s_%s_%s_%d_%s.log "% (self.scenario.name, self.fieldtype.name, self.itemtype.name,
                                                         self.routemaptype.name, self.filtertype.name,
                                                      self.repetitions,
                                                           '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())))
        else:
            file_name = 'evaluation/logs/time_%s_%s_%s_%d_%s.log ' % (self.scenario.name, self.fieldtype.name, self.itemtype.name,

                                                                            self.repetitions,
                                                                            '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))
            print("File name: %s_%s_%s_%d_%s.log " % (self.scenario.name, self.fieldtype.name, self.itemtype.name,

                                                            self.repetitions,
                                                            '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now())))
        #
        with open(file_name, 'w') as outfile:
            outfile.write("%s\n" % self.get_heading())
        # create all the general state: network model, route-map etc.
        if self.scenario == Scenario.FieldTest:
            print("run: scenario is scenario fieldtest")
            self.network = NetworkTopology('SingleRouterTwoNeighbors')

            self.network.add_community_list(["16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12",
                                            "16:13",
                                        "16:14", "16:15", "16:16"])
            tmp_router = self.network.add_internal_router('main', '10.0.0.1/32', 10)
            tmp_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
            tmp_router.add_route_map(tmp_route_map, RouteMapDirection.IN, '9.0.0.1')

            # route map out has zero route map items, would pass anything
            # tmp_route_map_out = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
            # tmp_router.add_route_map(tmp_route_map_out, RouteMapDirection.OUT, '11.0.0.1')

            # add all neighboring routers that advertise and receive routes
            self.network.add_external_router('in_neighbor', '9.0.0.1', 9)
            self.network.add_external_router('out_neighbor', '11.0.0.1', 11)

            # add the connections between the routers (e.g., full mesh between internal routers and a connection between
            # external routers and their specific counterpart internally
            self.network.add_peering('main', 'in_neighbor')
            self.network.add_peering('main', 'out_neighbor')

        for i in range(0, self.repetitions):
            # create all the specific things: for example the routing announcement
            #
            # create a match or a set routemapitem and add it to the network
            rm_items = create_route_map_item(self.fieldtype, self.filtertype, self.routemaptype, self.itemtype)
            tmp_route_map.clear()
            tmp_route_map.add_item(rm_items, 10)
            # time measurement
            print("about to start the timer")
            start_time = time.time()
            # print("start_time is %d" % start_time)

            # run whatever we need to measure - at the moment just some sleep
            # random_time = random.uniform(0.0, 2.0)
            # time.sleep(random_time)

            self.start_run()

            run_time = time.time() - start_time
            print("finished calculating the time")
            # tmp_stats = TimingStats(scenario, i, run_time)
            if self.itemtype == ItemType.MATCH:
                with open(file_name, 'a') as outfile:
                    outfile.write("%s %s %s\n" % (i,  run_time, rm_items.matches[0].pattern))
                print( i, run_time, rm_items.matches[0].pattern,)
            if self.itemtype == ItemType.SET:
                with open(file_name, 'a') as outfile:
                    outfile.write("%s %s %s\n" % (i,  run_time, rm_items.actions[0].pattern))
                print(i, run_time,rm_items.actions[0].pattern)

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
# def field_test_prep(field, filtertype, routemaptype, itemtype):
#     if field == RouteAnnouncementFields.IP_PREFIX or field == RouteAnnouncementFields.NEXT_HOP:
#         print("enter field test prep to generate ip")
#         pattern = ip_network_random()
#         routemaptype = route_map_random(routemaptype)
#         itemtype = item_type_random(itemtype)
#         print("pattern : %s, filtertype: %s, routemaptype: %s, itemtype: %s" % (pattern, filtertype, routemaptype, itemtype))
#
#     return field, pattern, filtertype, routemaptype, itemtype


def create_route_map_item(field, filtertype_p, routemaptype_p, itemtype_p):
    itemtype = item_type_random(itemtype_p) # match or action
    rm_items = RouteMapItems()
    if field == RouteAnnouncementFields.IP_PREFIX or field == RouteAnnouncementFields.NEXT_HOP:
        pattern_ip = ip_network_random()
        print("enter create route map item")

        pattern = SymbolicField.create_from_prefix(pattern_ip, RouteAnnouncementFields.IP_PREFIX)

        if itemtype == ItemType.MATCH: # match ip prefix or next hop
            filtertype = filter_type_random(filtertype_p) # GE or LE or EQUAL, next hop needs to be GE
            routemaptype = route_map_random(routemaptype_p) # permit or deny
            print("add match: routemaptype: %s, routeannoucementfields: %s, pattern_ip:%s, filtertype:%s" % (
                routemaptype, field, pattern, filtertype))
            rm_items.add_match(routemaptype, field, pattern, filtertype)
        else:
            # set next hop
            print("add action: routeannoucementfields: %s, pattern:%s" % (field, pattern))

            rm_items.add_action(RouteAnnouncementFields.NEXT_HOP, pattern.str_ip_prefix)

    if field == RouteAnnouncementFields.AS_PATH:

        if itemtype == ItemType.MATCH:
            pattern = AS_PATH_regex_random()
            filtertype = filter_type_random(FilterType.GE) # doesnt really matter for as path
            routemaptype = route_map_random(routemaptype_p)  # permit or deny
            print("add match: routemaptype: %s, routeannoucementfields: %s, pattern_ip:%s, filtertype:%s" % (
                routemaptype, field, pattern, filtertype))
            rm_items.add_match(routemaptype, field, pattern, filtertype)
        else:
            #  rm_items.add_action(RouteAnnouncementFields.AS_PATH, " 324 324")
            asn_rep = random.randint(1, 16)
            asn = random.randint(1, 65535)
            pattern = (str(asn) + " ") * asn_rep

            print("add action: routeannoucementfields: %s, pattern:%s" % (field, pattern))
            rm_items.add_action(field, pattern)

    if field == RouteAnnouncementFields.COMMUNITIES:
        community_list = ["16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12",
                                            "16:13",
                                        "16:14", "16:15", "16:16"]
        # randomly chooses x = comm_num of communities to match
        comm_num = random.randint(1, 16)
        # print ("comm #: %s" % comm_num)
        # the index are randomly chosen and put in a list
        community_index_list = random.sample(range(0, 16), comm_num)

        # in this case the pattern is a list
        pattern = list()
        # print("community_index_list: %s" % ",".join(community_index_list))
        for i in community_index_list:
            pattern.append(community_list[i])
        # print("community pattern to be matched is %s" % ", ".join(pattern))
        if itemtype == ItemType.MATCH:
            filtertype = filter_type_random(filtertype_p)  # GE or LE or EQUAL, next hop needs to be GE
            routemaptype = route_map_random(routemaptype_p)  # permit or deny
            rm_items.add_match(routemaptype, field, pattern, filtertype)
        if itemtype == ItemType.SET:
            rm_items.add_action(field, pattern)

    if field == RouteAnnouncementFields.LOCAL_PREF:
        if itemtype == ItemType.MATCH:
            print ("Error: can't match on local pref, SET operation only. ")
        else:
            rm_items.add_action(field, random.randint(1, 1000))

    if field == RouteAnnouncementFields.MED:
        pattern = random.randint(1, 1000)
        if itemtype == ItemType.MATCH:
            filtertype = FilterType.EQUAL # doesn't matter actually
            routemaptype = route_map_random(routemaptype_p)
            print("add match: routemaptype: %s, routeannoucementfields: %s, pattern_ip:%s, filtertype:%s" % (
                routemaptype, field, pattern, filtertype))
            rm_items.add_match(routemaptype, field, pattern, filtertype)
        else:

            print("add action: routeannoucementfields: %s, pattern:%s" % (field, pattern))

            rm_items.add_action(field, pattern)


    return rm_items


def AS_PATH_regex_random():

    as_path_number = random.randint(1, 65535)
    # AS_PATH: _x_, _x$, ^ x$, ^ x_
    pattern = ["_x_", "", "", "", "", ]
    pattern_index = random.randint(0, 3)
    if pattern_index == 0:
        regex = ".*\W"+str(as_path_number)+"\W.*"
    if pattern_index == 1:
        regex = ".*\W"+str(as_path_number)+"\W"
    if pattern_index == 2:
        regex = "\W"+str(as_path_number)+"\W"
    if pattern_index == 3:
        regex = "\W"+str(as_path_number)+"\W.*"

    print ("%s" % regex)
    return regex


def route_map_random(type=None):
    if type:
        return type
    else:
        list = [RouteMapType.PERMIT, RouteMapType.DENY]
        return list[random.randint(0, 1)]


def filter_type_random(type=None):
    if type:
        # return 'FilterType' + '.' + str(type)
        return type
    else:
        list = [FilterType.GE, FilterType.LE, FilterType.EQUAL]
        return list[random.randint(0, 2)]


def item_type_random(type=None):
    if type:

        return type
    else:
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





