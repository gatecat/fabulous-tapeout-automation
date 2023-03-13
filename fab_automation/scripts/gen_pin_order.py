import re
from ..util.fabric_csv import FabricCsv
from dataclasses import dataclass
from typing import Optional

side_comment_re = re.compile(r"\s*\/\/\s*.*\.(NORTH|EAST|SOUTH|WEST)\s*")
fab_pin_re = re.compile(r"\s*(input|output)\s*(\[(\d+):\d+\])?\s*([A-Za-z0-9_]+),?\s*(\/\/(.*))?")
meta_data_re = re.compile(r".*Side=(NORTH|EAST|SOUTH|WEST).*")

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

def parse_tile_pins(fabric, tiletype, filename, ext_pin_edge=""):
    pins = []
    curr_side = ""
    with open(filename, "r") as f:
        for line in f:
            if m := side_comment_re.match(line):
                curr_side = m.group(1)
            elif line.strip() == "//Tile IO ports from BELs":
                curr_side = ext_pin_edge
            elif m := fab_pin_re.match(line):
                iodir = m.group(1)
                if m.group(3) is not None:
                    width = int(m.group(3)) + 1
                else:
                    width = 1
                name = m.group(4)
                if "Emulate_Bitstream" in name:
                    continue
                subtile = None
                if name.startswith("Tile_X"):
                    subtile, basename = split_supertile_pin(name)
                else:
                    basename = name
                if basename.startswith("Frame") or basename.startswith("UserCLK"):
                    # sides for these will be resolved later...
                    side = None
                else:
                    meta = m.group(6)
                    if n := meta_data_re.match(meta):
                        side = n.group(1)
                    else:
                        side = curr_side
                pin = TilePin(name=basename, side=side, subtile=subtile, iodir=iodir, width=width)
                tt = tiletype
                if subtile is not None:
                    tt = fabric.supertiles[tiletype].subtiles[subtile[1]][subtile[0]]
                if tt in fabric.tiletypes:
                    for w in fabric.tiletypes[tt].wires:
                        if w.src_name == basename or w.dst_name == basename:
                            pin.src_wire = w.src_name
                            pin.dst_wire = w.dst_name
                            pin.dx = w.dx
                            pin.dy = w.dy
                pins.append(pin)
    return pins

def opposite_side(s):
    if s == "NORTH": return "SOUTH"
    if s == "EAST": return "WEST"
    if s == "SOUTH": return "NORTH"
    if s == "WEST": return "EAST"
    assert False, s

def gen_pin_order(pins, result_file, seed_pins=[]):
    # seed pins is used to ensure a correct order for termination tiles
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
    # when working with a seed we need to build a list of which pin names
    # in the seed actually matter
    our_pins = set()
    for p in pins:
        our_pins.add(get_pin_name(p.subtile, p.name))
    # process pins
    pin_width = dict()
    for side in ("NORTH", "EAST", "SOUTH", "WEST"):
        for is_seed in False, True:
            for p in seed_pins if is_seed else pins:
                if p.side != side:
                    continue
                # add the primary pin 
                vert = side in ("NORTH", "SOUTH")
                if is_supertile:
                    offset = p.subtile[0] if vert else p.subtile[1]
                    # pins should only be on supertile fringe
                    if side == "NORTH": assert p.subtile[1] == 0
                    elif side == "EAST": assert p.subtile[0] == 0
                    elif side == "SOUTH": assert p.subtile[1] == height - 1
                    elif side == "WEST": assert p.subtile[0] == width - 1
                else:
                    offset = 0
                this_pin = get_pin_name(p.subtile, p.name)
                if not is_seed or this_pin in our_pins:
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
                    if not is_seed or op_pin in our_pins:
                        op_side = opposite_side(side)
                        if op_pin not in pin_placement[op_side][offset]:
                            pin_placement[op_side][offset].append(op_pin)
                            pin_width[op_pin] = p.width
    # write out
    def pin_regex(p):
        if p not in pin_width or pin_width[p] > 1:
            return f"{p}(\\[.*)?"
        else:
            return p
    with open(result_file, "w") as f:
        for side in ("NORTH", "EAST", "SOUTH", "WEST"):
            print(f"#{side[0]}", file=f)
            order = list(enumerate(pin_placement[side]))
            for i, subtile in reversed(order) if side in ("EAST", "WEST") else order:
                for pin in subtile:
                    print(f"{pin_regex(pin)}", file=f)
                # special pins (currently hardcoded)
                if side == "NORTH":
                    print(pin_regex(get_pin_name((i, 0), "UserCLKo")), file=f)
                    print(pin_regex(get_pin_name((i, 0), "FrameStrobe_O")), file=f)
                elif side == "SOUTH":
                    print(pin_regex(get_pin_name((i, height - 1), "UserCLK")), file=f)
                    print(pin_regex(get_pin_name((i, height - 1), "FrameStrobe")), file=f)
                elif side == "EAST":
                    print(pin_regex(get_pin_name((0, i), "FrameData_O")), file=f)
                elif side == "WEST":
                    print(pin_regex(get_pin_name((width-1, i), "FrameData")), file=f)
            print(f"", file=f)


if __name__ == '__main__':
    import sys
    csv = FabricCsv.parse(sys.argv[1])
    tiletype = sys.argv[2]
    pins = parse_tile_pins(sys.argv[3])
    gen_pin_order(csv, tiletype, pins, sys.argv[4])
