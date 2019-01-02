#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


import sys
import os

from collections import defaultdict

from ciscoconfparse import CiscoConfParse

from model.announcement import RouteMapType, RouteAnnouncementFields, SymbolicField, FilterType
from model.router import RouteMap, RouteMapItems, RouteMapDirection

from model.network import NetworkTopology
from utils.logger import get_logger


logger = get_logger('ConfigParser', 'INFO')


def load_network_from_configs(config_path, scenario_name=""):
    """
    Creates a NetworkTopology by parsing all the supplied config files (configs) which are located in the config path.
    """

    if not scenario_name:
        scenario_name = os.path.basename(config_path)

    # get all config files
    all_files = os.listdir(config_path)

    configs = list()
    for file_name in all_files:
        router, filetype = file_name.split('.')
        if filetype == 'cfg' or filetype == 'conf':
            configs.append(file_name)

    logger.debug("Starting to parse %d configurations as part of the %s scenario." % (len(configs), scenario_name))

    parsed_configs = dict()

    routers = dict()
    route_maps = dict()
    peerings = dict()
    communities = set()  # set of all communities that somehow appear in the configs

    network = NetworkTopology(scenario_name)

    for config in configs:
        router_name = config.split(".")[0]
        config_file_path = os.path.join(config_path, config)
        parsed_configs[config] = CiscoConfParse(config=config_file_path)

        # add the internal router
        router_id, asn = get_router_info(parsed_configs[config])
        routers[router_name] = network.add_internal_router(router_name, router_id, asn)

        logger.debug("Parsing the config of %s with id %s and ASN %d." % (router_name, router_id, asn))

        # add all prefix-lists
        prefix_lists = create_prefix_lists(parsed_configs[config])

        # add all community-lists
        community_lists, tmp_communities = create_community_lists(parsed_configs[config])

        # update the communities
        communities |= tmp_communities

        # add all access-lists
        access_lists = create_access_lists(parsed_configs[config])

        # add all access-lists
        as_path_lists = create_as_path_lists(parsed_configs[config])

        # add all route-maps
        route_maps[router_name], tmp_communities = create_route_maps(
            parsed_configs[config], prefix_lists, community_lists, access_lists, as_path_lists
        )

        # update the communities
        communities |= tmp_communities

        # get BGP peerings
        local_peerings, external_routers = get_bgp_peerings(parsed_configs[config])

        # store peerings for later
        peerings[router_name] = local_peerings

        # add external routers
        for i, external_router in enumerate(external_routers):
            neighbor_ip, neighbor_asn = external_router
            network.add_external_router('ext_router_%d' % i, neighbor_ip, neighbor_asn)

        # output for debugging
        logger.debug(
            local_debug_output(
                router_name,
                prefix_lists,
                community_lists,
                access_lists,
                as_path_lists,
                route_maps[router_name],
                local_peerings,
                external_routers,
            )
        )


    # add all peerings (and route-maps) to the network
    for router_name, local_peerings in peerings.items():
        for neighbor, sessions in local_peerings.items():
            network.add_peering(router_name, neighbor)

            # add route-maps
            for direction in [RouteMapDirection.IN, RouteMapDirection.OUT]:
                if sessions[direction]:
                    rm_name = sessions[direction]

                    routers[router_name].add_route_map(
                        route_maps[router_name][rm_name],
                        direction,
                        neighbor
                    )

    # add a list of all the communities to the network model
    communities = list(communities)
    communities.sort()
    logger.debug("Community List: %s" % ", ".join(communities))
    network.add_community_list(communities)

    return network


def get_router_info(parsed_config):
    bgp_configs = parsed_config.find_objects("^router\sbgp\s\d+$", exactmatch=True)
    if bgp_configs:
        asn = int(bgp_configs[0].re_match("^router\sbgp\s(\d+)$", group=1))
    else:
        asn = -1

    ri_configs = parsed_config.find_objects_w_parents(
        "^router\sbgp\s\d+$",
        "^\sbgp\srouter-id\s")
    if ri_configs:
        router_id = ri_configs[0].re_match("^\sbgp\srouter-id\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", group=1)
    else:
        router_id = "UNKNOWN"

    return router_id, asn


