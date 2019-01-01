#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from model.announcement import RouteMapType, RouteAnnouncementFields, SymbolicField, FilterType
from model.router import RouteMap, RouteMapItems, RouteMapDirection

from model.network import NetworkTopology
from utils.logger import get_logger


logger = get_logger('test_networks', 'DEBUG')


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

    # expected output should be empty

    return network


def get_test9_network():
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

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement that matches Permit 39.0.0.0/9 GE Deny 39.0.99.0/25 LE

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

    # expected output should be empty

    return network


def get_test8_network():
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

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for [Permit 21.0.0.0/9 GE Deny 21.0.20.0/24 GE] [Permit 39.0.0.0/9 LE]

    return network


def get_test5_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # IMPORT
    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 11.0.0.0/24 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    # add an item that only permits announcements with prefix 11.0.0.0/16 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('11.0.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 20)

    # add an item that only permits announcements with prefix 11.0.0.0/8 or greater
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
    # and an announcement for 11.0.0.0/8 with deny 11.0.0.0/24 and 11.0.0.0/16, however the 11.0.0.0/24 is not
    # necessary, as it is included in the 11.0.0.0/16

    return network


def get_test6_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an export route-map
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

    # expected output should be an announcement for 11.0.0.0/[24-32], 11.0.0.0/[16-32] with deny 11.0.0.0/[24-32],
    # 11.0.0.0/[8-32] with deny 11.0.0.0/[16-32]

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
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    logger.debug("after adding match: pattern: %s" % pattern)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

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


def get_nexthop1_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.127.0.0/24 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.127.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    #tmp_out_route_map.add_item(rm_items, 10)

    #rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.127.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for IP: 39.0.0.0/[0-8] NEXT_HOP: 39.128.0.0/[16,32]

    return network


def get_nexthop2_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.127.0.0/24 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    #tmp_out_route_map.add_item(rm_items, 10)

    #rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.127.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)
    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for:
    #  [IP: [39.128.0.0 [8,16], IP Deny:[], NEXT_HOP: [39.127.1.0 GE 24], Next Hop Deny: []]
    #  [IP: [39.128.0.0 [0,16], IP Deny:[39.128.0.0 [8,16]], NEXT_HOP: [39.128.1.0 GE 24], Next Hop Deny: [39.127.1.0 GE 24]]

    return network


def get_set_nexthop_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.0.0.0 GE 8
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.128.24.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.24.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    #tmp_out_route_map.add_item(rm_items, 10)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.127.0.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.127.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.128.0.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.128.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)
    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add an item that permits announcements with ip prefix 39.128.25.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.25.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an action that sets next_hop to 29.0.0.0/8
    #pattern = SymbolicField.create_from_prefix('29.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_action(RouteAnnouncementFields.NEXT_HOP, '29.0.0.0/8')
    tmp_out_route_map.add_item(rm_items, 30)

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 40)

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for:
    #  [IP: [39.128.24.0 GE 24], IP Deny:[], NEXT_HOP: [39.127.1.0 GE 24], Next Hop Deny: []]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [39.128.1.0 GE 24], Next Hop Deny: [39.127.1.0 GE 24]]
    #  [IP: [39.128.25.0 GE 24], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [29.0.0.0 GE 8], Next Hop Deny: []]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24, 39.128.25.0 GE 24 ], NEXT_HOP: [39.0.0.0 GE 8], Next Hop Deny: [39.128.1.0 GE 24,39.127.1.0 GE 24]]

    return network


def get_set_3_fields_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.0.0.0 GE 8
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.128.24.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.24.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    #tmp_out_route_map.add_item(rm_items, 10)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.127.0.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.127.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)

    rm_items.add_action(RouteAnnouncementFields.MED, 200)
    tmp_out_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.128.0.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.128.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    rm_items.add_action(RouteAnnouncementFields.LOCAL_PREF, 150)
    tmp_out_route_map.add_item(rm_items, 20)
    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add an item that permits announcements with ip prefix 39.128.25.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.25.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an action that sets next_hop to 29.0.0.0/8
    #pattern = SymbolicField.create_from_prefix('29.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_action(RouteAnnouncementFields.NEXT_HOP, '29.0.0.0/8')
    tmp_out_route_map.add_item(rm_items, 30)

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 40)

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for:
    #  [IP: [39.128.24.0 GE 24], IP Deny:[], NEXT_HOP: [39.127.1.0 GE 24], Next Hop Deny: [], Local Pref: [50], MED: [200]]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [39.128.1.0 GE 24], Next Hop Deny: [39.127.1.0 GE 24], Local Pref: [150], MED: [50]]
    #  [IP: [39.128.25.0 GE 24], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [29.0.0.0 GE 8], Next Hop Deny: [], Local Pref: [50], MED: [50]]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24, 39.128.25.0 GE 24 ], NEXT_HOP: [39.0.0.0 GE 8], Next Hop Deny: [39.128.1.0 GE 24,39.127.1.0 GE 24], Local Pref: [50], MED: [50]]

    return network


