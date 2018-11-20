#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from enum import Enum
from netaddr import IPNetwork
from bitstring import BitArray

from utils.logger import get_logger

import copy

from model.router import RouteMapType


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

    def __init__(self, ip_prefix=None, next_hop=None, as_path=None, med=None, local_pref=None, communities=None, debug=True):
        # TODO model all other fields
        if ip_prefix:
            self.ip_prefix = SymbolicField.create_from_prefix(ip_prefix, RouteAnnouncementFields.IP_PREFIX)
            self.ip_prefix_deny = []
            self.ip_deny_display = []
        else:
            self.ip_prefix = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            self.ip_prefix_deny = []

            self.ip_deny_display = []
            print('fully symbolicfield for ip_prefix', self.ip_prefix)

        if next_hop:
            self.next_hop = SymbolicField.create_from_prefix(next_hop, RouteAnnouncementFields.NEXT_HOP)
        else:
            self.next_hop = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
            print('fully symbolicfield for next_hop', self.next_hop)

        self.ip_hit = 0
        self.drop_next_announcement = 0
        self.as_path = as_path
        self.med = med
        self.local_pref = local_pref
        self.communities = communities

        self.logger = get_logger('RouteAnnouncement', 'DEBUG')

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
            self.set_communities(value)
        else:
            self.logger.error('Tried to set unknown field "%s with value "%s"' % (field, value))

    def set_ip_prefix(self, ip_prefix):
        # TODO
        pass

    def set_next_hop(self, next_hop):
        # TODO
        pass

    def set_as_path(self, as_path):
        # TODO
        pass

    def set_med(self, med):
        # TODO
        pass

    def set_local_pref(self, local_pref):
        # TODO
        pass

    def set_communities(self, communities):
        # TODO
        pass

    def __str__(self):
        # TODO add the other fields
        if len(self.ip_prefix_deny) != 0:
            for x in self.ip_prefix_deny:
                self.ip_deny_display = ("".join(str(x)))
        return 'IP Prefix: %s, IP Deny: %s,  Next Hop: %s' % (self.ip_prefix, self.ip_deny_display, self.next_hop)

    def __repr__(self):
        return self.__str__()

    def set_action(self, instance, value):
        pass

    @staticmethod
    # check if a ip prefix bit array has any impossible bit in it
    def check_zero(ip_prefix):
        zero = 0
        for i in range(0, 32):
            if not ip_prefix[2 * i] and not ip_prefix[2 * i + 1]:
                zero = 1
                break
            else:
                continue
        return zero

    def check_zero_list(self, ip_list, ip_prefix):
        zero=0
        for x in ip_list:
            if self.check_zero(x.bitarray & ip_prefix.bitarray) != 0 or\
                    ((x.bitarray_mask_type == FilterType.EQUAL) and (ip_prefix.bitarray_mask_type == FilterType.EQUAL)
                     and (x.bitarray != ip_prefix.bitarray)):
                zero = 1
                break

            else:
                continue
        return zero

    # check if ip2 is ip1's subset or superset by comparing ip prefix and length of each mask
    def check_ip_subset(self, ip1, ip2):
        is_subset = 0
        # is_superset = 0
        ip_and = ip1.bitarray & ip2.bitarray
        # if the lengths are equal, take ip2's form (supposedly the pattern to match)
        if self.check_zero(ip_and) != 1:
            # print("checking prefix length between two ips", ip1.bitarray_mask, ip2.bitarray_mask)
            if ip1.bitarray_mask <= ip2.bitarray_mask:
                is_subset = 1
            # else:
            #     self.is_superset = 1
        return is_subset

    # this function is a bit weird. the return value will always be 0, you need to swap the order of break and is_ip_subset_deny = 1
    def check_ip_subset_deny(self, ip1, ip2):
        is_ip_subset_deny = 0
        if len(ip1) != 0:
            for x in ip1:
                if self.check_ip_subset(x, ip2) == 1:
                    is_ip_subset_deny = 1
                    break

        return is_ip_subset_deny

    # match type could be eq, ge, le
    def filter(self, match_type, field, pattern, filter_type):
        # TODO
        print("Doing deep copy")
        next = copy.deepcopy(self)
        print("Done deep copy")
        if field == RouteAnnouncementFields.IP_PREFIX and filter_type == FilterType.GE:
            pattern.bitarray_mask_type = FilterType.GE
            self.logger.debug('Before filtering: IP Prefix - %s | IP Prefix bitarray - %s| Pattern - %s | '
                              'Pattern bitarray - %s | length of current prefix deny %s' %
                              (self.ip_prefix, self.ip_prefix.bitarray, pattern, pattern.bitarray,
                               len(self.ip_prefix_deny)))
            print('Before filtering: IP Prefix - %s | IP Prefix bitarray - %s| Pattern - %s | '
                                    'Pattern bitarray - %s | length of current prefix deny %s |'
                  '                     self.ip_prefix.bitarray_mask %s | self.ip_prefix.bitarray_mask_type %s  ' %
                              (self.ip_prefix, self.ip_prefix.bitarray, pattern, pattern.bitarray,
                               len(self.ip_prefix_deny), self.ip_prefix.bitarray_mask, self.ip_prefix.bitarray_mask_type))
            self.ip_hit = 0
            # initial announcement [Permit XXXX ge 0, Deny: [] ] [10.0.0.0 ge 8 ]

            if self.check_zero(self.ip_prefix.bitarray & pattern.bitarray) == 0:
                print('no zeros found between ip and pattern')
                if self.ip_prefix.bitarray_mask_type == FilterType.EQUAL:  # [10.0.0.0/8 equal deny] [ 10.0.10.0/24 ge]
                    if self.ip_prefix.bitarray_mask < pattern.bitarray_mask:
                        self.ip_hit = 0
                    if self.ip_prefix.bitarray_mask >= pattern.bitarray_mask:  # [ 10.0.0.0/24 equal ] [10.0.10.0/16 ge]
                        if match_type == RouteMapType.PERMIT:
                            self.ip_hit = 1
                            # No need to check deny list, assuming the deny list of an permit equal is non-existent
                        if match_type == RouteMapType.DENY:
                            # drop current announcement
                            self.ip_hit = 0
                            self.drop_next_announcement = 1
                if self.ip_prefix.bitarray_mask_type == FilterType.GE:
                    print('checked current ip prefix bitarray mask type is GE')
                    if self.ip_prefix.bitarray_mask < pattern.bitarray_mask:  # [10.0.0.0/8 ge deny subset or non-overlap][ 10.0.10.0/24 ge]
                        print('checked current ip prefix bitarray is smaller than pattern bitarray mask')
                        print('match type should be Permit %s' % match_type)
                        if match_type == RouteMapType.PERMIT:
                            print('checked current match type is Routemap Permit')
                            print('first symbolic ann should start being processed here!')
                            if (self.check_ip_subset_deny(self.ip_prefix_deny, pattern) == 0) or (len(self.ip_prefix_deny) == 0):
                                self.ip_hit = 1
                                self.ip_prefix = pattern
                                next.ip_prefix_deny.append(pattern)
                            else:
                                # pattern is a subset of the deny list
                                self.ip_hit = 0
                        if match_type == RouteMapType.DENY:
                            # pattern is not a subset of the deny list
                            if (self.check_ip_subset_deny(self.ip_prefix_deny, pattern) == 0) or (
                                    len(self.ip_prefix_deny) == 0):
                                self.ip_hit = 0
                                next.ip_prefix_deny.append(pattern)
                            else:
                                self.ip_hit = 0
                    if self.ip_prefix.bitarray_mask >= pattern.bitarray_mask:  # [ 10.0.10.0/24 ge ] [10.0.0.0/8 ge]
                        if match_type == RouteMapType.PERMIT:
                            self.ip_hit = 1
                            # no need to check deny list as it can't be a superset of the pattern
                            # covered all space in current announcement, no need to pass the next announcement
                            # set next to none
                            self.drop_next_announcement = 1
                        if match_type == RouteMapType.DENY:
                            self.ip_hit = 0
                            self.drop_next_announcement = 1

                # if self.ip_prefix.bitarray_mask == FilterType.LE:
                #     if self.ip_prefix.bitarray_mask < pattern.bitarray_mask: # [10.0.0.0/8 le ] [10.0.10.0/24 ge]
                #         self.ip_hit = 0
                # TODO handle ge & le at the same time
                #     if self.ip_prefix.bitarray_mask >= pattern.bitarray_mask: # [10.0.0.0/24 le] [10.10.0.0/16 ge]
                #         self.ip_prefix

        if filter_type == FilterType.EQUAL and field == RouteAnnouncementFields.IP_PREFIX:
            pattern.bitarray_mask_type = FilterType.EQUAL
            self.ip_hit = 0
            if self.check_zero(self.ip_prefix.bitarray & pattern.bitarray) == 0:
                if self.ip_prefix.bitarray_mask_type == FilterType.EQUAL:
                    if self.ip_prefix.bitarray_mask == pattern.bitarray_mask:
                        # pattern can't have any overlapping with deny list 10.0.0.0/8 equal deny 11.0.0.0/24 permit 10.0.0.0/8
                        if len(self.ip_prefix_deny) == 0 or self.check_zero_list(self.ip_prefix_deny, pattern) == 0:
                            if match_type == RouteMapType.PERMIT:
                                self.ip_hit = 1
                            if match_type == RouteMapType.DENY:
                                # shouldn't append this processed announcement to the output
                                self.ip_hit = 0
                            # Nothing else gets passed onto the next route map item
                            # set next announcement to null
                            self.drop_next_announcement = 1
                            # next.ip_prefix.bitarray = BitArray('int:%d=0' % (2*32, ))

                if self.ip_prefix.bitarray_mask_type == FilterType.GE: # [10.0.0.0/8 ge, deny 10.0.10.0/32 ls deny 10.0.10.0/16 ge
                                                                    #  deny 10.0.10.0/32 equal] permit 10.0.10.0/24 equal
                    if self.ip_prefix.bitarray_mask <= pattern.bitarray_mask :
                        if len(self.ip_prefix_deny) == 0 or self.check_zero_list(self.ip_prefix_deny, pattern) == 0:
                            if match_type == RouteMapType.PERMIT:
                                self.ip_hit = 1
                                self.ip_prefix = pattern
                                # self.ip_prefix.bitarray_mask = pattern.bitarray_mask
                                self.ip_prefix.bitarray_mask_type = pattern.bitarray_mask_type
                                next.ip_prefix_deny.append(pattern)
                            if match_type == RouteMapType.DENY:
                                self.ip_hit = 0  # don't append it to the processed announcement list
                                self.ip_prefix_deny.append(pattern)
                                next.ip_prefix_deny.append(pattern)
                    if self.ip_prefix.bitarray_mask > pattern.bitarray_mask:  # [10.0.0.0/24 ge, ] [10.0.10.0/8 equal]
                        self.ip_hit = 0

                if self.ip_prefix.bitarray_mask_type == FilterType.LE:
                    if self.ip_prefix.bitarray_mask <= pattern.bitarray_mask : # [10.0.0.0 ls 8] [10.0.10.0/24 equal]
                        self.ip_hit = 0
                    if self.ip_prefix.bitarray_mask >= pattern.bitarray_mask : # [10.0.0.0/24 ls] [10.10.0.0/16 equal]
                        if len(self.ip_prefix_deny) == 0 or self.check_zero_list(self.ip_prefix_deny, pattern) == 0:
                            if match_type == RouteMapType.PERMIT:
                                self.ip_prefix = pattern
                                self.ip_prefix.bitarray = pattern.bitarray_mask
                                self.ip_prefix.bitarray_mask_type = pattern.bitarray_mask_type
                                next.ip_prefix_deny.append(pattern)
                            if match_type == RouteMapType.DENY:
                                self.ip_hit = 0  # don't append to the processed announcement list
                                self.ip_prefix_deny.append(pattern)
                                next.ip_prefix_deny.append(pattern)

        elif field == RouteAnnouncementFields.NEXT_HOP:
            self.logger.debug('Before: Next hop - %s | Pattern - %s' % (self.next_hop, pattern))
            self.next_hop.bitarray &= pattern.bitarray
            print('after filtering next hop field', self.next_hop)
            self.logger.debug('After: Next hop - %s' % (self.next_hop,))
            pass
        elif field == RouteAnnouncementFields.AS_PATH:
            pass
        elif field == RouteAnnouncementFields.MED:
            pass
        elif field == RouteAnnouncementFields.LOCAL_PREF:
            pass
        elif field == RouteAnnouncementFields.COMMUNITIES:
            pass
        else:
            self.logger.error('Tried to set unknown field %s with value %s' % (field, pattern))

        return self, next


