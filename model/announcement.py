#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from enum import Enum
from netaddr import IPNetwork
from bitstring import BitArray

from utils.logger import get_logger

from greenery.lego import parse
from greenery import lego
from colorama import Fore
from colorama import Style
import sys
import copy

def eprint(*args, **kwargs):
    print(Fore.RED, *args, Style.RESET_ALL, file=sys.stderr, **kwargs)

def debug(*args, **kwargs):
    print(Fore.YELLOW, *args, Style.RESET_ALL, file=sys.stderr, **kwargs)

class RouteMapType(Enum):
    PERMIT = 1
    DENY = 2

class RouteAnnouncementFields(Enum):
    IP_PREFIX = 1
    NEXT_HOP = 2
    AS_PATH = 3
    MED = 4
    LOCAL_PREF = 5
    COMMUNITIES = 6


class FilterType(Enum):
    EQUAL = 1
    GE = 2
    LE = 3


class RouteAnnouncement(object):
    """
    A BGP Route Announcement whose fields can be anywhere from fully symbolic to fully specified
    """

    def __init__(self, ip_prefix=None, next_hop=None, as_path=None, med=None, local_pref=None, communities=None, AS_community_list= None, debug=True):
        # TODO model all other fields
        self.logger = get_logger('RouteAnnouncement', 'DEBUG')
        if ip_prefix:
            self.ip_prefix = SymbolicField.create_from_prefix(ip_prefix, RouteAnnouncementFields.IP_PREFIX)
            self.ip_prefix_deny = []

        else:
            self.ip_prefix = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            self.ip_prefix_deny = []
            print('fully symbolicfield for ip_prefix', self.ip_prefix)

        if next_hop:
            self.next_hop = SymbolicField.create_from_prefix(next_hop, RouteAnnouncementFields.NEXT_HOP)
            self.next_hop_deny = []

        else:
            self.next_hop = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
            self.next_hop_deny = []
            print('fully symbolicfield for next_hop', self.next_hop)

        if local_pref:
            self.local_pref = local_pref

        else:
            # set default local pref to 50
            self.local_pref = "x"

        if med:
            self.med = med
            self.med_deny = []
        else:
            self.med = "x"
            self.med_deny = []

        if AS_community_list:
            self.AS_community_list = AS_community_list[:]
            self.logger.debug("Assign AS community list: %s" % self.AS_community_list)
        else:
            self.AS_community_list = []

        if communities:
            # map community value to community bitstring, set the corresponding bit to 1
            self.communities = Community(self.AS_community_list )
            # communities should be a list, currently only support to match AND type
            # TODO add support for OR
            self.communities.set_community_values_AND(communities)
            self.communities_deny = []
        else:
            # communities are 32 bit bit-string with all 1s
            # self.communities = BitArray('int:2*16=-1')
            self.logger.debug("Creating a Community object with as community list %s" % self.AS_community_list)

            self.communities = Community(self.AS_community_list)

            self.communities_deny = []
            self.logger.debug("Community bitarray: %s and As community list is %s" % (self.communities.community_bitarray, self.AS_community_list))

        if as_path:
            self.as_path = AsPath(regex=as_path)
        else:
            self.as_path = AsPath(regex=None)
            self.logger.debug(" Initialize as path regex to %s" % self.as_path.as_path_regex)

        self.hit = 0
        self.drop_next_announcement = 0

    def set_field(self, field, value):
        if field == RouteAnnouncementFields.IP_PREFIX:
            self.set_ip_prefix(value)
        elif field == RouteAnnouncementFields.NEXT_HOP:
            self.set_next_hop(value)
        elif field == RouteAnnouncementFields.AS_PATH:
            self.set_as_path(value)
        elif field == RouteAnnouncementFields.MED:
            self.set_med(value)
        elif field == RouteAnnouncementFields.LOCAL_PREF:
            self.set_local_pref(value)
        elif field == RouteAnnouncementFields.COMMUNITIES:
            # value here is a list of community strings ["16:3", "16:4"]
            self.set_communities(value)
        else:
            self.logger.error('Tried to set unknown field "%s with value "%s"' % (field, value))

    def set_ip_prefix(self, ip_prefix):
        # TODO
        pass

    def set_next_hop(self, next_hop):
        self.next_hop = SymbolicField.create_from_prefix(next_hop, RouteAnnouncementFields.IP_PREFIX)
        self.next_hop_deny = []
        pass

    def set_as_path(self, as_path):
        self.as_path.prepend_as_path(as_path)

        pass

    def set_med(self, med):
        self.med = med
        pass

    def set_local_pref(self, local_pref):
        self.local_pref = local_pref
        pass

    def set_communities(self, communities):
        self.communities.set_community_values_and(communities)  # communities is a list of the actual community values
        pass

    def __str__(self):
        # TODO add the other fields
        mask_ip_list = list()
        mask_ip_list_str = "[]"

        mask_next_hop_list = list()
        mask_next_hop_list_str ="[]"

        med_list = list()
        med_str = "[]"
        community_deny_list = list()
        community_deny_str = "[]"

        # as_path_deny_list = list()
        # as_path_deny_str = "[]"
        if len(self.ip_prefix_deny) != 0:
            for x in self.ip_prefix_deny:
                mask_ip = str(x) + " "+str(x.prefix_mask)
                mask_ip_list.append(("".join(str(mask_ip))))
                mask_ip_list_str = ", ".join(mask_ip_list)

        if len(self.next_hop_deny) != 0:
            for x in self.next_hop_deny:
                mask_next_hop = str(x) + " "+str(x.prefix_mask)
                mask_next_hop_list.append(("".join(str(mask_next_hop))))
                mask_next_hop_list_str = ", ".join(mask_next_hop_list)

        if len(self.med_deny) != 0:
            for x in self.med_deny:
                med_list.append(str(x))
            med_str = ", ".join(med_list)

        if len(self.communities_deny) != 0:
            for x in self.communities_deny:
                community_deny_list.append(str(x))
            community_deny_str = ", ".join(community_deny_list)

        return 'IP Prefix: %s, %s, IP Deny: %s, Next Hop: %s, Next Hop Deny: %s, Local Pref: %s, Med: %s, Med Deny: %s, Community: %s, ' \
               'Community_deny: %s, AS Path: %s\n' % (self.ip_prefix,self.ip_prefix.prefix_mask,mask_ip_list_str, self.next_hop,
                                                     mask_next_hop_list_str,
            self.local_pref, self.med, med_str, self.communities, community_deny_str, ",".join(self.as_path.as_path_list))

    def __repr__(self):
        return self.__str__()

    def __deepcopy__(self, memo):
        return deepcopy_with_sharing(self, shared_attribute_names=['logger'], memo=memo)

    def set_action(self, instance, value):
        pass

    @staticmethod
    # check if a ip prefix bit array has any impossible bit in it
    def check_zero(ip_prefix, length):
        zero = 0
        zero_position = 0
        for i in range(0, length):
            if not ip_prefix[2 * i] and not ip_prefix[2 * i + 1]:
                zero = 1
                zero_position = i
                break
            else:
                continue
        if zero == 0:
            zero_position = 32
        return zero, zero_position

    def check_zero_list(self, ip_list, ip_prefix):
        zero=0
        for x in ip_list:
            if self.check_zero(x.bitarray & ip_prefix.bitarray, 32) != 0 or\
                    ((x.bitarray_mask_type == FilterType.EQUAL) and (ip_prefix.bitarray_mask_type == FilterType.EQUAL)
                     and (x.bitarray != ip_prefix.bitarray)):
                zero = 1
                break

            else:
                continue
        return zero

    def check_subset(self, ip1, ip2):
        # check if ip2 is a subset of ip1
        is_subset = 0
        zero, zero_position = self.check_zero(ip1.bitarray & ip2.bitarray, 32)
        range = self.check_ip_range_overlap(ip1.prefix_mask, ip2.prefix_mask)
        if range[0] == -1:
            self.logger.error("IP mask ranges should be overlapping at this point")
        if ip1.prefix_mask[0] <= ip2.prefix_mask[0] and ip1.prefix_mask[1] >= ip2.prefix_mask[1]:
            # Superset is GE type
            if ip1.prefix_mask[1] == 32:
                if zero_position + 1 > ip1.prefix_mask[0]:
                    is_subset = 1
            # Superset is LE type
            if ip1.prefix_mask[0] == 0:
                self.logger.debug("comparing subset of LE types: zero position = %s" % ip2.prefix_mask[1])
                if zero_position + 1 > ip2.prefix_mask[1]:

                    is_subset = 1

        return is_subset

    def check_subset_deny(self, ip1, ip2):
        is_ip_subset_deny = 0
        if len(ip1) != 0:
            for x in ip1:
                if self.check_subset(x, ip2) == 1:
                    is_ip_subset_deny = 1
                    break
        self.logger.debug("pattern is a subset of the deny list %s" % is_ip_subset_deny)
        return is_ip_subset_deny

    def prefix_mask_intersect(self, pattern):
        if self.ip_prefix.prefix_mask[0]< pattern.ip_prefix.prefix_mask[0]:
            self.ip_prefix.prefix_mask[0] = pattern.ip_prefix.prefix_mask[0]
        if self.ip_prefix.prefix_mask[1]> pattern.ip_prefix.prefix_mask[1]:
            self.ip_prefix.prefix_mask[1] = pattern.ip_prefix.prefix_mask[1]

        return

    def check_le_overlap(self, ip1, ip2, limit):
        ip_prefix = ''
        self.logger.debug("check le overlap, ip1.bitarray: %s and ip2.bitarray: %s" % (ip1.bitarray, ip2.bitarray))
        fip = ip1.bitarray & ip2.bitarray

        zero, zero_position = self.check_zero(fip, 32)
        self.logger.debug("zero is found %s and zero_position is %s" % (zero, zero_position))
        if limit[0] < zero_position < limit[1]:
            prefix_len = zero_position
            print('Assign zero position to prefix_len %d' % prefix_len)
            for i in range(0, zero_position):
                # 0 -> 01
                if not fip[2 * i] and fip[2 * i + 1]:
                    ip_prefix += '0'
                # 1 -> 10
                elif fip[2 * i] and not fip[2 * i + 1]:
                    ip_prefix += '1'

            ip_prefix += '0' * (32 - prefix_len)

            prefix = '%s/%d' % (
            '.'.join(['%d' % int('0b%s' % ip_prefix[j * 8:(j + 1) * 8], 2) for j in range(0, 4)]), prefix_len)

            filtered_ip = SymbolicField.create_from_prefix(prefix, RouteAnnouncementFields.IP_PREFIX)
            filtered_ip.prefix_mask = [limit[0], prefix_len]
        elif zero_position == 32:
            prefix = ip1.ip_str_of_smaller_prefix_len(ip2)
            # check for filter pattern is a superset of the original announcement

            self.logger.debug("zero position is at 32 and smaller prefix is %s" % prefix)
            filtered_ip = SymbolicField.create_from_prefix(prefix, RouteAnnouncementFields.IP_PREFIX)
            filtered_ip.prefix_mask = limit
        else:
            # zero position is before range[0]
            filtered_ip = -1

        return filtered_ip

    def check_ge_le_overlap(self, ip1, ip2, limit):

        self.logger.debug("check GE LE overlap, ip1.bitarray: %s and ip2.bitarray: %s" % (ip1.bitarray, ip2.bitarray))
        fip = ip1.bitarray & ip2.bitarray
        ip_prefix = ''
        zero, zero_position = self.check_zero(fip, 32)
        self.logger.debug("zero is found %s and zero_position is %s" % (zero, zero_position))
        overlap = 0
        if ip2.prefix_type == FilterType.LE:
            # zero position could fall inside the range, but at least it needs to be greater than range[0]
            if zero_position + 1 > limit[0]:
                prefix_len = min(zero_position, limit[1])
                for i in range(0, prefix_len):
                    if not fip[2 * i] and fip[2 * i + 1]:
                        ip_prefix += '0'
                    # 1 -> 10
                    elif fip[2 * i] and not fip[2 * i + 1]:
                        ip_prefix += '1'

                ip_prefix += '0' * (32 - prefix_len)
                prefix = '%s/%d' % (
                    '.'.join(['%d' % int('0b%s' % ip_prefix[j * 8:(j + 1) * 8], 2) for j in range(0, 4)]), prefix_len)
                overlap = SymbolicField.create_from_prefix(prefix, RouteAnnouncementFields.IP_PREFIX)
                overlap.prefix_mask = [limit[0], prefix_len]
        elif ip2.prefix_type == FilterType.GE:
            if zero_position + 1 > limit[0]:
                # check if its two GE type overlapping
                if limit[1] == 32:
                    prefix= ip2.str_ip_prefix
                else:
                    prefix = ip1.str_ip_prefix
                overlap = SymbolicField.create_from_prefix(prefix, RouteAnnouncementFields.IP_PREFIX)
                overlap.prefix_mask = limit
                self.logger.debug("Overlap prefix_mask is two prefix intersection %s" % limit)

            else: # there is no overlapping
                overlap = -1
        elif ip2.prefix_type == FilterType.EQUAL:
            if zero_position +1 > ip2.prefix_mask[0]:
                prefix = ip2.str_ip_prefix
                overlap = SymbolicField.create_from_prefix(prefix, RouteAnnouncementFields.IP_PREFIX)
                overlap.prefix_mask = ip2.prefix_mask
            else:
                overlap = -1

        return overlap

    @ staticmethod
    def equal_two_symbolic_ip(ip1, ip2):
        if ip1.str_ip_prefix == ip2.str_ip_prefix:
            ip1.prefix_mask = ip2.prefix_mask
            return 0
        else:
            ip1.prefixlen = ip2.prefixlen
            ip1.bitarray = ip2.bitarray
            ip1.str_ip_prefix = ip2.str_ip_prefix
            ip1.prefix_mask = ip2.prefix_mask

        return

    @staticmethod
    def check_ip_range_overlap(prefix_mask1, prefix_mask2):

        lower_bound = max(prefix_mask1[0], prefix_mask2[0])
        upper_bound = min(prefix_mask1[1], prefix_mask2[1])
        if lower_bound <= upper_bound:
            return [lower_bound, upper_bound]
        # there is no intersection in ranges
        return [-1, -1]

    # match type could be eq, ge, le
    def filter(self, match_type, field, pattern):
        # TODO
        self.as_path.check_fsm('filter')
        original_fsm = self.as_path.as_path_fsm
        next = copy.deepcopy(self)
        next.as_path.as_path_fsm = original_fsm
        next.as_path.check_fsm('filter deep copy next')
        print("Done deep copy")

        # assume pattern can only be GE, LE or EQUAL. Currently not considering GE and LE at the match
        if field == RouteAnnouncementFields.IP_PREFIX:
            self.hit = 0
            self.drop_next_announcement = 0
            self.logger.debug("prefix_mask of ip1 %s" % self.ip_prefix.prefix_mask[0])
            limit = self.check_ip_range_overlap(self.ip_prefix.prefix_mask, pattern.prefix_mask)
            self.logger.debug("prefix_mask_intersect %s" % limit)
            # no overlaps between two ips, or the pattern to be matched is already in the deny list
            if limit[0] == -1 or self.check_subset_deny(self.ip_prefix_deny, pattern) == 1:
                self.hit = 0
                self.logger.debug("pattern is a subset of the deny list or no intersection")
            # if pattern is a superset of the current ip
            else:
                if self.check_subset(pattern, self.ip_prefix) == 1:
                    self.logger.debug("pattern is a superset of the current ip. Pattern: %s | Self: %s" % (pattern, self.ip_prefix))
                    # no leftovers from current match to be passed to the next
                    self.drop_next_announcement = 1
                    if match_type == RouteMapType.PERMIT:
                        self.hit = 1
                    else:
                        self.hit = 0
                        # everything is denied
                elif pattern.prefix_type == FilterType.LE:
                    self.logger.debug("Entering LE filtering")
                    # limit = self.check_ip_range_overlap(self.ip_prefix.prefix_mask, pattern.prefix_mask)
                    if limit[0] == 0:
                        # both ip ranges are LE type
                        ip_prefix_intersect = self.check_le_overlap(self.ip_prefix, pattern, limit)
                        if ip_prefix_intersect != -1:
                            if match_type == RouteMapType.PERMIT:
                                self.equal_two_symbolic_ip(self.ip_prefix, ip_prefix_intersect)
                                self.hit = 1
                                self.logger.debug("self ip_prefix %s" % self.ip_prefix)
                            else:
                                # match_type == denys
                                self.hit = 0
                                self.ip_prefix_deny.append(ip_prefix_intersect)
                                self.logger.debug("Next announcement would deny ip_prefix %s" % ip_prefix_intersect)

                            next.ip_prefix_deny.append(ip_prefix_intersect)
                        else:
                            # no overlap between ip prefix and pattern
                            self.hit = 0
                    else:
                        overlap = self.check_ge_le_overlap(self.ip_prefix, pattern, limit)
                        if overlap == -1:
                            # need to check up to limit[0] there is no impossible bit, otherwise the two ips don't intersect
                            # there is no overlap
                            self.hit = 0
                        else:
                            if match_type == RouteMapType.PERMIT:
                                self.hit = 1
                                self.equal_two_symbolic_ip(self.ip_prefix, overlap)
                            # else for deny no need to set ip_hit just add to the deny list
                            else:
                                self.ip_prefix_deny.append(overlap)
                            next.ip_prefix_deny.append(overlap)

                elif pattern.prefix_type == FilterType.GE:
                    self.logger.debug("Entering GE filtering")
                    # partially overlap
                    overlap = self.check_ge_le_overlap(self.ip_prefix, pattern, limit)
                    if overlap == -1:
                        self.hit = 0
                    else:
                        if match_type == RouteMapType.PERMIT:
                            self.hit = 1
                            self.equal_two_symbolic_ip(self.ip_prefix, overlap)
                            self.logger.debug("self.ip_prefix %s should have the same prefix mask as overlap %s" % (self.ip_prefix.prefix_mask, overlap.prefix_mask) )
                        else:
                            # deny case
                            self.ip_prefix_deny.append(overlap)

                        next.ip_prefix_deny.append(overlap)

                elif pattern.prefix_type == FilterType.EQUAL:
                    self.logger.debug("Entering EQUAL filtering")
                    if self.ip_prefix.prefix_mask[0] <= pattern.prefix_mask[0] <= self.ip_prefix.prefix_mask[1]:
                        overlap = self.check_ge_le_overlap(self.ip_prefix, pattern, limit)
                        if overlap == -1:
                            self.hit = 0
                        else:
                            if match_type == RouteMapType.PERMIT:
                                self.hit = 1
                                self.equal_two_symbolic_ip(self.ip_prefix, overlap)
                            else:
                                self.ip_prefix_deny.append(overlap)

                            next.ip_prefix_deny.append(overlap)

        elif field == RouteAnnouncementFields.NEXT_HOP:
            self.logger.debug('Before: Next hop - %s | Pattern - %s' % (self.next_hop, pattern))
            self.hit = 0
            self.drop_next_announcement = 0
            self.logger.debug("prefix_mask of ip1 %s" % self.next_hop.prefix_mask[0])
            limit = self.check_ip_range_overlap(self.next_hop.prefix_mask, pattern.prefix_mask)
            self.logger.debug("prefix_mask_intersect %s" % limit)
            # no overlaps between two ips, or the pattern to be matched is already in the deny list
            if limit[0] == -1 or self.check_subset_deny(self.next_hop_deny, pattern) == 1:
                self.hit = 0
                self.logger.debug("pattern is a subset of the deny list or no intersection")
            # if pattern is a superset of the current ip
            else:
                if self.check_subset(pattern, self.next_hop) == 1:
                    self.logger.debug(
                        "pattern is a superset of the current ip. Pattern: %s | Self: %s" % (pattern, self.next_hop))
                    # no leftovers from current match to be passed to the next
                    self.drop_next_announcement = 1
                    if match_type == RouteMapType.PERMIT:
                        self.hit = 1
                    else:
                        self.hit = 0
                        # everything is denied

                elif pattern.prefix_type == FilterType.GE:
                    self.logger.debug("Entering GE filtering")
                    # partially overlap
                    overlap = self.check_ge_le_overlap(self.next_hop, pattern, limit)
                    if overlap == -1:
                        self.hit = 0
                        self.logger.debug("next_hop_hit is a miss")
                    else:
                        if match_type == RouteMapType.PERMIT:
                            self.hit = 1
                            self.equal_two_symbolic_ip(self.next_hop, overlap)
                        else:
                            # deny case
                            self.next_hop_deny.append(overlap)

                        next.next_hop_deny.append(overlap)
                        self.logger.debug("next hop deny has %d items" % len(next.next_hop_deny))

            self.logger.debug('After: Next hop - %s' % (self.next_hop,))
            pass

        elif field == RouteAnnouncementFields.MED:
            # fully symbolic route at the beginning
            if self.med == 'x' and len(self.med_deny) > 0:
                deny = 0
                for x in self.med_deny:
                    if pattern == x:
                        deny = 1
                        break
                if deny == 0:
                    if match_type == RouteMapType.PERMIT:
                        self.med = pattern
                        self.hit = 1
                        self.logger.debug("next.med :%s | self.med %s " % (next.med, self.med))
                    else:
                        # deny case
                        self.med_deny.append(pattern)
                    next.med_deny.append(pattern)

            if self.med == pattern :
                if match_type == RouteMapType.PERMIT:
                    self.med = pattern
                    self.hit = 1
                else:
                    # deny case
                    self.med_deny.append(pattern)

                self.logger.debug("next.med :%s | self.med %s " % (next.med, self.med))
                # next.med_deny.append(pattern)

            if self.med == 'x' and self.med_deny == []:  # a specific med or fully symbolic route
                if match_type == RouteMapType.PERMIT:
                    self.med = pattern
                    self.hit = 1
                else:
                    # deny case
                    self.med_deny.append(pattern)

                self.logger.debug("next.med :%s | self.med %s " % (next.med, self.med))
                next.med_deny.append(pattern)

        # No matching to local pref
        # elif field == RouteAnnouncementFields.LOCAL_PREF:
        #     pass

        elif field == RouteAnnouncementFields.COMMUNITIES:
            community_match = self.communities.match_community_values_and(pattern)
            self.hit = 0
            self.logger.debug("match_community_value_and : %s" % community_match)
            zero, zero_position = self.check_zero(community_match, 16)
            if zero == 1:
                # match miss
                self.hit = 0
            else:
                if match_type == RouteMapType.PERMIT:
                    self.hit = 1
                    self.communities.community_bitarray = BitArray(hex=str(community_match))
                else:
                    # it is a match, but its deny
                    self.communities_deny.append(pattern) # deny list is [16:1, 16:2]
                    self.logger.debug("Deny community pattern: %s and self.hit is %s" % (pattern, self.hit))
                next.communities_deny.append(pattern)

        elif field == RouteAnnouncementFields.AS_PATH:
            # check if pattern is disjoint from the current as_path
            self.hit = 0
            pattern_regex = parse(pattern)

            pattern_fsm = pattern_regex.to_fsm()
            try:
                regex = lego.from_fsm(self.as_path.as_path_fsm)
                print("self.self.as_path.as_path_fsm converts to regex" % regex)
            except Exception:
                print ("unable to produce a regex from current self.as_path.as_path_fsm")
            self.logger.debug("as path ' 3 4 ' is contained in the self as path fsm %s" % self.as_path.as_path_fsm.accepts(" 3 4 "))

            if pattern_fsm.isdisjoint(self.as_path.as_path_fsm):
                self.hit = 0
                self.logger.debug("no overlap between current as path and pattern")
            else:
                intersect_fsm = self.as_path.as_path_fsm.intersection(pattern_fsm)
                if pattern_fsm.issuperset(self.as_path.as_path_fsm) is True:
                    self.logger.debug("current pattern is a superset of current as path fsm")
                    self.drop_next_announcement = 1

                if match_type == RouteMapType.PERMIT:
                    self.hit = 1

                    if self.as_path.as_path_fsm.issuperset(pattern_fsm):
                        self.logger.debug("current as path is a supperset of matching pattern")

                    self.as_path.as_path_fsm = intersect_fsm
                    self.as_path.update_regex()

                else:
                    # deny statement and doesn't care what updating self.as_path as it won't be appended to processed packet
                    self.hit = 0

                next.as_path.check_fsm('next announcement')
                next.as_path.as_path_fsm = self.as_path.as_path_fsm.difference(pattern_fsm)

                next.as_path.update_regex()
                self.logger.debug("self.drop_next_announcement %s" % self.drop_next_announcement)

        else:
            self.logger.error('Tried to set unknown field %s with value %s' % (field, pattern))

        return self, next


