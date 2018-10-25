#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from model.announcement import RouteAnnouncementFields, SymbolicField
from model.router import RouteMap, RouteMapType, RouteMapItems, RouteMapDirection

from model.network import NetworkTopology


def get_simple_network():
    """
    Creates a NetworkTopology consisting of a single internal router (10.0.0.1) that is connected to two external
    routers (9.0.0.1 and 11.0.0.1). This topology allows to test basic functionality of in and out route-maps.
    :return: NetworkTopology
    """
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all interal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1', 10)

    # add an import route-map that only permits announcements with prefix 10.0.0.0/8 or greater
    tmp_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('10.0.0.0/8')
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern)
    tmp_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map that only permits announcements with prefix 10.0.10.0/24 or greater
    tmp_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('10.0.10.0/24')
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern)
    tmp_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    return network