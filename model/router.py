#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

from enum import Enum


class RouterType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


class RouteMapType(Enum):
    PERMIT = 1
    DENY = 2


class RouteMapDirection(Enum):
    IN = 1
    OUT = 2


class BGPRouter(object):
    def __init__(self, router_id, name, as_number, router_type):
        self.id = router_id
        self.name = name
        self.as_number = as_number
        self.type = router_type  # enum RouterType - internal or external
        self.interfaces = None

    def get_config(self):
        pass


class InternalBGPRouter(BGPRouter):
    def __init__(self, router_id, name, as_number):
        super(InternalBGPRouter, self).__init__(router_id, name, as_number, RouterType.INTERNAL)
        self.route_maps = dict()

    def add_route_map(self, route_map, direction, neighbor):
        tag = (direction, neighbor)
        self.route_maps[tag] = route_map


class ExternalBGPRouter(BGPRouter):
    def __init__(self, router_id, name, as_number):
        super(ExternalBGPRouter, self).__init__(router_id, name, as_number, RouterType.EXTERNAL)


class RouteMap(object):
    def __init__(self, name, rm_type):
        self.name = name
        self.sequence = list()
        self.items = dict()
        self.type = rm_type  # permit or deny

    def add_item(self, item, seq_number):
        self.sequence.append(seq_number)
        self.items[seq_number] = item

    def apply(self, announcement):
        # TODO add support for both deny and permit
        # TODO apply the route maps in proper order (sequence)
        # TODO make sure that splitting of announcement works when there is for example a deny clause
        processed_announcements = list()

        self.sequence.sort(reverse=True)
        for i in self.sequence:
            route_map_item = self.items[i]
            processed_announcements.append(route_map_item.apply(announcement))

        return processed_announcements


class RouteMapItems(object):
    def __init__(self):
        self.matches = list()
        self.actions = list()

    def add_match(self, match_type, field, pattern):
        tmp_rm_match = RouteMapMatch(match_type, field, pattern)
        self.matches.append(tmp_rm_match)

    def add_action(self, field, pattern):
        tmp_rm_action = RouteMapAction(field, pattern)
        self.actions.append(tmp_rm_action)

    def apply(self, announcement):
        tmp_announcement = announcement

        # Performing the matches
        for match in self.matches:
            tmp_announcement = match.apply(tmp_announcement)

        # TODO add actions

        return tmp_announcement


class RouteMapMatch(object):
    def __init__(self, match_type, field, pattern):
        self.type = match_type  # permit or deny
        self.field = field
        self.pattern = pattern

    def apply(self, announcement):
        # TODO add support for both deny and permit
        announcement.filter(self.field, self.pattern)
        return announcement


class RouteMapAction(object):
    def __init__(self, field, pattern):
        self.field = field
        self.pattern = pattern

    def apply(self, announcement):
        # TODO implement
        return announcement