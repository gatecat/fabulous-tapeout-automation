import re
from dataclasses import dataclass
from typing import Optional

side_comment_re = re.compile(r"\s*\/\/\s*(Tile_X(\d+)Y(\d+)_)?(NORTH|EAST|SOUTH|WEST)\s*")
fab_pin_re = re.compile(r"\s*(input|output)\s*(\[(\d+):\d+\])?\s*([A-Za-z0-9_]+);\s*(\/\/(.*))?")
pin_meta_re = re.compile(r"wires:(\d+)\s+X_offset:(-?\d+)\s+Y_offset:(-?\d+)\s+source_name:([A-Z0-9_a-z]+)\s+destination_name:([A-Z0-9_a-z]+)\s*")

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

def split_supertile_pin(pin):
    m = re.match(r"Tile_X(\d+)Y(\d+)_([A-Z0-9_a-z]+)", pin)
    assert m, pin
    return ((int(m.group(1)), int(m.group(2))), m.group(3))

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
                subtile = None
                if name.startswith("Tile_X"):
                    subtile, basename = split_supertile_pin(name)
                else:
                    basename = name
                if basename.startswith("Frame") or basename.startswith("UserCLK"):
                    # sides for these will be resolved later...
                    side = None
                else:
                    side = curr_side
                pin = TilePin(name=basename, side=side, subtile=subtile, iodir=iodir, width=width)
                if m.group(6) is not None:
                    if p := pin_meta_re.match(m.group(6)):
                        pin.dx = int(p.group(2))
                        pin.dy = int(p.group(3))
                        pin.src_wire = p.group(4)
                        pin.dst_wire = p.group(5)
                pins.append(pin)
    return pins

def opposite_side(s):
    if s == "NORTH": return "SOUTH"
    if s == "EAST": return "WEST"
    if s == "SOUTH": return "NORTH"
    if s == "WEST": return "EAST"
    assert False, s

def gen_pin_order(pins, result_file):
    width = 1
    height = 1
    is_supertile = False
    # get supertile dimensions
    for p in pins:
        if p.subtile is None:
            continue
        is_supertile = True
        width = max(width, p.subtile[0] + 1)
        height = max(height, p.subtile[1] + 1)
    # side -> subtile -> pins
    pin_placement = dict(
        NORTH=[[] for i in range(width)],
        EAST=[[] for i in range(height)],
        SOUTH=[[] for i in range(width)],
        WEST=[[] for i in range(height)],
    )
    def get_pin_name(subtile, basename):
        if is_supertile:
            return f"Tile_X{subtile[0]}Y{subtile[1]}_{basename}"
        else:
            return basename
    # process pins
    pin_width = dict()
    for side in ("NORTH", "EAST", "SOUTH", "WEST"):
        for p in pins:
            if p.side != side:
                continue
            # add the primary pin 
            vert = side in ("NORTH", "SOUTH")
            if is_supertile:
                offset = p.subtile[0] if vert else p.subtile[1]
            else:
                offset = 0
            # pins should only be on supertile fringe
            if side == "NORTH": assert p.subtile[1] == 0
            elif side == "EAST": assert p.subtile[0] == 0
            elif side == "SOUTH": assert p.subtile[1] == height - 1
            elif side == "WEST": assert p.subtile[0] == width - 1
            this_pin = get_pin_name(p.subtile, p.name)
            if this_pin not in pin_placement[side][offset]:
                pin_placement[side][offset].append(this_pin)
                pin_width[this_pin] = p.width
            # now we might need to make sure we add this pin's counterparty on the opposite side
            # in the same order we process this side, so the sides (at least roughly) line up
            # exact alignment, including supertiles and icky cases, is a future kbity problem...
            opposite_wire = None
            if p.src_wire is not None and p.src_wire != "NULL" and p.src_wire != p.name:
                assert p.dst_wire == p.name
                opposite_wire = p.src_wire
            if p.dst_wire is not None and p.dst_wire != "NULL" and p.dst_wire != p.name:
                assert p.src_wire == p.name
                opposite_wire = p.dst_wire
            if opposite_wire is not None:
                if is_supertile:
                    if vert:
                        op_subtile = (offset, ((height - 1) - p.subtile[1]))
                    else:
                        op_subtile = (((width - 1) - p.subtile[0]), offset)
                else:
                    op_subtile = (0, 0)
                op_pin = get_pin_name(op_subtile, opposite_wire)
                op_side = opposite_side(side)
                if op_pin not in pin_placement[op_side][offset]:
                    pin_placement[op_side][offset].append(op_pin)
                    pin_width[op_pin] = p.width
    # write out
    def pin_regex(p):
        if pin_width[p] > 1:
            return f"{p}(\\[?).*"
        else:
            return p
    with open(result_file, "w") as f:
        for side in ("NORTH", "EAST", "SOUTH", "WEST"):
            print(f"#{side[0]}", file=f)
            for subtile in pin_placement[side]:
                for pin in subtile:
                    print(f"{pin_regex(pin)}", file=f)
            print(f"", file=f)


if __name__ == '__main__':
    import sys
    pins = get_tile_pins(sys.argv[1])
    gen_pin_order(pins, sys.argv[2])