def get_matchmed_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.0.0.0 GE 8
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)

    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.MED, 29, FilterType.EQUAL)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.128.24.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.24.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    #tmp_out_route_map.add_item(rm_items, 10)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.127.0.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.127.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)

    tmp_out_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.128.0.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.128.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)

    # add a match that permits announcements with MED 29
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.MED, 29, FilterType.EQUAL)

    rm_items.add_action(RouteAnnouncementFields.LOCAL_PREF, 150)

    tmp_out_route_map.add_item(rm_items, 20)
    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add an item that permits announcements with ip prefix 39.128.25.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.25.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an action that sets next_hop to 29.0.0.0/8
    #pattern = SymbolicField.create_from_prefix('29.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_action(RouteAnnouncementFields.NEXT_HOP, '29.0.0.0/8')
    tmp_out_route_map.add_item(rm_items, 30)

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 40)

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for:
    #  [IP: [39.128.24.0 GE 24], IP Deny:[], NEXT_HOP: [39.127.1.0 GE 24], Next Hop Deny: [], Local Pref: [None], MED: [29]]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [39.128.1.0 GE 24], Next Hop Deny: [39.127.1.0 GE 24], Local Pref: [150], MED: [29]]
    #  [IP: [39.128.25.0 GE 24], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [29.0.0.0 GE 8], Next Hop Deny: [], Local Pref: [none], MED: [x, deny [29]]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24, 39.128.25.0 GE 24 ], NEXT_HOP: [39.0.0.0 GE 8], Next Hop Deny: [39.128.1.0 GE 24,39.127.1.0 GE 24], Local Pref: [none], MED: [x, deny 29]]

    return network

# this is to test multiple unprocessed announcements are generated correctly after a route map item with multiple match fields has been applied
def get_matchapply_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.0.0.0 GE 8
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)

    #rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.MED, 29, FilterType.EQUAL)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.128.24.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.24.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an item that permits announcements with next hop 39.127.1.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.127.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)

    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for:
    #  [IP: [39.128.24.0 GE 24], IP Deny:[], NEXT_HOP: [39.127.1.0 GE 24], Next Hop Deny: [], Local Pref: [x], MED: [x], MED Deny: []]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [39.0.0.0/8], Next Hop Deny: [], Local Pref: [x], MED: [x], MED Deny[]]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[], NEXT_HOP: [39.0.0.0/8], Next Hop Deny: [39.127.1.0 GE 24], Local Pref: [x], MED: [x], deny []]

    return network


# this is to test multiple unprocessed announcements are generated correctly after a route map item with multiple match fields has been applied
def get_matchcommunity_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    network.add_community_list(["16:1", "16:2", "16:3", "16:4", "16:5", "16:6", "16:7", "16:8", "16:9", "16:10", "16:11", "16:12", "16:13",
                            "16:14", "16:15", "16:16"])
    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.128.0.0/16 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)
    # tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)

    #rm_items = RouteMapItems()
    # add an item that permits announcements with next hop 39.0.0.0 GE 8
    pattern = SymbolicField.create_from_prefix('39.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    logger.debug("pattern: %s" % pattern)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    logger.debug("after adding match: pattern: %s" % pattern)

    community_pattern = ["16:1", "16:2"]
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.COMMUNITIES, community_pattern, FilterType.GE)

    #rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.MED, 29, FilterType.EQUAL)
    tmp_in_route_map.add_item(rm_items, 10)
    logger.debug("adding item in the map: %s" % pattern)


    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that permits announcements with prefix 39.128.24.0 GE 24
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('39.128.24.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an item that permits announcements with next hop 39.127.1.0 GE 24
    pattern = SymbolicField.create_from_prefix('39.127.1.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)

    # rm_items.add_action(RouteAnnouncementFields.COMMUNITIES, ["16:3", "16:4"])
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.COMMUNITIES, ["16:1"], FilterType.GE)


    tmp_out_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.NEXT_HOP, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement for:
    #  [IP: [39.128.24.0 GE 24], IP Deny:[], NEXT_HOP: [39.127.1.0 GE 24], Next Hop Deny: [], Local Pref: [x], MED: [x], MED Deny: []]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[39.128.24.0 GE 24], NEXT_HOP: [39.0.0.0/8], Next Hop Deny: [], Local Pref: [x], MED: [x], MED Deny[]]
    #  [IP: [39.128.0.0 GE 16], IP Deny:[], NEXT_HOP: [39.0.0.0/8], Next Hop Deny: [39.127.1.0 GE 24], Local Pref: [x], MED: [x], deny []]

    return network


def get_matchaspath1_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an item that only permits announcements with as path that includes AS 3 to pass through
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W3\W.*", FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)

    # add an item that only permits announcements with that originates from AS 3, aka _3$
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W4\W", FilterType.GE)
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
    # try as path space 3 space 4 space

    return network

def get_matchaspath2_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an item that only permits announcements with as path that includes AS 3 to pass through
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W3\W.*", FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)

    # add an item that only permits announcements with that originates from AS 3, aka _3$
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.AS_PATH, ".*\W4\W", FilterType.GE)
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
    # try as path space 3 space 4 space

    return network


