#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


import networkx as nx

from model.router import InternalBGPRouter, ExternalBGPRouter, RouteMapDirection
from model.announcement import RouteAnnouncement
from utils.logger import get_logger


class NetworkTopology(nx.Graph):
    def __init__(self):
        super(NetworkTopology, self).__init__()

        # initialize logging
        self.logger = get_logger('NetworkTopology', 'INFO')

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

        # TODO check if we need to add router interfaces? probably for next-hop self/update source xyz

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
        if r1 in self.name_to_router_id:
            r1 = self.name_to_router_id[r1]

        if r2 in self.name_to_router_id:
            r2 = self.name_to_router_id[r2]

        if self.has_node(r1) and self.has_node(r2):
            super(NetworkTopology, self).add_edge(r1, r2, **attributes)
        else:
            self.logger.error('Either %s or %s do not exist' % (r1, r2))

    def propagate_announcement(self, neighbor, announcement=None):
        # TODO add proper copies of the announcements in the graph traversal, absolutely necessary for anything but
        # my trivial example.

        external_routers = dict()

        if not announcement:
            announcement = RouteAnnouncement()

        # map the neighbor to the router id, if the name was supplied
        if neighbor in self.name_to_router_id:
            neighbor_id = self.name_to_router_id[neighbor]
        else:
            neighbor_id = neighbor

        # find entry point from that neighbor
        ingress_routers = list(self.neighbors(neighbor_id))

        if len(ingress_routers) > 1:
            self.logger.debug('Looks like that neighboring router is connected to multiple internal routers. That '
                              'should not be the case.')

        ingress_router = ingress_routers[0]

        # starting from the ingress router perform a graph traversal until we end at another external router
        remaining_edges = [(neighbor_id, ingress_router, announcement)]

        while remaining_edges:
            prev_router_id, curr_router_id, announcement = remaining_edges.pop()
            curr_router = self.routers[curr_router_id]

            # pass announcement through import filter (if it exists)
            if (RouteMapDirection.IN, prev_router_id) in curr_router.route_maps:
                in_map = curr_router.route_maps[(RouteMapDirection.IN, prev_router_id)]
                local_announcements = in_map.apply(announcement)
            else:
                local_announcements = [announcement]

            for local_announcement in local_announcements:
                # iterate over all neighbors and pass through respective export filter (if it exists)
                # and skip the neighbor from which the announcement was received
                for neighbor_id in self.neighbors(curr_router_id):
                    if neighbor_id == prev_router_id:
                        continue
                    else:
                        if (RouteMapDirection.OUT, neighbor_id) in curr_router.route_maps:
                            out_map = curr_router.route_maps[(RouteMapDirection.OUT, neighbor_id)]

                            export_announcement = out_map.apply(local_announcement)
                        else:
                            export_announcement = local_announcement

                        if neighbor_id in self.peers:
                            external_routers[self.router_id_to_name[neighbor_id]] = export_announcement
                        else:
                            remaining_edges.append((curr_router_id, neighbor_id, export_announcement))

        return external_routers