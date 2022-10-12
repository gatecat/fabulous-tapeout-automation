import re
from dataclasses import dataclass
from typing import Optional

side_comment_re = re.compile(r"\s*\/\/\s*(Tile_X(\d+)Y(\d+)_)?(NORTH|EAST|SOUTH|WEST)\s*")
fab_pin_re = re.compile(r"\s*(input|output)\s*(\[(\d+):\d+\])?\s*([A-Za-z0-9_]+);\s*(\/\/(.*))?")
pin_meta_re = re.compile(r"wires:(\d+) X_offset:(-?\d+) Y_offset:(-?\d+)  source_name:([A-Z0-9_a-z]+) destination_name:([A-Z0-9_a-z]+)\s*")

@dataclass
class TilePin(object):
    name: str
    side: str
    iodir: str
    width: int
    subtile: Optional[tuple[int, int]] = None
    dx: int = 0
    dy: int = 0
    src_wire: Optional[str] = None
    dst_wire: Optional[str] = None

def get_tile_pins(filename):
    pins = []
    curr_side = ""
    with open(filename, "r") as f:
        for line in f:
            if m := side_comment_re.match(line):
                curr_side = m.group(4)
            elif m := fab_pin_re.match(line):
                iodir = m.group(1)
                if m.group(3) is not None:
                    width = int(m.group(3)) + 1
                else:
                    width = 1
                name = m.group(4)
                if name.startswith("Frame") or name.startswith("UserCLK"):
                    # sides for these will be resolved later...
                    side = None
                else:
                    side = curr_side
                pin = TilePin(name=name, side=side, iodir=iodir, width=width)
                if m.group(6) is not None:
                    if p := pin_meta_re.match(m.group(6)):
                        pin.dx = int(p.group(2))
                        pin.dy = int(p.group(3))
                        pin.src_wire = p.group(4)
                        pin.dst_wire = p.group(5)
                pins.append(pin)
    return pins

if __name__ == '__main__':
    import sys
    print(get_tile_pins(sys.argv[1]))

