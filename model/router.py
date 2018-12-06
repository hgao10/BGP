#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

from enum import Enum
from utils.logger import get_logger

from model.announcement import FilterType, RouteAnnouncementFields


class RouterType(Enum):
    INTERNAL = 1
    EXTERNAL = 2


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
        self.logger = get_logger('RouteMap', 'DEBUG')

    def add_item(self, item, seq_number):
        self.sequence.append(seq_number)
        self.items[seq_number] = item

    def apply(self, announcement, route_map_direction):
        # TODO add support for both deny and permit
        # TODO make sure that splitting of announcement works when there is for example a deny clause
        processed_announcements = list()

        # TODO Edge case: 2 ip prefix matches with same sequence number while the first one is a superset of the second?
        # process announcements in the order of ascending sequence number
        self.sequence.sort()

        for i in self.sequence:
            route_map_item = self.items[i]
            self.logger.debug('Going to apply item seq %s in route map %s | current announcement is %s' % (i, self.name, announcement))
            processed_ann, to_be_processed_ann = route_map_item.apply(announcement)

            # if route_map_item != self.items[-1]:
            if i != self.sequence[-1]:
                announcement = to_be_processed_ann

            if processed_ann.hit == 1:
                processed_announcements.append(processed_ann)
                print('Routemap item %s applied, appending processed ann %s' % (i, processed_ann))

            # if i == self.sequence[-1]:
            #     processed_announcements.append(processed_ann)
            #     print('Routemap item %s applied, appending processed ann %s' % (i, processed_ann))

            if processed_ann.drop_next_announcement == 1:
                break

        return processed_announcements


class RouteMapItems(object):
    def __init__(self):
        self.matches = list()
        self.actions = list()
        self.logger = get_logger('RouteMapItems', 'DEBUG')

    def add_match(self, match_type, field, pattern, filter_type):
        self.logger.debug('adding a match with match_type %s | field: %s | pattern: %s| filter_type: %s' % (match_type, field, pattern, filter_type))
        tmp_rm_match = RouteMapMatch(match_type, field, pattern)

        if field == RouteAnnouncementFields.IP_PREFIX:
            self.logger.debug('Entered field : %s == RouteAnnouncementFields.IP_PREFIX and filter_type: %s and %s!' % (field, filter_type, FilterType.LE))

            if filter_type == FilterType.EQUAL:
                self.logger.debug('Entered filter_type == filtertype.equal if')

                pattern.prefix_mask = [pattern.prefixlen, pattern.prefixlen]
                pattern.prefix_type = FilterType.EQUAL

            if filter_type == FilterType.GE:
                self.logger.debug('Entered filter_type == filtertype.ge if')

                pattern.prefix_mask = [pattern.prefixlen, 32]
                pattern.prefix_type = FilterType.GE

            if filter_type == FilterType.LE:
                self.logger.debug('Entered filter_type == filtertype.le if')
                pattern.prefix_mask = [0, pattern.prefixlen]
                pattern.prefix_type = FilterType.LE
                self.logger.debug('pattern prefix mask is now %s' % pattern.prefix_mask)

        if field == RouteAnnouncementFields.NEXT_HOP:
            self.logger.debug('Entered field : %s == RouteAnnouncementFields.NEXT_HOP and filter_type: %s and match '
                              'type is %s' % (field, filter_type, match_type))

            if filter_type != FilterType.GE:

                self.logger.error("NEXT_HOP matches are restricted to longest prefix match, filter type should be GE")
            else:
                pattern.prefix_mask = [pattern.prefixlen, 32]
                pattern.prefix_type = FilterType.GE
                self.logger.debug("Add next hop match, pattern is %s and prefix mask is %s" % (pattern, pattern.prefix_mask))

        self.matches.append(tmp_rm_match)

    def add_action(self, field, pattern):
        tmp_rm_action = RouteMapAction(field, pattern)

        self.actions.append(tmp_rm_action)

    def apply(self, announcement):
        tmp_announcement = announcement

        # Applying the matches
        self.logger.debug("Read to apply routemap item, match list length: %s" % len(self.matches))
        overrall_hit = 0
        overrall_drop = 1
        for match in self.matches:
            tmp_announcement, next_announcement = match.apply(tmp_announcement)
            if announcement.hit == 0:
                overrall_hit = 0
                break
            else:
                overrall_hit = 1
            if announcement.drop_next_announcement == 0:
                # next announcement would only be dropped if all matches with the same seq # have drop next announcement set to 1
                overrall_drop = 0

            self.logger.debug("tmp_announcement: %s| next_announcement: %s" % (tmp_announcement, next_announcement))

        announcement.hit = overrall_hit
        announcement.drop_next_announcement = overrall_drop
        # Applying the actions
        # TODO add actions
        for action in self.actions:
            tmp_announcement, next_announcement = action.apply(tmp_announcement)

        return tmp_announcement, next_announcement


class RouteMapMatch(object):
    def __init__(self, match_type, field, pattern):
        # TODO better model what the match actually does. For example, we need to distinguish between exact, greater or equal and less or equal prefix matches
        self.type = match_type  # permit or deny
        self.field = field
        self.pattern = pattern
        self.logger = get_logger('RouteMapMatch', 'DEBUG')
        #self.filter_type = filter_type # equal, ge, le

    def apply(self, announcement):
        # TODO add support for both deny and permit (e.g., for prefix-list, community-list etc)

        self.logger.debug('Going to filter pattern: %s|pattern bitarray: %s| field: %s| match_type: %s' % (self.pattern, self.pattern.bitarray, self.field, self.type))
        processed_ann, to_be_processed_ann = announcement.filter(self.type, self.field, self.pattern)

        # TODO update the exclude field
        self.logger.debug('Has filtered pattern: %s' % self.pattern)

        return processed_ann, to_be_processed_ann


class RouteMapAction(object):
    def __init__(self, field, pattern):
        self.field = field
        self.pattern = pattern

    def apply(self, announcement):
        # TODO implement
        # should just be set, instead of filtering
        current_announcement, next_announcement = announcement.filter(self.type, self.field, self.pattern, FilterType.EQUAL)
        print('filtering routemap action item', self.field, self.pattern)

        return current_announcement, next_announcement
