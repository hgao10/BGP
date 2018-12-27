#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)


from ciscoconfparse import CiscoConfParse
from collections import defaultdict

parse = CiscoConfParse(config="../configs/comm-net/Wint.conf")

### PARSE BGP NEIGHBORS
bgp_configs = parse.find_objects("^router\sbgp\s\d+$", exactmatch=True)

for bgp_config in bgp_configs:
    asn = int(bgp_config.re_match("^router\sbgp\s(\d+)$", group=1))

    neighbors = defaultdict(dict)
    for child in bgp_config.children:
        if child.re_match("(router-id)"):
            router_id = child.re_match("router-id\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", group=1)
        if child.re_match("^\s*(neighbor)"):
            neighbor_ip = child.re_match("^\s*neighbor\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s", group=1)
            neighbor = neighbors[neighbor_ip]

            if child.re_match("(remote-as)"):
                neighbor["ASN"] = int(child.re_match("remote-as\s(\d+)"))
                neighbor["TYPE"] = "iBGP" if neighbor["ASN"] == asn else "eBGP"

            elif child.re_match("(update-source)"):
                neighbor["UPDATE-SOURCE"] = child.re_match("update-source\s(.+)", group=1)

            elif child.re_match("(next-hop-self)"):
                neighbor["NEXT-HOP-SELF"] = True

            elif child.re_match("(route-map)"):
                route_map_name = child.re_match("route-map\s(\w+)\s(in|out)$", group=1)
                route_map_type = "OUT" if child.re_match("(out)$") else "IN"

                neighbor["RM-%s" % route_map_type] = route_map_name

            else:
                print("UNKNOWN: %s" % (child.text))

    output = ""
    for neighbor_ip, neighbor in neighbors.items():
        output += "NEIGHBOR: %s\n" % neighbor_ip
        for key, value in neighbor.items():
            output += "\t%s: %s\n" % (key, value)
        output += "\n"


    # print("BGP ASN: %d - ROUTER ID: %s" % (asn, router_id))
    # print(output)

### PARSE ROUTE MAPS
rm_configs = parse.find_objects("^route-map\s(\w+)\s(permit|deny)\s(\d+)$", exactmatch=True)

route_maps = defaultdict()

for rm_config in rm_configs:
    rm_name = rm_config.re_match("^route-map\s(\w+)\s(permit|deny)\s(\d+)$", group=1)
    rm_type = rm_config.re_match("^route-map\s(\w+)\s(permit|deny)\s(\d+)$", group=2)
    rm_seq_number = int(rm_config.re_match("^route-map\s(\w+)\s(permit|deny)\s(\d+)$", group=3))

    print("ROUTE-MAP: %s - %s - %d" % (rm_name, rm_type, rm_seq_number))

    for child in rm_config.children:
        if child.re_match("^\s*(match)"):
            match_type = child.re_match("^\s*match\s(community|ip\saddress\sprefix-list)", group=1)
            print("MATCH - %s" % match_type)
        elif child.re_match("^\s*(set)"):
            action_type = child.re_match("^\s*set\s(community|local-preference|med)", group=1)
            print("ACTION - %s" % action_type)

        else:
            print("UNKNOWN: Route-Map - %s" % child.text)
