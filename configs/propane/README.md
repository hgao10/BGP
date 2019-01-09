# Propane Config

From [Don’t Mind the Gap: Bridging Network-wide Objectives and Device-level Configurations](https://ratul.org/papers/sigcomm2016-propane.pdf) Figure 1

## Setup

A network consisting of four routers (R1, R2, R4, R5) that are all
connected in a full-mesh. It has three neighbors Cust (ASN 100), Peer
(ASN 200), and Prov (ASN 300). Cust owns the prefix 100.0.0.0/8.

## Policies

* __P1: Prefer Cust > Peer > Prov__
  Every router sets the local-preference on all incoming announcements.
  For routes received from the customer, we use 150, for the peer, 125,
  and for the provider, we use 100.

* __P2: Disallow traffic between Prov and Peer__
  We set communities on all incoming routes that show from which
  neighbor the announcement comes from. We block the outgoing route-maps
  accordingly. For Prov, we use 21:100, for Peer 21:125 and for Cust
  21:150. At the peer, we block all outgoing announcements that have
  community 21:100 set.

* __P3: For Cust, prefer R1 > R2__
  We enforce this by setting a slightly higher local-preference on the
  announcements received by R1 (151 instead of 150). In addition, we
  set a lower MED (metric) to all routes going from R1 to Cust as to the
  routes going from R2 to Cust (metric of 50 vs. 100)

* __P4: Cust must be on path for its prefixes__
  To enforce this policy, we have a special on all incoming connections
  that match all announcements for the prefix of Cust (100.0.0.0/16) and
  and that do not have Cust's AS number (100) in the AS path.

* __P5: Cust must not be a transit to Prov__
  At both peerings with Cust, we have a filter that drops all incoming
  announcements that have Prov's AS number (300) on the path.

## Mistakes

* __P2: Disallow traffic between Prov and Peer__
  At R2, the operator made a typo and specified to match on the
  community `21:12` instead of `21:125`.

* __P4: Cust must be on path for its prefixes__
  At R5, the operator forgot the `ge 16` in the prefix-list. Therefore,
  it only drops the announcements that exactly for 100.0.0.0/16, and lets
  all announcements for more specific prefixes pass. This is a violation
  of the policy.
