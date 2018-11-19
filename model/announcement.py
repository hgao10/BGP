#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from enum import Enum
from netaddr import IPNetwork
from bitstring import BitArray

from utils.logger import get_logger

import copy


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
            self.ip_hit = 0
            self.ip_deny_display = []
        else:
            self.ip_prefix = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
            self.ip_prefix_deny = []
            self.ip_hit = 0
            self.ip_deny_display = []
            print('fully symbolicfield for ip_prefix', self.ip_prefix)

        if next_hop:
            self.next_hop = SymbolicField.create_from_prefix(next_hop, RouteAnnouncementFields.NEXT_HOP)
        else:
            self.next_hop = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
            print('fully symbolicfield for next_hop', self.next_hop)

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
            self.logger.error('Tried to set unknown field "%sæ with value "%s"' % (field, value))

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
            if self.check_zero(x.bitarray & ip_prefix.bitarray) != 0:
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

    def check_ip_subset_deny(self, ip1, ip2):
        is_ip_subset_deny = 0
        if len(ip1) != 0:
            for x in ip1:
                if self.check_ip_subset(x, ip2) == 1:
                    break
                    is_ip_subset_deny = 1
        return is_ip_subset_deny

    # match type could be eq, ge, le
    def filter(self, field, pattern, match_type):
        # TODO
        print("Doing deep copy")
        next = copy.deepcopy(self)
        print("Done deep copy")
        if match_type == FilterType.GE:
            if field == RouteAnnouncementFields.IP_PREFIX:
                self.logger.debug('Before filtering: IP Prefix - %s | IP Prefix bitarray - %s| Pattern - %s | '
                                  'Pattern bitarray - %s | length of current prefix deny %s' %
                                  (self.ip_prefix, self.ip_prefix.bitarray, pattern, pattern.bitarray,
                                   len(self.ip_prefix_deny)))
                print('Before filtering: IP Prefix - %s | IP Prefix bitarray - %s| Pattern - %s | '
                                        'Pattern bitarray - %s | length of current prefix deny %s' %
                                  (self.ip_prefix, self.ip_prefix.bitarray, pattern, pattern.bitarray,
                                   len(self.ip_prefix_deny)))
                # print("Doing deep copy")
                # next = copy.deepcopy(self)
                # print("Done deep copy")

                if self.check_zero(self.ip_prefix.bitarray & pattern.bitarray) == 0:
                    self.logger.debug('No impossible bits, now checking subset')
                    print('No impossible bits, now checking subset')
                    if self.check_ip_subset(self.ip_prefix, pattern)== 1:
                        self.logger.debug('Pattern is a subset, now check length of the deny list %s' % (len(self.ip_prefix_deny)))
                        print('Pattern is a subset, now check length of the deny list %s' % (len(self.ip_prefix_deny)))
                        if len(self.ip_prefix_deny) != 0:
                            self.logger.debug('Checking if pattern is a subset of any of the deny list %s' %
                                              self.ip_prefix_deny[0])
                            print('Checking if pattern is a subset of any of the deny list %s' % self.ip_prefix_deny[0])

                            if self.check_ip_subset_deny(self.ip_prefix_deny, pattern) == 0:
                                self.logger.debug('the pattern is not a subset of the deny list')
                                print('the pattern is not a subset of the deny list')
                                next.ip_prefix_deny.append(pattern)
                                self.logger.debug('adding current pattern to the next deny list %s' % pattern)
                                print('adding current pattern to the next deny list %s' % pattern)
                                next.ip_prefix = self.ip_prefix
                                self.ip_prefix = pattern
                                self.ip_hit = 1
                            else:
                                self.ip_hit = 0
                                return self, next

                        else:
                            self.ip_hit = 1
                            if len(self.ip_prefix_deny) == 0:
                                self.logger.debug('current ip deny list is 0')
                                print('current ip deny list is 0')
                            else:
                                for x in self.ip_prefix_deny:
                                    self.logger.debug('Before add to next deny list, current ip deny list is %s \n' % x)
                            next.ip_prefix_deny.append(pattern)
                            # next.ip_prefix = self.ip_prefix
                            print('No change to next.ip_prefix %s, equal to self.ip_prefix %s' % (next.ip_prefix, self.ip_prefix))
                            self.ip_prefix = pattern
                            self.logger.debug('After Filtering: Next ip prefix - %s | current ip_prefix is now %s| '
                                              'next ip_prefix_deny %s| '
                                              'length of current ip deny list %s'
                                              % (next.ip_prefix, self.ip_prefix, next.ip_prefix_deny[0],
                                                 len(self.ip_prefix_deny)))
                            print('After Filtering: Next ip prefix - %s | current ip_prefix is now %s| '
                                              'next ip_prefix_deny %s| '
                                              'length of current ip deny list %s'
                                              % (next.ip_prefix, self.ip_prefix, next.ip_prefix_deny[0],
                                                 len(self.ip_prefix_deny)))

                            if len(self.ip_prefix_deny) == 0:
                                self.logger.debug('current ip deny list is 0')
                                print('current ip deny list is 0')
                            else:
                                for x in self.ip_prefix_deny:
                                    self.logger.debug('after add to next deny list, current ip deny list is %s \n' % x)
                                    print('after add to next deny list, current ip deny list is %s \n' % x)
                else:
                    self.ip_hit = 0
                    self.logger.debug('pattern does not match current ip prefix, thus next announcement is the same as '
                                      'current announcement, current deny list length %s | '
                                      'length of next.ip_prefix_deny - %s|next.ip_prefix - %s |'
                                      % (len(self.ip_prefix_deny), len(next.ip_prefix_deny), next.ip_prefix))

        if match_type == FilterType.EQUAL:
            self.ip_hit = 0
            if (self.ip_prefix.bitarray_mask == 0) & (len(self.ip_prefix_deny) == 0):
                self.ip_hit = 1
                self.ip_prefix = pattern
                next.ip_prefix_deny.append(pattern)
            elif self.check_zero(self.ip_prefix.bitarray & pattern.bitarray) != 0:
                if self.ip_prefix.bitarray_mask == pattern.bitarray_mask:
                    if len(self.ip_prefix_deny)==0 | self.check_zero_list(self.ip_prefix_deny, pattern) == 0:
                        self.ip_hit = 1
                        # set next announcement to null
                        next.ip_prefix.bitarray = '00' * 32

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



