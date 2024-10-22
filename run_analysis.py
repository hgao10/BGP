#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import argparse
import cmd
import os
import random

from model.test_networks import get_simple_network, get_double_network, get_test0_network, get_test1_network, get_test2_network, \
    get_test3_network, get_test4_network, get_test5_network, get_test6_network, get_test7_network, get_test8_network, \
    get_test9_network, get_nexthop1_network, get_nexthop2_network, get_set_nexthop_network, get_set_3_fields_network, \
    get_matchmed_network, get_matchapply_network, get_matchcommunity_network, get_matchaspath1_network, get_matchaspath2_network, \
    get_matchaspath3_network, get_matchaspath4_network, get_test_communities_network, get_test_next_hop_network, get_test_med_network

from utils.config_parser import load_network_from_configs


class TestSuite(cmd.Cmd):

    def __init__(self, *args, **kw):
        cmd.Cmd.__init__(self, *args, **kw)

        # current network
        self.network = None
        self.neighbor = None

        self.prompt = '> '
        # self.intro = 'Hi, '

        self.cmdloop()

    def do_exit(self, line=''):
        """exit: Leave the CLI"""
        return True

    def do_parse(self, line=''):
        if not os.path.exists(line):
            print('The supplied path does not exist.')
        else:
            self.network = load_network_from_configs(line)
            self.neighbor = None

    def do_load(self, line=''):
        """load: Load one of the provided network models or create a new one from configurations"""
        line = line.lower()

        if line == 'simple':
            self.network = get_simple_network()
        elif line == 'double':
            self.network = get_double_network()
        elif line == 'testmed':
            self.network = get_test_med_network()
        elif line == 'testcom':
            self.network = get_test_communities_network()
        elif line == 'testnh':
            self.network = get_test_next_hop_network()
        elif line == 'test0':
            self.network = get_test0_network()
        elif line == 'test1':
            self.network = get_test1_network()
        elif line == 'test2':
            self.network = get_test2_network()
        elif line == 'test3':
            self.network = get_test3_network()
        elif line == 'test4':
            self.network = get_test4_network()
        elif line == 'test5':
            self.network = get_test5_network()
        elif line == 'test6':
            self.network = get_test6_network()
        elif line == 'test7':
            self.network = get_test7_network()
        elif line == 'test8':
            self.network = get_test8_network()
        elif line == 'test9':
            self.network = get_test9_network()
        elif line == 'nexthop1':
            self.network = get_nexthop1_network()
        elif line == 'nexthop2':
            self.network = get_nexthop2_network()
        elif line == 'setnexthop':
            self.network = get_set_nexthop_network()
        elif line == 'set3fields':
            self.network = get_set_3_fields_network()
        elif line == 'matchmed':
            self.network = get_matchmed_network()
        elif line == 'matchapply':
            self.network = get_matchapply_network()
        elif line == 'matchcommunity':
            self.network = get_matchcommunity_network()

        elif line == 'matchaspath1':
            self.network = get_matchaspath1_network()
        elif line == 'matchaspath2':
            self.network = get_matchaspath2_network()
        elif line == 'matchaspath3':
            self.network = get_matchaspath3_network()
        elif line == 'matchaspath4':
            self.network = get_matchaspath4_network()
        else:
            print('The supplied topology is not known: %s. Try "simple" for example.' % line)
            return

        self.neighbor = "in_neighbor"

        print('Loaded %s topology with %d nodes and %d edges.' % (self.network.name, len(self.network.nodes), len(self.network.edges)))

    def do_neighbors(self, line):
        if self.network:
            neighbors = self.network.get_external_routers()
            print("The network has the following neighbors: %s" % (", ".join([str(neighbor) for neighbor in neighbors])))
        else:
            print('You need to load a network model before you can display its neighbors.')

    def do_set_neighbor(self, line):
        if self.network:
            if line in self.network.get_external_routers():
                self.neighbor = line
            else:
                print("The supplied neighbor is not known.")
        else:
            print('You need to load a network model before you can display its neighbors.')

    def do_run(self, line=''):
        """run: Run an analysis on the loaded network model by propagating a symbolic announcement"""
        if self.network:
            if not self.neighbor:
                self.neighbor = random.choice(list(self.network.get_external_routers()))
                print("No neighbor specified, picked %s randomly." % self.neighbor)


            print("Propagate announcement with AS community list :%s" % self.network.AS_community_list)
            outcome = self.network.propagate_announcement(self.neighbor, None, self.network.AS_community_list)

            output = 'From %s the following announcements make it through to the other neighbors:\n\n' % (self.neighbor, )
            for neighbor, announcements in sorted(outcome.items(), key=lambda x: x[0]):
                neighbor_id = self.network.get_router_id(neighbor)

                output += '\t%s (%s):\n' % (neighbor, neighbor_id)

                for i, announcement in enumerate(announcements):
                    output += '\t\t(%d): %s\n' % (i + 1, announcement)

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='enable debug output', action='store_true')

    args = parser.parse_args()

    debug = args.debug

    TestSuite()