def create_prefix_lists(parsed_config):
    prefix_lists = defaultdict(dict)

    pl_regex = "^ip\sprefix-list\s(\w+)\sseq\s(\d{1,5})\s(deny|permit)\s" \
               "(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})(?:\sle\s(\d+))?(?:\sge\s(\d+))?$"

    pl_configs = parsed_config.find_objects("^ip\sprefix-list", exactmatch=False)
    for pl_config in pl_configs:

        pl_name = pl_config.re_match(pl_regex, group=1)
        pl_seq = int(pl_config.re_match(pl_regex, group=2))
        pl_type = pl_config.re_match(pl_regex, group=3)
        pl_prefix = pl_config.re_match(pl_regex, group=4)
        pl_le = pl_config.re_match(pl_regex, group=5)
        pl_ge = pl_config.re_match(pl_regex, group=6)

        if pl_le and pl_ge:
            # TODO implement
            logger.error("At the moment, we only support LE, GE, or EQUAL match, but nothing more specific.")

        prefix_lists[pl_name][pl_seq] = (pl_type, pl_prefix, pl_le, pl_ge)

    return prefix_lists


def create_community_lists(parsed_config):
    community_lists = defaultdict(list)
    communities = set()

    cl_regex = "^ip\scommunity-list\s(standard\s)?(\w+)\s(deny|permit)\s(.*)$"

    cl_configs = parsed_config.find_objects("^ip\scommunity-list", exactmatch=False)
    for cl_config in cl_configs:

        cl_name = cl_config.re_match(cl_regex, group=2)
        cl_type = get_match_type(cl_config.re_match(cl_regex, group=3))
        tmp_list = cl_config.re_match(cl_regex, group=4)
        cl_list = tmp_list.split()
        communities.update(cl_list)

        community_lists[cl_name].append((cl_type, cl_list))

    return community_lists, communities


def create_access_lists(parsed_config):
    access_lists = defaultdict(list)

    al_regex = "^access-list\s(\w+)\s(deny|permit)\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})$"

    al_configs = parsed_config.find_objects("^access-list\s", exactmatch=False)
    for al_config in al_configs:

        al_name = al_config.re_match(al_regex, group=1)
        al_type = get_match_type(al_config.re_match(al_regex, group=2))
        al_prefix = al_config.re_match(al_regex, group=3)

        access_lists[al_name].append((al_type, al_prefix))

    return access_lists


def create_as_path_lists(parsed_config):
    as_path_lists = defaultdict(list)

    apl_regex = "^ip\sas-path\saccess-list\s(\w+)\s(deny|permit)\s(.*)$"

    apl_configs = parsed_config.find_objects("^ip\sas-path\saccess-list\s", exactmatch=False)
    for apl_config in apl_configs:

        apl_name = apl_config.re_match(apl_regex, group=1)
        apl_type = get_match_type(apl_config.re_match(apl_regex, group=2))
        apl_pattern = apl_config.re_match(apl_regex, group=3)

        as_path_lists[apl_name].append((apl_type, apl_pattern))

    return as_path_lists


def create_route_maps(parsed_config, prefix_lists, community_lists, access_lists, as_path_lists):
    route_maps = dict()
    communities = set()

    rm_configs = parsed_config.find_objects("^route-map\s(\w+)\s(permit|deny)\s(\d+)$", exactmatch=True)
    for rm_config in rm_configs:

        rm_regex = "^route-map\s(\w+)\s(permit|deny)\s(\d+)$"

        rm_name = rm_config.re_match(rm_regex, group=1)
        rm_type = get_match_type(rm_config.re_match(rm_regex, group=2))

        if rm_name not in route_maps:
            route_maps[rm_name] = RouteMap(rm_name, rm_type)

        rm_items = RouteMapItems()
        for child in rm_config.children:
            if child.re_match("^\s*(match)"):
                match_type, field, pattern, filter_type = parse_match(
                    child, prefix_lists, community_lists, access_lists, as_path_lists
                )
                rm_items.add_match(match_type, field, pattern, filter_type)

            elif child.re_match("^\s*(set)"):
                field, pattern, tmp_communities = parse_action(child)
                communities.union(tmp_communities)

                rm_items.add_action(field, pattern)

            else:
                logger.error("UNKNOWN ROUTE-MAP LINE: %s" % child.text)

        rm_seq_number = int(rm_config.re_match(rm_regex, group=3))
        route_maps[rm_name].add_item(rm_items, rm_seq_number)

    return route_maps, communities


