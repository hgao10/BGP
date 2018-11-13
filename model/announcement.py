#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from enum import Enum
from netaddr import IPNetwork
from bitstring import BitArray

from utils.logger import get_logger
import logging

import copy

logger2 = logging.getLogger('hhhh')
logger2.setLevel(logging.INFO)


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


class SubSet:
    def __init__(self):
        self.is_subset = 0
        self.is_superset = 0
        self.zero = 0
        self.is_ip_subset_deny = 0
    # check if a ip prefix bit array has any impossible bit in it

    def check_zero(self, ip_prefix):
        print("checking for zero bits in this ip", ip_prefix)
        self.zero = 0
        for i in range(0, 32):
            if not ip_prefix[2 * i] and not ip_prefix[2 * i + 1]:
                self.zero = 1
                break
            else:
                continue
        return self.zero

    # check if ip2 is ip1's subset or superset by comparing ip prefix and length of each mask
    def check_ip_subset(self, ip1, ip2):
        self.is_subset = 0
        self.is_superset = 0
        ip_and = ip1.bitarray & ip2.bitarray
        # if the lengths are equal, take ip2's form (supposedly the pattern to match)
        if self.check_zero(ip_and) != 1:
            print("checking prefix length between two ips", ip1.bitarray_mask, ip2.bitarray_mask)
            if ip1.bitarray_mask >= ip2.bitarray_mask:
                self.is_subset = 1
            else:
                self.is_superset = 1
        return self

    def check_ip_subset_deny(self, ip1, ip2):
        self.is_ip_subset_deny = 0
        if len(ip1) != 0:
            for x in ip1:
                if self.check_ip_subset(x, ip2).is_subset == 1:
                    break
                    self.is_ip_subset_deny = 1
        return self


class RouteAnnouncement(object):
    """
    A BGP Route Announcement whose fields can be anywhere from fully symbolic to fully specified
    """

    def __init__(self, ip_prefix=None, next_hop=None, as_path=None, med=None, local_pref=None, communities=None, debug=True):
        # TODO model all other fields
        if ip_prefix:
            self.ip_prefix = SymbolicField.create_from_prefix(ip_prefix,RouteAnnouncementFields.IP_PREFIX)
            self.ip_prefix_next = SymbolicField.create_from_prefix(ip_prefix, RouteAnnouncementFields.IP_PREFIX)
            self.ip_prefix_deny = []
            self.ip_prefix_deny_next = []
        else:
            self.ip_prefix = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            self.ip_prefix_next = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            self.ip_prefix_deny = []
            self.ip_prefix_deny_next = []
            print('fully symbolicfield for ip_prefix', self.ip_prefix)

        if next_hop:
            self.next_hop = SymbolicField.create_from_prefix(next_hop,RouteAnnouncementFields.NEXT_HOP)
        else:
            self.next_hop = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
            print('fully symbolicfield for next_hop', self.next_hop)

        self.as_path = as_path
        self.med = med
        self.local_pref = local_pref
        self.communities = communities
        self.next = copy.deepcopy(self)
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
            self.logger.error('Tried to set unknown field "%sæ with value "%s"' % (field, value))

    def set_ip_prefix(self, ip_prefix):
        # TODO
        pass

    def set_next_hop(self, next_hop):
        # TODO
        # self.next_hop.bitarray &= pattern.bitarray
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
        return 'IP Prefix: %s, Next Hope: %s' % (self.ip_prefix, self.next_hop)

    def __repr__(self):
        return self.__str__()

    def set_action(self, instance, value):
        pass

    # match type could be eq, ge, le
    def filter(self, field, pattern, match_type):
        # TODO
        self.logger = get_logger('RouteAnnouncement', 'DEBUG')
        if match_type == FilterType.EQUAL:
            if field == RouteAnnouncementFields.IP_PREFIX:
                self.logger.debug('Before: IP Prefix - %s | Pattern - %s' % (self.ip_prefix, pattern))
                subset = SubSet()
                # subset = self.check_subset(self.ip_prefix.bitarray, pattern.bitarray, match_type)
                print("ip_prefix bitarray should be all 1s", self.ip_prefix.bitarray)
                print("pattern.bitarray:", pattern.bitarray)
                if subset.check_zero(self.ip_prefix.bitarray & pattern.bitarray) == 0:
                    print("subset check zero has passed, now checking subset")
                    if subset.check_ip_subset(self.ip_prefix, pattern).is_subset == 1:
                        print("checked that pattern.bitarray is a subset of the original ip and current length of prefix_deny list is", len(self.ip_prefix_deny))
                        if len(self.ip_prefix_deny) != 0:
                            print("length of the ip prefix deny list",len(self.ip_prefix_deny), self.ip_prefix_deny[0], str(pattern) )
                            if subset.check_ip_subset_deny(self.ip_prefix_deny, pattern).is_ip_subset_deny == 0:
                                # if it's a superset or non-overlapping
                                # if last_item != 0 : # even if its the last item in the list
                                    # self.ip_prefix_deny_next.append(pattern.bitarray)
                                self.next.ip_prefix_deny.append(pattern)
                                # self.ip_prefix_next = self.ip_prefix
                                self.next.ip_prefix = self.ip_prefix
                                self.ip_prefix = pattern
                        else:
                            self.next.ip_prefix_deny.append(pattern)
                            # self.ip_prefix_next = self.ip_prefix
                            self.next.ip_prefix = self.ip_prefix
                            self.ip_prefix = pattern
                            print("self.next ip prefix, ip_prefix_deny, new processed ip is", self.next.ip_prefix, self.next.ip_prefix_deny[0], self.ip_prefix)

                    # else:
                        # it is a subset, and next is equal to current
                    # if it's a superset or non-overlapping
                          # self.anndeny.ip_prefix = 0; no changes to the deny list
                # else: # current ip is an subset of the pattern, eg: 10.0.10.0/24, then match 10.0.0.0/8
                    # no changes to current announcement
            # else:
                # no matches have been found, move to the next match, do nothing

            # self.ip_prefix.bitarray &= pattern.bitarray


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
            self.logger.error('Tried to set unknown field "%sæ with value "%s"' % (field, pattern))

        print('after filtering ip prefix field', self.ip_prefix)
        self.logger.debug('After: IP Prefix - %s' % (self.ip_prefix,))
        print("self.next.ip_prefix is and self.next.ip_prefix_list is at the end of filter call", self.next.ip_prefix, self.next.ip_prefix_deny[0])
        return self, self.next

