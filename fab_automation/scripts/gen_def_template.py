# Copyright 2020-2022 Efabless Corporation
# Copyright 2022 Myrtle Shah <gatecat@ds0.me>
#
# Based on OpenLane io_place.py; extended for FABulous tile pin placement
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import sys
import math
import click
import random


def grid_to_tracks(origin, count, step):
    tracks = []
    pos = origin
    for _ in range(count):
        tracks.append(pos)
        pos += step
    assert len(tracks) > 0
    tracks.sort()

    return tracks

# HUMAN SORTING: https://stackoverflow.com/questions/5967500/how-to-correctly-sort-a-string-with-a-number-inside
def natural_keys(enum):
    def atof(text):
        try:
            retval = float(text)
        except ValueError:
            retval = text
        return retval

    text = enum[0]
    text = re.sub(r"(\[|\]|\.|\$)", "", text)
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (see toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    """
    return [atof(c) for c in re.split(r"[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)", text)]

def bus_keys(enum):
    text = enum[0]
    m = re.match(r"^.*\[(\d+)\]$", text)
    if not m:
        return -1
    else:
        return int(m.group(1))

def parse_pin_config(config_file_name):
    pin_placement_cfg = {"#N": [], "#E": [], "#S": [], "#W": []}
    cur_side = None
    with open(config_file_name, "r") as config_file:
        for line in config_file:
            line = line.split()
            if len(line) == 0:
                continue

            if len(line) > 1:
                print("Only one entry allowed per line.")
                sys.exit(1)

            token = line[0]

            if cur_side is not None and token[0] != "#":
                pin_placement_cfg[cur_side].append(token)
            elif token not in ["#N", "#E", "#S", "#W", ]:
                print(
                    "Valid directives are #N, #E, #S, or #W.",
                    "Please make sure you have set a valid side first before listing pins",
                )
                sys.exit(1)
            else:
                cur_side = token
    return pin_placement_cfg

