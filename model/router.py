#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

from enum import Enum
from utils.logger import get_logger

from model.announcement import FilterType, RouteAnnouncementFields, RouteAnnouncement
import copy


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
        self.logger.disabled = True

    def __str__(self):
        output = ""
        self.sequence.sort()
        for seq in self.sequence:
            output += "route-map %s %s %d\n%s\n" % (self.name, self.items[seq].type, seq, self.items[seq])
        return output

    def add_item(self, item, seq_number):
        self.sequence.append(seq_number)
        self.items[seq_number] = item

    def clear(self):
        self.items.clear()
        self.sequence = list()

    def apply(self, announcement, route_map_direction):
        processed_announcements = list()

        # process announcements in the order of ascending sequence number
        self.sequence.sort()
        list_to_be_processed_ann = list()

        announcement_list = list()
        announcement_list.append(announcement)

        # if the route map is empty, let everything pass through
        if len(self.sequence) == 0:
            self.logger.debug("route map is empty, let everything pass through")
            processed_announcements = [announcement]
        for i in self.sequence:
            route_map_item = self.items[i]

            list_to_be_processed_ann.clear()
            self.logger.debug("len of announcement_list is %s" % len(announcement_list))
            for ann in announcement_list:
                self.logger.debug('Going to apply item seq %s in route map %s | current announcement is %s' % (
                i, self.name, ann))
                processed_ann, to_be_processed_ann = route_map_item.apply(ann)
                #to_be_processed_ann is a list
                if processed_ann.hit == 1:
                    processed_announcements.append(processed_ann)
                    # print('Routemap item %s applied, appending processed ann %s' % (i, processed_ann))
                for to_be_ann in to_be_processed_ann:
                    list_to_be_processed_ann.append(to_be_ann)
                    self.logger.debug("append %s to list_to_be_processed" % to_be_ann)
            # if route_map_item != self.items[-1]:
            if i != self.sequence[-1]:
                # announcement_list = copy.deepcopy(list_to_be_processed_ann)
                announcement_list = list_to_be_processed_ann[:]
                listA = list()
                for i in list_to_be_processed_ann:
                    listA.append(str(i))
                    self.logger.debug("announcement list is: %s" % (" ,".join(listA)))

            if processed_ann.drop_next_announcement == 1:
                # print("break from routemapapply ")
                break

        return processed_announcements


