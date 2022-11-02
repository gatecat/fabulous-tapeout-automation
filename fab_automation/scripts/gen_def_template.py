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
import argparse
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
def natural_keys(text):
    def atof(text):
        try:
            retval = float(text)
        except ValueError:
            retval = text
        return retval

    text = re.sub(r"(\[|\]|\.|\$)", "", text)
    """
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (see toothy's implementation in the comments)
    float regex comes from https://stackoverflow.com/a/12643073/190597
    """
    return [atof(c) for c in re.split(r"[+-]?([0-9]+(?:[.][0-9]*)?|[.][0-9]+)", text)]

def bus_keys(text):
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

def order_pins(pin_config, pins):
    sorted_pins = list(sorted(pins, key=natural_keys))
    sorted_pins = list(sorted(sorted_pins, key=bus_keys))
    pin_placement = {"#N": [], "#E": [], "#S": [], "#W": []}
    pin_regex_map = {}
    for side in pin_config:
        for regex in pin_config[side]:
            regex += "$"
            for pin_name in pins:
                if re.match(regex, pin_name) is not None:
                    # check each pin is only matched by one regex...
                    assert pin_name not in pin_regex_map, (pin_name, pin_regex_map[pin_name], regex)
                    pin_placement[side].append(pin_name)
                    pin_regex_map[pin_name] = regex
    unmatched_pins = [pin_name for pin_name in pins if pin_name not in pin_regex_map]
    assert len(unmatched_pins) == 0, unmatched_pins
    return pin_placement

# Block boundaries: 0 0 223275 446230
#    (offset, count, grid)
# h  (340, 656, 680)
# v  (230, 485, 460)

def get_pin_layout(pins, grid, length):
    # TODO: so that modules can actually abut without channels, we need to special-case the gap between super-tiles...
    num_tracks = (length // grid) - 1
    offset = grid // 2
    result = []
    assert len(pins) < num_tracks, (len(pins), num_tracks)
    for i, pin in enumerate(pins):
        track = (i * num_tracks) // len(pins)
        pos = (track + 1) * grid + offset
        result.append((pin, pos))
    return result

def gen_def_template(macro_size, micron_scale, pin_config, pins, h_layer, v_layer, pin_length, top, def_file):
    with open(def_file, "w") as df:
        pin_names = [n for n, d in pins]
        pin_dirs = {n: d for n, d in pins}
        pin_placement = order_pins(pin_config, pin_names)
        width, height = macro_size

        print("VERSION 5.8 ;", file=df)
        print("DIVIDERCHAR \"/\" ;", file=df)
        print("BUSBITCHARS \"[]\" ;", file=df)
        print(f"DESIGN {top} ;", file=df)
        print(f"UNITS DISTANCE MICRONS {micron_scale} ;", file=df)
        print(f"DIEAREA ( 0 0 ) ( {width} {height} ) ;", file=df)
        print(f"PINS {len(pin_names)} ;", file=df)
        for side, pins in pin_placement.items():
            layer, grid, pin_width = v_layer if side in ("#N", "#S") else h_layer
            length = width if side in ("#N", "#S") else height
            layout = get_pin_layout(pins, grid, length)
            for pin, pos in layout:
                print(f"    - {pin} + NET {pin} + DIRECTION {pin_dirs[pin].upper()} + USE SIGNAL", file=df)
                print(f"      + PORT", file=df)
                pin_w = pin_width if side in ("#N", "#S") else pin_length
                pin_h = pin_length if side in ("#N", "#S") else pin_width
                if side == "#N":
                    pin_x = pos
                    pin_y = height - pin_h // 2
                elif side == "#E":
                    pin_x = pin_w // 2
                    pin_y = pos
                elif side == "#S":
                    pin_x = pos
                    pin_y = pin_h // 2
                elif side == "#W":
                    pin_x = width - pin_w // 2
                    pin_y = pos
                print(f"        + LAYER {layer} ( {-pin_w//2} {-pin_h//2} ) ( {pin_w//2} {pin_h//2} )", file=df)
                print(f"        + PLACED ( {pin_x} {pin_y} ) N ;", file=df)
        print("END PINS", file=df)
        print("END DESIGN", file=df)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', dest='cfg', required=True)
    parser.add_argument('--size', dest='size', required=True)
    parser.add_argument('--verilog', dest='verilog', required=True)
    parser.add_argument('--top', dest='top', required=True)
    parser.add_argument('--vlayer', dest='vlayer', required=True)
    parser.add_argument('--hlayer', dest='hlayer', required=True)
    parser.add_argument('--pinlen', dest='pinlen', required=True)
    parser.add_argument('--def', dest='def_file', required=True)

    args = parser.parse_args()
    from ..util import yosys
    port_bits = yosys.get_port_bits([args.verilog, ] , args.top)
    pin_config = parse_pin_config(args.cfg)
    macro_size = tuple(int(x) for x in args.size.split("x"))
    def parse_layer(l):
        l, g, w = l.split(":")
        return l, int(g), int(w)
    vlayer = parse_layer(args.vlayer)
    hlayer = parse_layer(args.hlayer)
    gen_def_template(macro_size, 1000, pin_config, port_bits, hlayer, vlayer, int(args.pinlen), args.top, args.def_file)
if __name__ == '__main__':
    main()