class SymbolicField(object):
    def __init__(self, field_type, length):
        # TODO efficiently detect if there is an impossible bit in the bitarray
        # TODO add support for all other fields
        # TODO add support for the most important operations (e.g., bitwise-and)

        # initialize BitArray to all 1s
        self.field_type = field_type
        self.original_length = length
        self.bitarray = BitArray('int:%d=-1' % (2*length, ))
        self.bitarray_mask = 0
        self.bitarray_mask_type = FilterType.GE

        self.logger = get_logger('SymbolicField', 'DEBUG')

        # we use twice the length as we want to represent every bit by 2 bits to additionally allow
        # for wildcard and impossible bits
        # Z -> 00 > impossible bit
        # 0 -> 01 > 0 bit
        # 1 -> 10 > 1 bit
        # * -> 11 > wildcard bit

    def __len__(self):
        return len(self.bitarray)

    def __str__(self):
        if self.field_type == RouteAnnouncementFields.IP_PREFIX:  # convert HSA bit array to human-readable ip-prefix
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
                    prefix_len = i
                    ip_prefix += '0' * (32 - prefix_len)
                    break
            # TODO map 11 to wildcard character x?
            prefix = '%s/%d' % ('.'.join(['%d' % int('0b%s' % ip_prefix[j * 8:(j + 1) * 8], 2) for j in range(0, 4)]), prefix_len)
            return prefix
        elif self.field_type == RouteAnnouncementFields.NEXT_HOP:
            fnexthop = self.bitarray
            next_hop = ''
            next_hop_len = 32
            for i in range(0, 32):
                # Z -> 00
                if not fnexthop[2 * i] and not fnexthop[2 * i + 1]:
                    print('ERROR: invalid bit found')
                # 0 -> 01
                elif not fnexthop[2 * i] and fnexthop[2 * i + 1]:
                    next_hop += '0'
                # 1 -> 10
                elif fnexthop[2 * i] and not fnexthop[2 * i + 1]:
                    next_hop += '1'
                else:
                    next_hop_len = i
                    next_hop += '0' * (32 - next_hop_len)
                    break

            nexthop = '%s/%d' % ('.'.join(['%d' % int('0b%s' % next_hop[j * 8:(j + 1) * 8], 2) for j in range(0, 4)]), next_hop_len)
            return nexthop
        else:
            return str(self.bitarray)

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

        symbolic_field.bitarray_mask = ip_prefix.prefixlen
        logger.debug('symbolic_field.bitarray is %s and bitarray_mask length is %s' % (symbolic_field.bitarray,
                                                                                       symbolic_field.bitarray_mask))
        return symbolic_field



