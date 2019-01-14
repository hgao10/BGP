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
    NetworkSizeTest = 4


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
        self.itemsize = 1
        self.routemapnum = 1
        self.itemnumber =1 # number of items in a route map

        self.prompt = '> '
        # self.intro = 'Hi, '

        self.cmdloop()

    def do_load(self, line=''):
        scn_tag = line.split()
        self.scenario = Scenario[scn_tag[0]]
        if self.scenario == Scenario.FieldTest:
            self.fieldtype = RouteAnnouncementFields[scn_tag[1]] # tag: IP_Prefix,

            self.repetitions = int(scn_tag[2])

            self.itemtype = ItemType[scn_tag[3]] # match or set
            if self.itemtype == ItemType.MATCH:
                self.filtertype = FilterType[scn_tag[4]]  # ge, le or equal
                self.routemaptype = RouteMapType[scn_tag[5]]  # deny or permit

            print('scenario: %s, fieldtype :%s, repetitons:%s, filtertype: %s, routemaptype: %s, itemtype: %s' % (self.scenario, self.fieldtype,
                                                                                                                  self.repetitions, self.filtertype,
                                                                                                                  self.routemaptype, self.itemtype))

        if self.scenario == Scenario.ItemSizeTest:
            self.itemsize = int(scn_tag[1]) # tag: how many match or set operations are contained in a route map item
            self.repetitions = int(scn_tag[2])

            print ('scenario: %s, Itemsize: %s, repetitions: %s' % (self.scenario, self.itemsize, self.repetitions))

        if self.scenario == Scenario.RoutemapSizeTest:
            self.itemnumber = int(scn_tag[1])
            self.repetitions = int(scn_tag[2])

            print('scenario: %s, Itemnumber: %s, repetitions: %s' % (self.scenario, self.itemnumber, self.repetitions))

        if self.scenario == Scenario.NetworkSizeTest:
            self.routemapnum = int(scn_tag[1])
            self.repetitions = int(scn_tag[2])

            print('scenario: %s, Route map number: %s, repetitions: %s' % (self.scenario, self.routemapnum, self.repetitions))

        self.neighbor = "in_neighbor"


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
        if self.scenario == Scenario.FieldTest:
            if self.itemtype == ItemType.MATCH:
                return "%s, %s, %s, %s, %s, %d " % (self.scenario.name, self.fieldtype.name, self.itemtype.name,
                                                             self.routemaptype.name, self.filtertype.name,
                                                          self.repetitions)
            else:
                return "%s, %s, %s,%d " % (self.scenario.name, self.fieldtype.name, self.itemtype.name,

                                                          self.repetitions)
        if self.scenario == Scenario.ItemSizeTest:
            return "%s, %s, %d" % (self.scenario.name, self.itemsize, self.repetitions)
        if self.scenario == Scenario.RoutemapSizeTest:
            return "%s, %s, %d" % (self.scenario.name, self.itemnumber, self.repetitions)
        if self.scenario == Scenario.NetworkSizeTest:
            return "%s, %s, %d" % (self.scenario.name, self.routemapnum, self.repetitions)

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
        #      ItemSizeTest: # number of matches/sets in a single item
        #      RoutemapSizeTest: # of route map items in a single route map
        #       NetworkSizeTest: # of route maps in a network: 1, 2, 4


        # create all the general state: network model, route-map etc.

        # create a topology
        if self.scenario == Scenario.FieldTest or self.scenario == Scenario.ItemSizeTest or self.scenario == Scenario.RoutemapSizeTest:
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


        if self.scenario == Scenario.NetworkSizeTest:
            if self.routemapnum == 1:
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

            if self.routemapnum == 2:
                self.network = NetworkTopology('SingleRouterTwoNeighborswith2Routemaps')
                self.network.add_community_list(["16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12",
                                                 "16:13",
                                                 "16:14", "16:15", "16:16"])
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

            if self.routemapnum == 4:
                print("prepare network for 4 routemaps")
                self.network = NetworkTopology('TwoRouterTwoNeighborswith4Routemaps')
                self.network.add_community_list(["16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12",
                                                 "16:13",
                                                 "16:14", "16:15", "16:16"])
                tmp_router1 = self.network.add_internal_router('main1', '10.0.0.1/32', 10)

                tmp_router2 = self.network.add_internal_router('main2', '10.0.0.2/32', 10)

                tmp_route_map1 = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
                tmp_router1.add_route_map(tmp_route_map1, RouteMapDirection.IN, '9.0.0.1')

                # route map out has zero route map items, would pass anything
                tmp_route_map_out1 = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
                tmp_router1.add_route_map(tmp_route_map_out1, RouteMapDirection.OUT, '10.0.0.2')

                tmp_route_map2 = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
                tmp_router2.add_route_map(tmp_route_map2, RouteMapDirection.IN, '10.0.0.1')

                # route map out has zero route map items, would pass anything
                tmp_route_map_out2 = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
                tmp_router2.add_route_map(tmp_route_map_out2, RouteMapDirection.OUT, '11.0.0.1')


                # add all neighboring routers that advertise and receive routes
                self.network.add_external_router('in_neighbor', '9.0.0.1', 9)
                self.network.add_external_router('out_neighbor', '11.0.0.1', 11)

                # add the connections between the routers (e.g., full mesh between internal routers and a connection between
                # external routers and their specific counterpart internally
                self.network.add_peering('main1', 'in_neighbor')
                self.network.add_peering('main1', 'main2')
                self.network.add_peering('main2', 'out_neighbor')


        if self.scenario == Scenario.FieldTest:
            print("run: scenario is scenario fieldtest")

            # file_name = 'evaluation/logs/time_%s_%s_%s.log' % (scenario, self.fieldtype, '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))
            if self.itemtype == ItemType.MATCH:
                file_name = 'evaluation/logs/time_%s_%s_%s_%s_%s_%d_%s.log ' % (self.scenario.name, self.fieldtype.name, self.itemtype.name,
                                                                                self.routemaptype.name, self.filtertype.name,
                                                                                self.repetitions,
                                                                                '{:%Y%m%d-%H%M%S}'.format(datetime.datetime.now()))
                print("File name: %s_%s_%s_%s_%s_%d_%s.log " % (self.scenario.name, self.fieldtype.name, self.itemtype.name,
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

            with open(file_name, 'w') as outfile:
                outfile.write("%s\n" % self.get_heading())

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
                        outfile.write("%s,%s,%s\n" % (i,  run_time, rm_items.matches[0].pattern))
                    print(i, run_time, rm_items.matches[0].pattern)
                if self.itemtype == ItemType.SET:
                    with open(file_name, 'a') as outfile:
                        outfile.write("%s,%s,%s\n" % (i,  run_time, rm_items.actions[0].pattern))
                    print(i, run_time, rm_items.actions[0].pattern)

        if self.scenario == Scenario.ItemSizeTest:
            # pick match, set field
            match_options = [RouteAnnouncementFields.IP_PREFIX, RouteAnnouncementFields.NEXT_HOP, RouteAnnouncementFields.AS_PATH,
                             RouteAnnouncementFields.COMMUNITIES, RouteAnnouncementFields.MED]

            set_options = [RouteAnnouncementFields.LOCAL_PREF, RouteAnnouncementFields.NEXT_HOP, RouteAnnouncementFields.AS_PATH,
                             RouteAnnouncementFields.COMMUNITIES, RouteAnnouncementFields.MED]
            # incrementally add a match then a set, so the number of matches are always 1 more or equal to the set operation
            number_set = int(self.itemsize/2) # 5/2 = 2
            number_match = self.itemsize - number_set

            print("going to generate %s number of matches and %s number of set " % (number_match, number_set))

            file_name = 'evaluation/logs/time_%s_%s_%s_%s.log' % (self.scenario, self.itemsize, self.repetitions, '{:%Y%m%d-%H%M%S}'.format(
            datetime.datetime.now()))
            print("file name:%s" % file_name)
            with open(file_name, 'w') as outfile:
                outfile.write("%s\n" % self.get_heading())
            print ("Heading: %s\n" % self.get_heading())
            for i in range(0, self.repetitions):
                tmp_route_map.clear()

                match_field_index = random.sample(range(0, 5), number_match)  # pick from 0, 1, 2, 3, 4
                set_field_index = random.sample(range(0, 5), number_set)
                # print("match field index is %s and set_field_index is %s" % (",".join(match_field_index), ",".join(set_field_index)))
                match_field = list()
                set_field = list()

                match_field_name = list()
                set_field_name = list()
                for m in match_field_index:
                    match_field.append(match_options[m])
                    match_field_name.append(match_options[m].name)
                    print("adding match field index %d" % m)
                for s in set_field_index:
                    set_field.append(set_options[s])
                    set_field_name.append(set_options[s].name)
                    print("adding set field index %d" % s)
                # pick a type for the item

                itempermittype = route_map_random() # pick permit or Deny
                rm_items = RouteMapItems(itempermittype)
                print("rm item type %s " % rm_items.type)
                # add match to the item
                for m in match_field:
                    create_a_match_or_set(m, ItemType.MATCH, rm_items)

                for s in set_field:
                    create_a_match_or_set(s, ItemType.SET, rm_items)

                tmp_route_map.add_item(rm_items, 10)
                # time measurement
                print("about to start the timer")
                start_time = time.time()
                # print("start_time is %d" % start_time)

                self.start_run()

                run_time = time.time() - start_time
                print("finished calculating the time")
                operation_fields = ",".join(match_field_name) +"&" +",".join(set_field_name)

                with open(file_name, 'a') as outfile:
                    outfile.write("%s,%s,%s\n" % (i,  run_time, operation_fields))
                #print(i, run_time, ",".join(match_field_name), ",".join(set_field_name), operation_fields)

        if self.scenario == Scenario.RoutemapSizeTest:
            # self.itemnumber, self.repetitions
            file_name = 'evaluation/logs/time_%s_%s_%s_%s.log' % (self.scenario, self.itemnumber, self.repetitions, '{:%Y%m%d-%H%M%S}'.format(
                datetime.datetime.now()))
            print("file name:%s" % file_name)
            with open(file_name, 'w') as outfile:
                outfile.write("%s\n" % self.get_heading())
            print("Heading: %s\n" % self.get_heading())
            for i in range(0, self.repetitions):
                tmp_route_map.clear()
                operation_type = list()
                for s in range(0, self.itemnumber):
                    item = create_route_map_item(None, None, None, None)
                    tmp_route_map.add_item(item, (s+1)*10 )

                    operation_type.append(item.type.name)
                    print("add route map item with seq %s to route map with type %s" % ((s+1)*10, item.type))

                start_time = time.time()
                # print("start_time is %d" % start_time)

                self.start_run()

                run_time = time.time() - start_time
                print("finished calculating the time")
                with open(file_name, 'a') as outfile:
                    outfile.write("%s,%s,%s\n" % (i, run_time, "_".join(operation_type)))
                print(i, run_time, "_".join(operation_type))

            # if i % 10 == 0:
            #     logger.info('Done with iteration %d out of %d' % (i + 1, repetitions))

        if self.scenario == Scenario.NetworkSizeTest:
            file_name = 'evaluation/logs/time_%s_%s_%s_%s.log' % (self.scenario, self.routemapnum, self.repetitions, '{:%Y%m%d-%H%M%S}'.format(
                datetime.datetime.now()))
            print("file name:%s" % file_name)
            with open(file_name, 'w') as outfile:
                outfile.write("%s\n" % self.get_heading())
            print("Heading: %s\n" % self.get_heading())
            for i in range(0, self.repetitions):
                if self.routemapnum == 1:
                    tmp_route_map.clear()
                    item1 = create_route_map_item(None, None, None, None)
                    tmp_route_map.add_item(item1, 10)

                if self.routemapnum == 2:
                    tmp_route_map.clear()
                    tmp_route_map_out.clear()
                    item1 = create_route_map_item(None, None, None, None)
                    item2 = create_route_map_item(None, None, None, None)
                    tmp_route_map.add_item(item1, 10)
                    tmp_route_map_out.add_item(item2, 10)

                if self.routemapnum == 4:
                    print("going to add 4 items to 4 route maps ")
                    tmp_route_map1.clear()
                    tmp_route_map_out1.clear()
                    tmp_route_map2.clear()
                    tmp_route_map_out2.clear()

                    item1 = create_route_map_item(None, None, None, None)
                    item2 = create_route_map_item(None, None, None, None)
                    item3 = create_route_map_item(None, None, None, None)
                    item4 = create_route_map_item(None, None, None, None)
                    tmp_route_map1.add_item(item1, 10)
                    tmp_route_map_out1.add_item(item2, 10)
                    tmp_route_map2.add_item(item3, 10)
                    tmp_route_map_out2.add_item(item4, 10)


                start_time = time.time()
                print("start_time is %d" % start_time)

                self.start_run()

                run_time = time.time() - start_time
                print("finished calculating the time")
                with open(file_name, 'a') as outfile:
                    outfile.write("%s,%s\n" % (i, run_time))
                print(i, run_time)


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

def create_a_match_or_set(field, itemtype, rm_items):
    routemaptype = route_map_random()  # permit or deny

    if field == RouteAnnouncementFields.IP_PREFIX or field == RouteAnnouncementFields.NEXT_HOP:
        pattern_ip = ip_network_random()
        print("enter create route map item")

        pattern = SymbolicField.create_from_prefix(pattern_ip, RouteAnnouncementFields.IP_PREFIX)

        if itemtype == ItemType.MATCH: # match ip prefix or next hop
            filtertype = filter_type_random() # GE or LE or EQUAL, next hop needs to be GE
            # routemaptype = route_map_random(routemaptype_p) # permit or deny
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
            # routemaptype = route_map_random(routemaptype_p)  # permit or deny
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
            filtertype = filter_type_random()  # GE or LE or EQUAL, next hop needs to be GE
            # routemaptype = route_map_random(routemaptype_p)  # permit or deny
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
            # routemaptype = route_map_random(routemaptype_p)
            print("add match: routemaptype: %s, routeannoucementfields: %s, pattern_ip:%s, filtertype:%s" % (
                routemaptype, field, pattern, filtertype))
            rm_items.add_match(routemaptype, field, pattern, filtertype)
        else:

            print("add action: routeannoucementfields: %s, pattern:%s" % (field, pattern))

            rm_items.add_action(field, pattern)

    return

def create_route_map_item(field, filtertype_p, routemaptype_p, itemtype_p):
    itemtype = item_type_random(itemtype_p) # match or action

    routemaptype = route_map_random(routemaptype_p) # permit or deny
    rm_items = RouteMapItems(routemaptype)

    if field == None:
        field_index = random.randint(0,5)
        field_list = [RouteAnnouncementFields.LOCAL_PREF, RouteAnnouncementFields.NEXT_HOP, RouteAnnouncementFields.AS_PATH,
                             RouteAnnouncementFields.COMMUNITIES, RouteAnnouncementFields.MED, RouteAnnouncementFields.LOCAL_PREF]
        field = field_list[field_index]
        # for randomly generate a match or an action make sure the type is correct
        if field == RouteAnnouncementFields.LOCAL_PREF:
            itemtype = ItemType.SET
        if field == RouteAnnouncementFields.IP_PREFIX:
            itemtype = ItemType.MATCH
        print("chosen field for route map item is %s" % field.name)
    if field == RouteAnnouncementFields.IP_PREFIX or field == RouteAnnouncementFields.NEXT_HOP:
        pattern_ip = ip_network_random()
        print("enter create route map item")

        pattern = SymbolicField.create_from_prefix(pattern_ip, RouteAnnouncementFields.IP_PREFIX)

        if itemtype == ItemType.MATCH: # match ip prefix or next hop
            filtertype = filter_type_random(filtertype_p) # GE or LE or EQUAL, next hop needs to be GE
            # routemaptype = route_map_random(routemaptype_p) # permit or deny
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
            # routemaptype = route_map_random(routemaptype_p)  # permit or deny
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
            # routemaptype = route_map_random(routemaptype_p)  # permit or deny
            rm_items.add_match(routemaptype, field, pattern, filtertype)
            print ("add match for community")
        if itemtype == ItemType.SET:
            rm_items.add_action(field, pattern)
            print("add action for community")
    if field == RouteAnnouncementFields.LOCAL_PREF:
        if itemtype == ItemType.MATCH:
            print ("Error: can't match on local pref, SET operation only. ")
        else:
            pattern = random.randint(1, 1000)
            rm_items.add_action(field, pattern)
            print("add action: routeannoucementfields: %s, pattern:%s" % (field, pattern))

    if field == RouteAnnouncementFields.MED:
        pattern = random.randint(1, 1000)
        if itemtype == ItemType.MATCH:
            filtertype = FilterType.EQUAL # doesn't matter actually
            # routemaptype = route_map_random(routemaptype_p)
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