class SymbolicField(object):
    def __init__(self, field_type, length):
        # TODO efficiently detect if there is an impossible bit in the bitarray
        # TODO add support for all other fields
        # TODO add support for the most important operations (e.g., bitwise-and)

        # initialize BitArray to all 1s
        self.field_type = field_type
        self.original_length = length
        self.bitarray = BitArray('int:%d=-1' % (2*length, ))
        self.bitarray_mask = self.original_length



        print('Creating a symbolicfield, bitarray is initialized as', self.bitarray)

        # we use twice the length as we want to represent every bit by 2 bits to additionally allow
        # for wildcard and impossible bits
        # Z -> 00 > impossible bit
        # 0 -> 01 > 0 bit
        # 1 -> 10 > 1 bit
        # * -> 11 > wildcard bit

    def __len__(self):
        return len(self.bitarray)

    def __str__(self):
        if self.field_type == RouteAnnouncementFields.IP_PREFIX: # convert HSA bitarray to human-readable ip-prefix
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
        ip_prefix = IPNetwork(str_ip_prefix)
        print(ip_prefix)

        # take binary representation of prefix without the leading '0b'
        bin_ip_prefix = ip_prefix.ip.bin[2:]
        print(bin_ip_prefix)
        if len(bin_ip_prefix) < 32:
            bin_ip_prefix = '0' * (32-len(bin_ip_prefix)) + bin_ip_prefix

        # create a new bitstring by translating bits to the four bit representation
        formatted_ip_prefix_bin = '0b'
        for i in range(0, ip_prefix.prefixlen):
            if bin_ip_prefix[i] == '1':
                formatted_ip_prefix_bin += '10'
            else:
                formatted_ip_prefix_bin += '01'
            # TODO Need to handle wildcard conversion for le, ge match????

        # fill the end with wildcard bits
        formatted_ip_prefix_bin += '11' * (32 - ip_prefix.prefixlen)
        print('HSA rep:', formatted_ip_prefix_bin)
        # convert an ip to a bit-array
        if type == RouteAnnouncementFields.IP_PREFIX:
            symbolic_field = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            # symbolic bit array is 1111111 wild cards AND with specified ip-converted bit array
            print('creating symbolic field from ip prefix', symbolic_field.bitarray)
        elif type == RouteAnnouncementFields.NEXT_HOP:
            symbolic_field = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
            print('creating symbolic field from next hop', symbolic_field.bitarray)

        symbolic_field.bitarray &= BitArray(formatted_ip_prefix_bin)
        symbolic_field.bitarray_mask = ip_prefix.prefixlen
        print("returning symbolic bitarray", symbolic_field.bitarray)
        return symbolic_field



