#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from enum import Enum
from netaddr import IPNetwork
from bitstring import BitArray

from utils.logger import get_logger


class RouteAnnouncementFields(Enum):
    IP_PREFIX = 1
    NEXT_HOP = 2
    AS_PATH = 3
    MED = 4
    LOCAL_PREF = 5
    COMMUNITIES = 6


class RouteAnnouncement(object):
    """
    A BGP Route Announcement whose fields can be anywhere from fully symbolic to fully specified
    """

    def __init__(self, ip_prefix=None, next_hop=None, as_path=None, med=None, local_pref=None, communities=None, debug=False):
        # TODO model all other fields
        if ip_prefix:
            self.ip_prefix = SymbolicField.create_from_prefix(ip_prefix,0)
        else:
            self.ip_prefix = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)

        if next_hop:
            self.next_hop = SymbolicField.create_from_prefix(next_hop,1)
        else:
            self.next_hop = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)

        self.as_path = as_path
        self.med = med
        self.local_pref = local_pref
        self.communities = communities

        self.logger = get_logger('RouteAnnouncement', debug)

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
        #self.next_hop.bitarray &= pattern.bitarray
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
        return 'IP Prefix: %s' % (self.ip_prefix, )

    def __repr__(self):
        return self.__str__()

    def filter(self, field, pattern):
        # TODO
        if field == RouteAnnouncementFields.IP_PREFIX:
            self.logger.debug('Before: IP Prefix - %s | Pattern - %s' % (self.ip_prefix, pattern))
            self.ip_prefix.bitarray &= pattern.bitarray
            self.logger.debug('After: IP Prefix - %s' % (self.ip_prefix, ))
        elif field == RouteAnnouncementFields.NEXT_HOP:
            self.logger.debug('Before: Next hop - %s | Pattern - %s' % (self.next_hop, pattern))
            self.next_hop.bitarray &= pattern.bitarray
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


class SymbolicField(object):
    def __init__(self, field_type, length):
        # TODO efficiently detect if there is an impossible bit in the bitarray
        # TODO add support for all other fields
        # TODO add support for the most important operations (e.g., bitwise-and)

        # initialize BitArray to all 1s
        self.field_type = field_type
        self.original_length = length
        self.bitarray = BitArray('int:%d=-1' % (2*length, ))

        # we use twice the length as we want to represent every bit by 2 bits to additionally allow
        # for wildcard and impossible bits
        # Z -> 00 > impossible bit
        # 0 -> 01 > 0 bit
        # 1 -> 10 > 1 bit
        # * -> 11 > wildcard bit

    def __len__(self):
        return len(self.bitarray)

    def __str__(self):
        if self.field_type == RouteAnnouncementFields.IP_PREFIX:
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

        # take binary representation of prefix without the leading '0b'
        bin_ip_prefix = ip_prefix.ip.bin[2:]
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

        # convert an ip to a bit-array
        if type == 0:
            symbolic_field = SymbolicField(RouteAnnouncementFields.IP_PREFIX, 32)
        # symbolic bit array is 1111111 wild cards AND with specified ip-converted bit array
        else:
            symbolic_field = SymbolicField(RouteAnnouncementFields.NEXT_HOP, 32)
        symbolic_field.bitarray &= BitArray(formatted_ip_prefix_bin)

        return symbolic_field