def get_matchaspath3_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an item that only permits announcements with as path that includes AS 3 to pass through
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W3\W.*", FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)

    # add an item that only permits announcements with that originates from AS 3, aka _3$
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.AS_PATH, ".*\W4\W", FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W5\W.*", FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement that matches 39.0.99.0/[9-25]
    # try as path space 3 space 5 space accepted
    # try as path space 3 space 4 space is not accepted

    return network


def get_matchaspath4_network():
    network = NetworkTopology('SingleRouterTwoNeighbors')

    # add all internal routers and their route-maps
    tmp_router = network.add_internal_router('main', '10.0.0.1/32', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)

    # add an item that only permits announcements with as path that includes AS 3 to pass through
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W3\W.*", FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_router.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    # pattern = SymbolicField.create_from_prefix('39.0.99.0/25', RouteAnnouncementFields.IP_PREFIX)
    # rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.LE)

    # add an item that only permits announcements with that originates from AS 3, aka _3$
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.AS_PATH, ".*\W4\W", FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.AS_PATH, ".*\W5\W.*", FilterType.GE)

    rm_items.add_action(RouteAnnouncementFields.AS_PATH, " 324 324")
    tmp_out_route_map.add_item(rm_items, 20)

    tmp_router.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '11.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('main', 'in_neighbor')
    network.add_peering('main', 'out_neighbor')

    # expected output should be an announcement that matches 39.0.99.0/[9-25]
    # try as path space 3 space 5 space accepted
    # try as path space 3 space 4 space is not accepted

    return network


def get_double_network():
    network = NetworkTopology('TwoRoutersTwoNeighbors')

    # add first internal routers and their route-maps
    tmp_r1 = network.add_internal_router('r1', '10.0.0.1', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER_1', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 13.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('13.0.0.0/9', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    tmp_r1.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '9.0.0.1')

    # add an export route-map
    tmp_out_route_map = RouteMap('EXPORT_FILTER_1', RouteMapType.PERMIT)

    # add an item that denies announcements with prefix 39.0.99.0/25 or smaller
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('13.0.0.0/24', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.DENY, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 10)

    # add an item that permits everything
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('0.0.0.0/0', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_out_route_map.add_item(rm_items, 20)

    tmp_r1.add_route_map(tmp_out_route_map, RouteMapDirection.OUT, '10.0.0.2')

    # add second internal routers and their route-maps
    tmp_r2 = network.add_internal_router('r2', '10.0.0.2', 10)

    # add an import route-map
    tmp_in_route_map = RouteMap('IMPORT_FILTER_2', RouteMapType.PERMIT)

    # add an item that only permits announcements with prefix 39.0.0.0/9 or greater
    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('13.0.0.0/16', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 10)

    rm_items = RouteMapItems()
    pattern = SymbolicField.create_from_prefix('13.0.0.0/8', RouteAnnouncementFields.IP_PREFIX)
    rm_items.add_match(RouteMapType.PERMIT, RouteAnnouncementFields.IP_PREFIX, pattern, FilterType.GE)
    tmp_in_route_map.add_item(rm_items, 20)

    tmp_r2.add_route_map(tmp_in_route_map, RouteMapDirection.IN, '10.0.0.1')

    # add all neighboring routers that advertise and receive routes
    network.add_external_router('in_neighbor', '9.0.0.1', 9)
    network.add_external_router('out_neighbor', '11.0.0.1', 11)

    # add the connections between the routers (e.g., full mesh between internal routers and a connection between
    # external routers and their specific counterpart internally
    network.add_peering('r1', 'in_neighbor')
    network.add_peering('r1', 'r2')
    network.add_peering('r2', 'out_neighbor')

    # expected output should be [13.0.0.0/[16-32], deny: 13.0.0.0/[24-32]] and [13.0.0.0/[9-32], deny: 13.0.0.0/[16-32]]

    return network
