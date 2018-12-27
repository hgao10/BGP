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

    rm_regex = "^route-map\s(\w+)\s(permit|deny)\s(\d+)$"

    rm_name = rm_config.re_match(rm_regex, group=1)
    rm_type = rm_config.re_match(rm_regex, group=2)
    rm_seq_number = int(rm_config.re_match(rm_regex, group=3))

    print("ROUTE-MAP: %s - %s - %d" % (rm_name, rm_type, rm_seq_number))

    for child in rm_config.children:
        if child.re_match("^\s*(match)"):
            match_type = child.re_match("^\s*match\s(community|ip\saddress\sprefix-list|local-preference)", group=1)
            print("MATCH - %s" % match_type)
        elif child.re_match("^\s*(set)"):
            action_type = child.re_match("^\s*set\s(community|local-preference|med)", group=1)
            print("ACTION - %s" % action_type)

        else:
            print("UNKNOWN: Route-Map - %s" % child.text)


### COMMUNITY-LISTS
cl_configs = parse.find_objects("^ip\scommunity-list", exactmatch=False)

community_lists = defaultdict(list)
for cl_config in cl_configs:
    print(cl_config)

    cl_regex = "^ip\scommunity-list\s(standard\s)?(\w+)\s(deny|permit)\s(.*)$"

    cl_name = cl_config.re_match(cl_regex, group=2)
    cl_type = cl_config.re_match(cl_regex, group=3)
    cl_list = cl_config.re_match(cl_regex, group=4)

    community_lists[cl_name].append((cl_type, cl_list))

### PREFIX-LISTS
pl_configs = parse.find_objects("^ip\sprefix-list", exactmatch=False)

prefix_lists = defaultdict(dict)
for pl_config in pl_configs:
    print(pl_config)

    pl_regex = "^ip\sprefix-list\s(\w+)\sseq\s(\d{1,5})\s(deny|permit)\s(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})$"

    pl_name = pl_config.re_match(pl_regex, group=1)
    pl_seq = int(pl_config.re_match(pl_regex, group=2))
    pl_type = pl_config.re_match(pl_regex, group=3)
    pl_prefix = pl_config.re_match(pl_regex, group=4)

    prefix_lists[pl_name][pl_seq] = (pl_type, pl_prefix)

for name, prefix_list in prefix_lists.items():
    for seq, data in prefix_list.items():
        print("PFX LIST: %s - %d - %s - %s" % (name, seq, data[0], data[1]))