class AsPath(object):
    def __init__(self, regex=None):
        self.as_path_list = list()
        if regex:
            self.as_path_regex = parse(regex)
        else:
            # represent any pattern
            self.as_path_regex = parse(".*")

        self.as_path_fsm = self.as_path_regex.to_fsm()
        print ("initialize as path fsm from regex %s" % self.as_path_regex)
        print ("initialized as path fsm accepts ' 3 4' %s" % self.as_path_fsm.accepts(" 3 4 "))

        self. as_path_regex_outdated = False

    def check_fsm(self, caller='main'):
        debug ("%s as path fsm is the corresponding fsm to the regex %s"
               % (caller, self.as_path_fsm.equivalent(self.as_path_regex.to_fsm())))

    def prepend_as_path(self, element):
        new_list = [element] + self.as_path_list
        self.as_path_list = new_list[:]

    def update_regex(self):
        # self.as_path_regex_outdated = False
        try:
            self.as_path_regex = lego.from_fsm(self.as_path_fsm)
            self.as_path_regex_outdated = False
        except RuntimeError:
            self.as_path_regex_outdated = True

    # TODO figure out how to print sample as paths
    def __str__(self):
        print("as path list is: %s" % self.as_path_list)
        if self.as_path_fsm.empty() is False:
            print("As path regex contains non-zero as paths")
            try:
                if self.as_path_regex_outdated is True:
                    print(lego.from_fsm(self.as_path_fsm))
                else:
                    print(self.as_path_regex)
            except RuntimeError:
                print("regex is not reducible or printable, try testing as paths with fsm.accepts()")


