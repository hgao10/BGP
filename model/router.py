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

class FilterType(Enum):
    EQUAL = 1
    GE = 2
    LE = 3

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
        # add support for next-hop self

        self.next_hop_self = router_id

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

        # process announcements in the order of ascending sequence number
        self.sequence.sort()
        for i in self.sequence:
            route_map_item = self.items[i]
            print('route_map_item in routemap.apply', route_map_item.matches, route_map_item.actions, i)
            processed_ann, to_be_processed_ann = route_map_item.apply(announcement)
            processed_announcements.append(processed_ann)
            # if route_map_item != self.items[-1]:
            if i != self.sequence[-1]:
                announcement = to_be_processed_ann

            # Does each processed announcement need to be fed into the next route-map-item?
            # match ip-prefix, then permit as path or set next hop, or do a set AND at the end per route-map

        return processed_announcements


class RouteMapItems(object):
    def __init__(self):
        self.matches = list()
        self.actions = list()

    def add_match(self, match_type, field, pattern, filter_type):
        tmp_rm_match = RouteMapMatch(match_type, field, pattern, filter_type)
        self.matches.append(tmp_rm_match)

    def add_action(self, field, pattern):
        tmp_rm_action = RouteMapAction(field, pattern)
        self.actions.append(tmp_rm_action)

    def apply(self, announcement):
        tmp_announcement = announcement

        # Applying the matches
        print("routemap_item, match list length", len(self.matches))
        for match in self.matches:
            tmp_announcement, next_announcement = match.apply(tmp_announcement)


        # Applying the actions
        # TODO add actions
        for action in self.actions:
            tmp_announcement, next_announcement = action.apply(tmp_announcement)

        return tmp_announcement, next_announcement


class RouteMapMatch(object):
    def __init__(self, match_type, field, pattern, filter_type):
        # TODO better model what the match actually does. For example, we need to distinguish between exact, greater or equal and less or equal prefix matches
        self.type = match_type  # permit or deny
        self.field = field
        self.pattern = pattern
        self.filter_type = filter_type # equal, ge, le

    def apply(self, announcement):
        # TODO add support for both deny and permit (e.g., for prefix-list, community-list etc)

        processed_ann, to_be_processed_ann = announcement.filter(self.field, self.pattern, self.filter_type)

        # TODO update the exclude field

        print('filtering routemap match item', self.field, self.pattern, self.filter_type)
        return processed_ann, to_be_processed_ann


class RouteMapAction(object):
    def __init__(self, field, pattern):
        self.field = field
        self.pattern = pattern

    def apply(self, announcement):
        # TODO implement
        # should just be set, instead of filtering
        current_announcement, next_announcement = announcement.filter(self.field, self.pattern, FilterType.EQUAL)
        print('filtering routemap action item', self.field, self.pattern)
        return current_announcement, next_announcement
