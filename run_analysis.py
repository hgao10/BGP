#!/usr/bin/env python
# Author: Ruediger Birkner (Networked Systems Group at ETH Zurich)

import argparse
import cmd

from model.test_networks import get_simple_network


class TestSuite(cmd.Cmd):

    def __init__(self, *args, **kw):
        cmd.Cmd.__init__(self, *args, **kw)

        # current network
        self.network = None

        self.prompt = '> '
        # self.intro = 'Hi, '

        self.cmdloop()

    def do_exit(self):
        """exit: Leave the CLI"""
        return True

    def do_load(self, line=''):
        """load: Load one of the provided network models or create a new one from configurations"""
        line = line.lower()

        if line == 'simple':
            self.network = get_simple_network()
        else:
            print('The supplied topology is not known: %s. Try "simple" for example.' % line)

    def do_run(self):
        """run: Run an analysis on the loaded network model by propagating a symbolic announcement"""
        if self.network:
            neighbor = 'in_neighbor'

            outcome = self.network.propagate_announcement(neighbor)

            output = 'From %s the following announcements make it through to the other neighbors:\n\n' % (neighbor, )
            for neighbor, announcement in outcome.items():
                output += '\t%s: %s\n' % (neighbor, announcement)
            print(output)
        else:
            print('You need to load a network model before you can run the symbolic execution.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', help='enable debug output', action='store_true')
    args = parser.parse_args()

    debug = args.debug

    TestSuite()
