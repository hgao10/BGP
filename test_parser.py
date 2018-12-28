#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

from utils.config_parser import load_network_from_configs

config_path = "configs/comm-net/"

load_network_from_configs(config_path, scenario_name="HalloTest")