#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import sys
import networkx as nx
from collections import defaultdict

from model.router import InternalBGPRouter, ExternalBGPRouter, RouteMapDirection
from model.announcement import RouteAnnouncement
from utils.logger import get_logger


class NetworkTopology(nx.Graph):
    def __init__(self, name):
        super(NetworkTopology, self).__init__()

        # initialize logging
        self.logger = get_logger('NetworkTopology', 'DEBUG')

        self.name = name

        # dict of router id to router
        self.routers = dict()
        self.peers = dict()

        self.name_to_router_id = dict()
        self.router_id_to_name = dict()

    def add_internal_router(self, name, router_id, as_number, **attributes):
        super(NetworkTopology, self).add_node(router_id, **attributes)

        self.routers[router_id] = InternalBGPRouter(router_id, name, as_number)

        self.name_to_router_id[name] = router_id
        self.router_id_to_name[router_id] = name


        # TODO check if we need to add router interfaces? probably for next-hop self, use interface ip/


        return self.routers[router_id]

    def add_external_router(self, name, router_id, as_number, **attributes):
        super(NetworkTopology, self).add_node(router_id, **attributes)

        self.peers[router_id] = ExternalBGPRouter(router_id, name, as_number)

        self.name_to_router_id[name] = router_id
        self.router_id_to_name[router_id] = name

    def add_peering(self, r1, r2, **attributes):
        """
        Add a directed link between router r1 and r2 with the given cost
        """

        # in case router names are supplied, map them to the corresponding id
        r1_id = self.get_router_id(r1)
        r2_id = self.get_router_id(r2)

        if self.has_node(r1_id) and self.has_node(r2_id):
            super(NetworkTopology, self).add_edge(r1_id, r2_id, **attributes)
        else:
            self.logger.error('Either %s or %s do not exist' % (r1_id, r2_id))

    def propagate_announcement(self, neighbor, announcement=None):
        # TODO add proper copies of the announcements in the graph traversal, absolutely necessary for anything but my trivial example.

        # TODO properly handle announcements, every route-map is a mapping from a single announcement to multiple announcements - this has to be considered
        #

        # dict to store all the announcements that arrived at all the neighbors after propagation
        external_routers = defaultdict(list)

        # if no announcement is supplied, just take the fully symbolic one
        if not announcement:
            announcement = RouteAnnouncement()
            print('taking the fully symbolic announcement:', announcement)

        # map the neighbor to the router id, if the name was supplied
        neighbor_id = self.get_router_id(neighbor)
        print('get in_neighbors ip, should be 9.0', neighbor_id)

        # find entry point from that neighbor
        # returns a list of internal border routers that are connected to the external neighbor (expect a total of one)
        ingress_routers = list(self.neighbors(neighbor_id))
        print('returns the internal router that is directly connected to the neighbor, should just be 1, 10.0.0', ingress_routers)
        ingress_router = ingress_routers[0]

        if len(ingress_routers) > 1:
            self.logger.debug('Looks like that neighboring router is connected to multiple internal routers. '
                              'That should not be the case.')

        # starting from the ingress router perform a graph traversal until we end at another external router
        remaining_edges = [(neighbor_id, ingress_router, announcement)]

        # performing a DFS on the BGP topology graph, starting with the entry point
        while remaining_edges:
            print('remaining edges: ', remaining_edges)
            prev_router_id, curr_router_id, announcement = remaining_edges.pop()
            curr_router = self.routers[curr_router_id]  # .routers is a dict of internal BGP routers indexed by ip addr

            # pass announcement through import filter (if it exists)
            if (RouteMapDirection.IN, prev_router_id) in curr_router.route_maps:
                in_map = curr_router.route_maps[(RouteMapDirection.IN, prev_router_id)]
                print('before applying route_map_in, the announcement is', announcement)
                local_announcements = in_map.apply(announcement)
                print('assigning route-mapping-in to local_announcement', local_announcements)
            else:
                local_announcements = [announcement]

            for local_announcement in local_announcements:
                # iterate over all neighbors and pass through respective export filter (if it exists)
                # and skip the neighbor from which the announcement was received as it is not announced back

                # TODO make sure that iBGP announcements are not sent over more than one hop
                for neighbor_id in self.neighbors(curr_router_id):
                    print('current neighbor id is', neighbor_id)
                    if neighbor_id == prev_router_id:
                        print('Find in_neighbor in the return list, continue', neighbor_id)
                        continue
                    else:
                        if (RouteMapDirection.OUT, neighbor_id) in curr_router.route_maps:
                            out_map = curr_router.route_maps[(RouteMapDirection.OUT, neighbor_id)]
                            print('going to apply OUT_MAP')
                            export_announcements = out_map.apply(local_announcement)
                            print('OUT route map filtering', export_announcements)
                        else:
                            export_announcements = [local_announcement]

                        if neighbor_id in self.peers:
                            external_routers[self.router_id_to_name[neighbor_id]].extend(export_announcements)
                            print('{} : {}'.format(self.router_id_to_name[neighbor_id], export_announcements))
                        else:
                            for export_announcement in export_announcements:
                                remaining_edges.append((curr_router_id, neighbor_id, export_announcement))
                                print('remaining edges.append(curr_router_id, neighbor_id, export_announcement)',
                                      curr_router_id, neighbor_id, export_announcement)

        return external_routers

    def get_router_id(self, identifier):
        if identifier in self.name_to_router_id:
            router_id = self.name_to_router_id[identifier]
            return router_id
        elif identifier in self.router_id_to_name:
            return identifier
        else:
            self.logger.error('Unknown router: %s.' % (identifier, ))
            sys.exit(0)
