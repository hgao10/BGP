#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from model.announcement import RouteMapType, RouteAnnouncementFields, SymbolicField, FilterType
from model.router import RouteMap, RouteMapItems, RouteMapDirection

from model.network import NetworkTopology


def get_simple_network():
    """
    Creates a NetworkTopology consisting of a single internal router (10.0.0.1) that is connected to two external
    routers (9.0.0.1 and 11.0.0.1). This topology allows to test basic functionality of in and out route-maps.
    :return: NetworkTopology
    """

    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map that only permits announcements with prefix 10.0.0.0/8 or greater
    tmp_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('10.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an route map item to the same import route map that set next-path to self
    rm_items = RouteMapItems()
    # pattern_next_hop = SymbolicField.create_from_prefix(tmp_router.next_hop_self, 1)
    # TODO need to add support for creating next-hop from an IP prefix list ?
    # rm_item_next_hop.add_action(RouteAnnouncementFields.NEXT_HOP, pattern_next_hop)
    pattern = SymbolicField.create_from_prefix('11.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_route_map.add_item(rm_items, 20)

    # add an export route-map that only permits announcements with prefix 10.0.10.0/24 or greater
    tmp_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('10.0.10.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.EQUAL)
    tmp_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add a route-map item matches on ip next-hop prefix-list

    # TODO add support for a deny clause
    rm_items = RouteMapItems()
    # pattern_next_hop = SymbolicField.create_from_prefix('10.0.0.1/32', 1)
    # what if routemap is deny and match is permit
    # rm_item_next_hop.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern_next_hop)
    pattern = SymbolicField.create_from_prefix('10.0.20.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_route_map.add_item(rm_items, 20)

    rm_items = RouteMapItems()
    # pattern_next_hop = SymbolicField.create_from_prefix('10.0.0.1/32', 1)
    # what if routemap is deny and match is permit
    # rm_item_next_hop.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern_next_hop)
    pattern = SymbolicField.create_from_prefix('11.0.20.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_route_map.add_item(rm_items, 30)

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    return network


def get_test1_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement that matches 39.0.99.0/[9-25]

    return network


def get_test2_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that denies announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement that matches 39.0.99.0/[26-32]

    return network


def get_test3_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.0.99.0/25 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be empty

    return network


def get_test4_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 21.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('21.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    # add an item that only permits announcements with prefix 21.0.20.0/24 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('21.0.20.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 20)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    tmp_in_route_map.add_item(rm_items, 30)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map that denies announcements with prefix 21.0.20.0/24 or greater
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that denies announcements with prefix 21.0.20.0/24 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('21.0.20.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for 21.0.0.0/[9-32] with deny 21.0.20.0/[24-32], and an announcement for
    # 39.0.0.0/[0-9]

    return network


def get_test5_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # IMPORT
    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 21.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    # add an item that only permits announcements with prefix 21.0.20.0/24 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 20)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 30)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for 11.0.0.0/24, an announcement for 11.0.0.0/16 with deny 11.0.0.0/24,
    # and an announcement for 11.0.0.0/8 with deny 11.0.0.0/24 and 11.0.0.0/16,

    return network


def get_test6_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an export route-map that denies announcements with prefix 21.0.20.0/24 or greater
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 11.0.0.0/24 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    # add an item that only permits announcements with prefix 11.0.0.0/16 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    # add an item that only permits announcements with prefix 11.0.0.0/8 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 30)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for 21.0.0.0/[9-32] with deny 21.0.20.0/[24-32], and an announcement for
    # 39.0.0.0/[0-9]

    return network


def get_test7_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    print("RouteMapType.PERMIT: %d RouteAnnouncementFields.IP_PREFIX: %d pattern: %s FilterType.LE:%d" % (RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE))

    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.127.0.0/24 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.127.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for 39.0.0.0/[0-8]

    return network