class Community(object):
    def __init__(self, AS_community_list):
        self.community_bitarray = BitArray('int:32=-1')

        self.AS_community_list = AS_community_list[:]

        # self.logger = get_logger('Community', 'DEBUG')

    def match_community_values_and(self, match_list):  # match_list = ['16:1', '16:8']
        match_bit_string = BitArray('int:32=-1')

        match_item_index = list()
        for i in match_list:
            # represent the position of the second bit of '10'
            match_item_index.append(self.AS_community_list.index(i) * 2 + 1)

        # setting second bit to '0' to represent the match items and leave the first bit to 1
        match_bit_string.set(False, match_item_index)

        # carry out AND operation between current bitstring and match items
        and_match_bit_string = match_bit_string & self.community_bitarray

        # returns a bit string
        return and_match_bit_string

    def set_community_values_and(self, set_list):  # set_list = ['16:1', '16:2']

        set_item_index_true = list()
        set_item_index_false = list()
        for i in set_list:
            set_item_index_true.append(self.AS_community_list.index(i) * 2)
            set_item_index_false.append(self.AS_community_list.index(i) * 2 +1)

        self.community_bitarray.set(True, set_item_index_true)
        self.community_bitarray.set(False, set_item_index_false)

    def __str__(self):
        contained_communities = list()
        for i in range(16):
            if (self.community_bitarray[i*2] is True) and (self.community_bitarray[i*2 +1] is False):
                contained_communities.append(self.AS_community_list[i])

        return ','.join(contained_communities)