def parse_match(config_line, prefix_lists, community_lists, access_lists, as_path_lists):
    str_field = config_line.re_match(
        "^\s*match\s(community|ip\saddress\sprefix-list|local-preference|metric|as-path)", group=1
    )

    if str_field == "community":
        field = RouteAnnouncementFields.COMMUNITIES
        cl_name = config_line.re_match("^\s*match\scommunity\s(\w+)", group=1)

        cl = community_lists[cl_name]
        if len(cl) > 1:
            logger.error("At the moment, we only support community lists "
                         "that consists of a conjunction of communities, and not disjunction.")

        match_type, pattern = cl[0]
        filter_type = FilterType.GE

    elif str_field == "ip address prefix-list":
        field = RouteAnnouncementFields.IP_PREFIX
        pl_name = config_line.re_match("^\s*match\sip\saddress\sprefix-list\s(\w+)", group=1)

        pl = prefix_lists[pl_name]
        if len(pl) > 1:
            logger.error("At the moment, we only support prefix lists with a single prefix.")

        for match_type, pl_prefix, pl_le, pl_ge in pl.values():
            break

        pattern = SymbolicField.create_from_prefix(pl_prefix, field)

        # TODO add proper filter type parsing... add support for LE and GE at the same time
        if pl_le and not pl_ge:
            filter_type = FilterType.LE
        elif not pl_le and pl_ge:
            filter_type = FilterType.GE
        else:
            filter_type = FilterType.EQUAL

    elif str_field == "ip next-hop":
        field = RouteAnnouncementFields.NEXT_HOP
        al_name = config_line.re_match("^\s*match\sip\snext-hop\saccess-list\s(\w+)", group=1)

        al = access_lists[al_name]
        if len(al) > 1:
            logger.error("At the moment, we only support prefix lists with a single prefix.")
        match_type, al_prefix = al[0]

        # TODO is this really supposed to be IP_PREFIX???
        pattern = SymbolicField.create_from_prefix(al_prefix, RouteAnnouncementFields.IP_PREFIX)

        filter_type = FilterType.EQUAL

    elif str_field == "as-path":
        field = RouteAnnouncementFields.AS_PATH
        apl_name = config_line.re_match("^\s*match\sas-path\s(\w+)", group=1)

        apl = as_path_lists[apl_name]
        if len(apl) > 1:
            logger.error("At the moment, we only support as path lists with a pattern.")

        for match_type, pattern in apl:
            break

        filter_type = FilterType.EQUAL

    elif str_field == "metric":
        field = RouteAnnouncementFields.MED
        match_type = RouteMapType.PERMIT
        pattern = config_line.re_match("^\s*match\smetric\s(\d+)", group=1)
        filter_type = FilterType.EQUAL

    elif str_field == "local-preference":
        field = RouteAnnouncementFields.LOCAL_PREF
        match_type = RouteMapType.PERMIT
        pattern = config_line.re_match("^\s*match\slocal-preference\s(\d+)", group=1)
        filter_type = FilterType.EQUAL

    else:
        logger.error("UNKNOWN MATCH: %s" % config_line.text)
        sys.exit(0)

    return match_type, field, pattern, filter_type


def parse_action(config_line):
    communities = set()

    str_field = config_line.re_match(
        "^\s*set\s(community|ip\snext-hop|local-preference|as-path\sprepend|metric)",
        group=1
    )

    if str_field == "community":
        field = RouteAnnouncementFields.COMMUNITIES
        str_pattern = config_line.re_match("^\s*set\scommunity\s(.+)$", group=1)
        pattern = str_pattern.split()
        communities = set(pattern)

    elif str_field == "ip next-hop":
        field = RouteAnnouncementFields.NEXT_HOP
        pattern = config_line.re_match("^\s*set\sip\snext-hop\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", group=1)

    elif str_field == "local-preference":
        field = RouteAnnouncementFields.LOCAL_PREF
        pattern = int(config_line.re_match("^\s*set\slocal-preference\s(\d+)$", group=1))

    elif str_field == "as-path prepend":
        field = RouteAnnouncementFields.AS_PATH
        pattern = [
            int(asn) for asn in config_line.re_match("^\s*set\sas-path\sprepend\s((?:\d+\s?)+)$", group=1).split()
        ]

    elif str_field == "metric":
        field = RouteAnnouncementFields.MED
        pattern = int(config_line.re_match("^\s*set\smetric\s(\d+)$", group=1))

    else:
        logger.error("UNKNOWN ACTION: %s" % config_line.text)
        sys.exit(0)

    return field, pattern, communities


