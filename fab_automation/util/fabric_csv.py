from dataclasses import dataclass, field
from typing import Optional
from os import path

@dataclass
class TileWire:
    direction: str
    src_name: str
    dx: int
    dy: int
    dst_name: str
    wire_count: int

@dataclass
class FabricTile:
    tiletype: str
    bel_verilog: set[str] = field(default_factory=set)
    wires: list[TileWire] = field(default_factory=list)

@dataclass
class SuperTile:
    tiletype: str
    subtiles: list[list[str]]

@dataclass
class FabricCsv:
    root: str
    tiletypes: dict[str, FabricTile] = field(default_factory=dict)
    supertiles: dict[str, SuperTile] = field(default_factory=dict)
    tilegrid: list[list[str]] = field(default_factory=list)

    def height(self):
        return len(self.tilegrid)

    def width(self):
        return max(len(row) for row in self.tilegrid)

    def parse(filename):
        result = FabricCsv(root=path.abspath(path.dirname(filename)))
        lines = []
        with open(filename, "r") as f:
            for line in f:
                line = line.split('#')[0].strip().split(",")
                if len(line) == 0:
                    continue
                lines.append(line)
        lines.reverse() # so we can 'pop'

        def parse_grid(end_tok):
            grid = []
            while lines:
                l = lines.pop()
                if l[0] == end_tok:
                    break
                tile_line = []
                for t in l:
                    if t == "":
                        break
                    tile_line.append(t)
                if len(tile_line) > 0:
                    grid.append(tile_line)
            return grid

        while lines:
            l = lines.pop()
            cmd = l[0]
            if cmd == "":
                continue
            elif cmd == "FabricBegin":
                # parse tilegrid
                result.tilegrid = parse_grid("FabricEnd")
            elif cmd == "TILE":
                tiletype = l[1]
                tile = FabricTile(tiletype=tiletype)
                while lines:
                    l = lines.pop()
                    if l[0] == "EndTILE":
                        break
                    if l[0] == "BEL":
                        tile.bel_verilog.add(l[1].replace(".vhdl", ".v")) # ...?
                    if l[0] in ("NORTH", "SOUTH", "EAST", "WEST", "JUMP"):
                        tile.wires.append(TileWire(
                            l[0], l[1], int(l[2]), int(l[3]), l[4], int(l[5])
                        ))
                result.tiletypes[tiletype] = tile
            elif cmd == "SuperTILE":
                tiletype = l[1]
                tile = SuperTile(tiletype=tiletype, subtiles=parse_grid("EndSuperTILE"))
                result.supertiles[tiletype] = tile
        return result

if __name__ == '__main__':
    import sys, pprint
    pprint.pprint(FabricCsv.parse(sys.argv[1]))