class SymbolicField(object):
    def __init__(self, field_type, length):
        # TODO efficiently detect if there is an impossible bit in the bitarray
        # TODO add support for all other fields
        # TODO add support for the most important operations (e.g., bitwise-and)

        self.logger = get_logger('SymbolicField', 'DEBUG')

        self.field_type = field_type
        #self.original_length = length
        # initialize BitArray to all 1s
        self.bitarray = BitArray('int:%d=-1' % (2*32, ))
        if field_type == RouteAnnouncementFields.IP_PREFIX or field_type == RouteAnnouncementFields.NEXT_HOP:
            self.str_ip_prefix = '0.0.0.0/0'
            self.prefix_mask = [0, 32]
            self.prefix_type = FilterType.GE
            self.prefixlen = 32

        # we use twice the length as we want to represent every bit by 2 bits to additionally allow
        # for wildcard and impossible bits
        # Z -> 00 > impossible bit
        # 0 -> 01 > 0 bit
        # 1 -> 10 > 1 bit
        # * -> 11 > wildcard bit

    def __len__(self):
        return len(self.bitarray)

    def __deepcopy__(self, memo):
        return deepcopy_with_sharing(self, shared_attribute_names=['logger'], memo=memo)

    def __str__(self):
        if self.field_type == RouteAnnouncementFields.IP_PREFIX or self.field_type == RouteAnnouncementFields.NEXT_HOP:  # convert HSA bit array to human-readable ip-prefix
            fip = self.bitarray

            ip_prefix = ''
            prefix_len = 32
            for i in range(0, 32):
                # Z -> 00
                if not fip[2 * i] and not fip[2 * i + 1]:
                    print('ERROR: invalid bit found')
                # 0 -> 01
                elif not fip[2 * i] and fip[2 * i + 1]:
                    ip_prefix += '0'
                # 1 -> 10
                elif fip[2 * i] and not fip[2 * i + 1]:
                    ip_prefix += '1'
                else:
                    #  map 11 t0 wildcard character 0
                    prefix_len = i
                    ip_prefix += '0' * (32 - prefix_len)
                    break

            prefix = '%s/%d' % ('.'.join(['%d' % int('0b%s' % ip_prefix[j * 8:(j + 1) * 8], 2) for j in range(0, 4)]), prefix_len)
            return prefix

        else:
            return str(self.bitarray)

    @ staticmethod
    def convert_to_hsa(str_ip_prefix, prefix_mask):
        ip_prefix = IPNetwork(str_ip_prefix)
        bin_ip_prefix = ip_prefix.ip.bin[2:]
        bitarray = BitArray('int:%d=-1' % (2 * 32,))
        if len(bin_ip_prefix) < 32:
            bin_ip_prefix = '0' * (32-len(bin_ip_prefix)) + bin_ip_prefix

        # create a new bitstring by translating bits to the four bit representation
        formatted_ip_prefix_bin = '0b'
        for i in range(0, 32):
            if prefix_mask[0] <= i <= (prefix_mask[1] - 1):
                # fill the prefix mask[x,y] with wildcard bits
                formatted_ip_prefix_bin += '11'
            else:
                if bin_ip_prefix[i] == '1':
                    formatted_ip_prefix_bin += '10'
                else:
                    formatted_ip_prefix_bin += '01'

        if type == RouteAnnouncementFields.IP_PREFIX:
            bitarray &= BitArray(formatted_ip_prefix_bin)

        return bitarray

    def ip_str_of_smaller_prefix_len(self, ip2):
        self.logger.debug("comparing two prefixes, prefix_mask 1: %s and prefix_mask2: %s and ip2.str_ip_prefix is %s" % (self.prefix_mask, ip2.prefix_mask, ip2.str_ip_prefix))
        if self.prefix_mask[1] < ip2.prefix_mask[1]:
            return self.str_ip_prefix
        else:
            return ip2.str_ip_prefix

    @staticmethod
    def create_from_prefix(str_ip_prefix, type):
        logger = get_logger('SymbolicField_create_from_prefix', 'DEBUG')
        ip_prefix = IPNetwork(str_ip_prefix)
        logger.debug('create from prefix: ip prefix object is - %s and prefix length - %s' % (ip_prefix, ip_prefix.prefixlen))

        # take binary representation of prefix without the leading '0b'
        bin_ip_prefix = ip_prefix.ip.bin[2:]
        logger.debug('bin_ip_prefix - %s and length is %s' % (bin_ip_prefix, len(bin_ip_prefix)))
        if len(bin_ip_prefix) < 32:
            bin_ip_prefix = '0' * (32-len(bin_ip_prefix)) + bin_ip_prefix

        # create a new bitstring by translating bits to the four bit representation
        formatted_ip_prefix_bin = '0b'
        for i in range(0, ip_prefix.prefixlen):
            if bin_ip_prefix[i] == '1':
                formatted_ip_prefix_bin += '10'
            else:
                formatted_ip_prefix_bin += '01'

        # fill the end with wildcard bits
        formatted_ip_prefix_bin += '11' * (32 - ip_prefix.prefixlen)
        logger.debug('Convert ip prefix to HSA representation %s and there are %s wildcards' % (formatted_ip_prefix_bin,
                                                                                                (32-ip_prefix.prefixlen)))
        # convert an ip to a bit-array
        if type == RouteAnnouncementFields.IP_PREFIX:
            symbolic_field = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            # symbolic bit array is 1111111 wild cards AND with specified ip-converted bit array
        elif type == RouteAnnouncementFields.NEXT_HOP:
            symbolic_field = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
        symbolic_field.bitarray &= BitArray(formatted_ip_prefix_bin)

        symbolic_field.prefixlen = ip_prefix.prefixlen
        symbolic_field.str_ip_prefix = str_ip_prefix
        print('symbolic_field.bitarray is %s and bitarray_mask length is %s' % (symbolic_field.bitarray,
                                                                                       symbolic_field.prefixlen))
        return symbolic_field


def deepcopy_with_sharing(obj, shared_attribute_names, memo=None):
    '''
    Deepcopy an object, except for a given list of attributes, which should
    be shared between the original object and its copy.

    obj is some object
    shared_attribute_names: A list of strings identifying the attributes that
        should be shared between the original and its copy.
    memo is the dictionary passed into __deepcopy__.  Ignore this argument if
        not calling from within __deepcopy__.
    '''
    assert isinstance(shared_attribute_names, (list, tuple))
    shared_attributes = {k: getattr(obj, k) for k in shared_attribute_names}

    if hasattr(obj, '__deepcopy__'):
        # Do hack to prevent infinite recursion in call to deepcopy
        deepcopy_method = obj.__deepcopy__
        obj.__deepcopy__ = None

    for attr in shared_attribute_names:
        del obj.__dict__[attr]

    clone = copy.deepcopy(obj)

    for attr, val in shared_attributes.items():
        setattr(obj, attr, val)
        setattr(clone, attr, val)

    if hasattr(obj, '__deepcopy__'):
        # Undo hack
        obj.__deepcopy__ = deepcopy_method
        del clone.__deepcopy__

    return clone