def get_bgp_peerings(parsed_config):
    peerings = dict()
    external_routers = list()

    # TODO at the moment, we assume that there is a single BGP process per router
    bgp_configs = parsed_config.find_objects("^router\sbgp\s\d+$", exactmatch=True)
    bgp_config = bgp_configs[0]

    asn = int(bgp_config.re_match("^router\sbgp\s(\d+)$", group=1))

    for child in bgp_config.children:
        if child.re_match("^\s*(neighbor)"):
            neighbor_ip = child.re_match("^\s*neighbor\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s", group=1)

            # init the session
            if neighbor_ip not in peerings:
                peerings[neighbor_ip] = {
                    RouteMapDirection.IN: "",
                    RouteMapDirection.OUT: "",
                }

            if child.re_match("(route-map)"):
                rm_name = child.re_match("route-map\s(\w+)\s(in|out)$", group=1)
                rm_type = RouteMapDirection.OUT if child.re_match("(out)$") else RouteMapDirection.IN

                peerings[neighbor_ip][rm_type] = rm_name

            elif child.re_match("(remote-as)"):
                neighbor_asn = int(child.re_match("remote-as\s(\d+)"))

                if neighbor_asn != asn:
                    external_routers.append((neighbor_ip, neighbor_asn))

            elif child.re_match("(update-source)"):
                us_intf = child.re_match("update-source\s(.+)", group=1)
                logger.debug("Update-Source %s" % us_intf)

            elif child.re_match("(next-hop-self)"):
                logger.debug("Next-Hop-Self")

            else:
                logger.error("UNKNOWN: %s" % (child.text))

    return peerings, external_routers


def get_match_type(str_type):
    if str_type == "permit":
        return RouteMapType.PERMIT
    else:
        return RouteMapType.DENY


def local_debug_output(
        router,
        prefix_lists,
        community_lists,
        access_lists,
        as_path_lists,
        route_maps,
        local_peerings,
        external_routers):

    output = "Parsed information from %s\n" % router
    if prefix_lists:
        output += "PREFIX LISTS:\n"
        for pl_name, data1 in prefix_lists.items():
            for pl_seq, data2 in data1.items():
                pl_type, pl_prefix, pl_le, pl_ge = data2
                output += "\tName: %s, Seq: %d, Type: %s, Prefix: %s, LE: %s, GE: %s\n" % \
                          (pl_name, pl_seq, pl_type, pl_prefix, pl_le, pl_ge)

    if community_lists:
        output += "COMMUNITY LISTS:\n"
        for cl_name, community_list in community_lists.items():
            cl_list = ", ".join("%s-%s" % (cl_type, cl_list) for cl_type, cl_list in community_list)
            output += "\tName: %s -> %s\n" % (cl_name, cl_list)

    if access_lists:
        output += "ACCESS LISTS:\n"
        for al_name, al_lists in access_lists.items():
            al_list = ", ".join("%s-%s" % (al_type, al_prefix) for al_type, al_prefix in al_lists)
            output += "\tName: %s -> %s\n" % (al_name, al_list)

    if as_path_lists:
        output += "AS PATH LISTS:\n"
        for apl_name, apl_lists in as_path_lists.items():
            apl_list = ", ".join("%s-%s" % (apl_type, apl_pattern) for apl_type, apl_pattern in apl_lists)
            output += "\tName: %s -> %s\n" % (apl_name, apl_list)

    if route_maps:
        output += "ROUTE MAPS:\n"
        for rm_name, data1 in route_maps.items():
            output += "\tName: %s, RouteMap:\n%s\n" % (rm_name, data1)

    if local_peerings:
        output += "PEERINGS\n"
        for neighbor, sessions in local_peerings.items():
            tmp_sessions = list()
            for direction, route_map in sessions.items():
                if route_map:
                    tmp_sessions.append("%s: %s" % (str(direction).split(".")[1], route_map))
            rm_sessions = ", ".join(tmp_sessions)
            output += "\tNeighbor: %s - %s\n" % (neighbor, rm_sessions)

    if external_routers:
        output += "EXTERNAL ROUTERS\n"
        output += ", ".join(["%s (%s)" % (asn, ip) for ip, asn in external_routers])

    return output
