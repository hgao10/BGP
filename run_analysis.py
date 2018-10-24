#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import argparse
import cmd

from model.announcement import RouteAnnouncementFields, SymbolicField
from model.router import RouteMap, RouteMapType, RouteMapItems, RouteMapDirection

from model.network import NetworkTopology


class TestSuite(cmd.Cmd):
    prompt = '> '

    def __init__(self, *args, **kw):
        cmd.Cmd.__init__(self, *args, **kw)

        # current network
        self.network = None

        self.cmdloop()

    def do_exit(self, line=''):
        """exit: Leave the CLI"""
        return True

    def do_load(self, line=''):
        self.network = NetworkTopology()

        # add all interal routers and their route-maps
        tmp_router = self.network.add_internal_router('main', '10.0.0.1', 10)

        tmp_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
        rm_items = RouteMapItems()
        pattern = SymbolicField.create_from_prefix('10.0.0.0/8')
        rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern)
        tmp_route_map.add_item(rm_items, 10)

        tmp_router.add_route_map(tmp_route_map, RouteMapDirection.IN, '9.0.0.1')

        tmp_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
        rm_items = RouteMapItems()
        pattern = SymbolicField.create_from_prefix('10.0.10.0/24')
        rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern)
        tmp_route_map.add_item(rm_items, 10)

        tmp_router.add_route_map(tmp_route_map, RouteMapDirection.OUT, '11.0.0.1')

        # add all neighboring routers that advertise and receive routes
        self.network.add_external_router('in_neighbor', '9.0.0.1', 9)
        self.network.add_external_router('out_neighbor', '11.0.0.1', 11)

        # add the connections between the routers (e.g., full mesh between internal routers and a connection between
        # external routers and their specific counterpart internally
        self.network.add_peering('main', 'in_neighbor')
        self.network.add_peering('main', 'out_neighbor')

    def do_run(self, line=None):
        if self.network:
            neighbor = 'in_neighbor'

            outcome = self.network.propagate_announcement(neighbor)

            output = 'From %s the following announcements make it through to the other neighbors:\n\n' % (neighbor, )
            for neighbor, announcement in outcome.items():
                output += '\t%s: %s\n' % (neighbor, announcement)
            print(output)
        else:
            print('You need to load a network model before you can run the symbolic execution.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='enable debug output', action='store_true')
    args = parser.parse_args()

    debug = args.debug

    TestSuite()