class RouteMapItems(object):
    def __init__(self, type):
        self.matches = list()
        self.actions = list()
        self.type = type

        self.logger = get_logger('RouteMapItems', 'DEBUG')
        self.logger.disabled = True

    def __str__(self):
        match_str = "\n\t".join([str(match) for match in self.matches])
        action_str = "\n\t".join([str(action) for action in self.actions])
        output = "\t%s\n\t%s" % (match_str, action_str)
        return output

    def add_match(self, match_type, field, pattern, filter_type):
        self.logger.debug('adding a match with match_type %s | field: %s | pattern: %s| filter_type: %s' % (match_type, field, pattern, filter_type))
        tmp_rm_match = RouteMapMatch(match_type, field, pattern)

        if field == RouteAnnouncementFields.IP_PREFIX:
            self.logger.debug('Entered field : %s == RouteAnnouncementFields.IP_PREFIX and filter_type: %s ' % (field, filter_type))

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
        # announcement.as_path.check_fsm("Before copy announcement")
        original_fsm = announcement.as_path.as_path_fsm
        tmp_announcement = copy.deepcopy(announcement)
        tmp_announcement.as_path.as_path_fsm = original_fsm
        # tmp_announcement.as_path.check_fsm("After copy tmp announcement")

        # Applying the matches
        self.logger.debug("Read to apply routemap item, match list length: %s" % len(self.matches))
        overall_hit = 0
        overall_drop = 1

        item_next_announcements = list()

        for match in self.matches:

            tmp_announcement, next_announcement = match.apply(tmp_announcement)

            self.logger.debug("after apply match on field %s, tmp_announcement: %s| next_announcement: %s" % (match.field, tmp_announcement, next_announcement))

            if match.field == RouteAnnouncementFields.IP_PREFIX:
                item_next_announcement = copy.deepcopy(announcement)
                item_next_announcement.ip_prefix = next_announcement.ip_prefix
                item_next_announcement.ip_prefix_deny = next_announcement.ip_prefix_deny

            if match.field == RouteAnnouncementFields.NEXT_HOP:
                item_next_announcement = copy.deepcopy(announcement)
                item_next_announcement.next_hop = next_announcement.next_hop
                item_next_announcement.next_hop_deny = next_announcement.next_hop_deny

            if match.field == RouteAnnouncementFields.MED:
                item_next_announcement = copy.deepcopy(announcement)
                item_next_announcement.med = next_announcement.med
                item_next_announcement.med_deny = next_announcement.med_deny

            if match.field == RouteAnnouncementFields.COMMUNITIES:
                item_next_announcement = copy.deepcopy(announcement)
                item_next_announcement.communities = next_announcement.communities
                item_next_announcement.communities_deny = next_announcement.communities_deny
                item_next_announcement.AS_community_list = next_announcement.AS_community_list

            if match.field == RouteAnnouncementFields.AS_PATH:
                item_next_announcement = copy.deepcopy(announcement)
                item_next_announcement.as_path = next_announcement.as_path

            if match.field != RouteAnnouncementFields.AS_PATH:
                # restore changes brought by deepcopy
                item_next_announcement.as_path.as_path_fsm = original_fsm
                # item_next_announcement.as_path.check_fsm("After copy item next announcement")

            item_next_announcements.append(item_next_announcement)

            self.logger.debug("after apply match on field %s, item_next_announcement: %s" % (
                match.field, item_next_announcement))

            # if announcement.drop_next_announcement == 0:
            if tmp_announcement.drop_next_announcement == 0:
                # next announcement would only be dropped if all matches with the same seq # have drop next announcement set to 1
                overall_drop = 0

            self.logger.debug("announcement hit: %s and tmp_announcement hit: %s" % (announcement.hit, tmp_announcement.hit))

            # this needs to be checked after drop next announcement, otherwise a deny clause would result in dropping the next announcement because
            #  of break statement
            # if announcement.hit == 0:
            if tmp_announcement.hit == 0:
                overall_hit = 0
                break
            else:
                overall_hit = 1

        listA= list()
        for i in item_next_announcements:
            listA.append(str(i))
            self.logger.debug("item_next_announcement list: %s" % (" ,".join(listA)))

        # announcement.hit = overall_hit
        tmp_announcement.hit = overall_hit

        if tmp_announcement.hit == 0:
            # if one of match fails, next announcement is the same as the unprocessed announcement
            self.logger.debug("Overall hit is zero, No match for item" )
            item_next_announcements.clear()
            item_next_announcements.append(announcement)
            tmp_announcement = announcement
            tmp_announcement.hit = 0

        # announcement.drop_next_announcement = overall_drop
        tmp_announcement.drop_next_announcement = overall_drop
        # Applying the actions if all matches match or there is no match
        if overall_hit == 1 or len(self.matches) == 0:
            tmp_announcement.hit = 1
            for action in self.actions:
                action.apply(tmp_announcement)

        return tmp_announcement, item_next_announcements


class RouteMapMatch(object):
    def __init__(self, match_type, field, pattern):
        # TODO better model what the match actually does. For example, we need to distinguish between exact, greater or equal and less or equal prefix matches
        self.type = match_type  # permit or deny
        self.field = field
        self.pattern = pattern
        self.logger = get_logger('RouteMapMatch', 'DEBUG')
        self.logger.disabled = True
        #self.filter_type = filter_type # equal, ge, le

    def apply(self, announcement):
        # TODO add support for both deny and permit (e.g., for prefix-list, community-list etc)

        # self.logger.debug('Going to filter pattern: %s|pattern bitarray: %s| field: %s| match_type: %s' % (self.pattern, self.pattern.bitarray, self.field, self.type))
        processed_ann, to_be_processed_ann = announcement.filter(self.type, self.field, self.pattern)

        # TODO update the exclude field
        self.logger.debug('Has filtered pattern: %s' % self.pattern)

        return processed_ann, to_be_processed_ann

    def __str__(self):
        output = "match %s %s (%s)" % (self.field, self.pattern, self.type)
        return output


class RouteMapAction(object):
    def __init__(self, field, pattern):
        self.field = field
        self.pattern = pattern

    def apply(self, announcement):
        # TODO implement
        # should just be set, instead of filtering
        #current_announcement, next_announcement = announcement.filter(self.type, self.field, self.pattern, FilterType.EQUAL)
        # print('Set field %s to pattern %s' % (self.field, self.pattern))
        announcement.set_field(self.field, self.pattern)
        return

    def __str__(self):
        output = "set %s %s" % (self.field, self.pattern)
        return output
