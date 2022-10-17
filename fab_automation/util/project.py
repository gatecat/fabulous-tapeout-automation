from dataclasses import dataclass, field, fields
from typing import Optional
from os import path

__all__ = ["PhysTileType", "PinConfig", "FabricConfig", "TapepoutProject"]

@dataclass
class PhysTileType:
    tiletype: str
    width: int
    height: int
    ext_pin_edge: str = ""

@dataclass
class PinConfig:
    h_layer: str
    h_grid: int
    h_width: int
    v_layer: str
    v_grid: int
    v_width: int
    pin_length: int

@dataclass
class FabricConfig:
    tile_space_h: int
    tile_space_v: int
    edge_space_n: int = 0
    edge_space_e: int = 0
    edge_space_s: int = 0
    edge_space_w: int = 0

@dataclass
class ProjectConfig:
    process: str = "sky130"
    cell_map: str = "./cell_map.v"
    tile_base_config: str = "./tile_build.tcl"

@dataclass
class FabulousIntegration:
    fabric_csv: str
    verilog_root: str

def _parse_section(sec_class, lines, init_args=dict()):
    args = dict()
    field_types = {field.name: field.type for field in fields(sec_class)}
    while lines:
        l = lines.pop()
        sl = l.split(" ")
        if len(sl) == 0:
            continue
        if sl[0].lower() == "end":
            break
        key = sl[0].lower()
        val = sl[1]
        if key not in field_types:
            assert False, f"field {key} not in type {sec_class}"
        args[key] = field_types[key](val)
    return sec_class(**init_args, **args)

@dataclass
class TapepoutProject:
    root: str
    tiles: dict[str, PhysTileType] = field(default_factory=dict)
    pin_cfg: Optional[PinConfig] = None
    fab_cfg: Optional[FabricConfig] = None
    prj_cfg: Optional[ProjectConfig] = None
    fabulous: Optional[FabulousIntegration] = None

    def parse(filename):
        lines = []
        result = TapepoutProject(root=path.abspath(path.dirname(filename)))
        with open(filename, "r") as f:
            for line in f:
                line = line.split('#')[0].strip()
                if len(line) == 0:
                    continue
                lines.append(line)
        lines.reverse() # so we can 'pop'
        while lines:
            l = lines.pop()
            sl = l.split(" ")
            if len(sl) == 0:
                continue
            cmd = sl[0].lower()
            if cmd == "tile":
                tile = _parse_section(PhysTileType, lines, init_args=dict(tiletype=sl[1]))
                result.tiles[tile.tiletype] = tile
            elif cmd == "pin_config":
                result.pin_cfg = _parse_section(PinConfig, lines)
            elif cmd == "fabric":
                result.fab_cfg = _parse_section(FabricConfig, lines)
            elif cmd == "project":
                result.prj_cfg = _parse_section(ProjectConfig, lines)
            elif cmd == "fabulous":
                result.fabulous = _parse_section(FabulousIntegration, lines)
            else:
                assert False, f"unknown command {cmd}"
        return result

    def resolve_path(self, p):
        p = path.expandvars(p)
        if path.isabs(p):
            return p
        else:
            return f"{self.root}/{p}"

    def get_fabric(self):
        from .fabric_csv import FabricCsv
        return FabricCsv.parse(self.resolve_path(self.fab_cfg.fabric_csv))

if __name__ == '__main__':
    import sys, pprint
    pprint.pprint(TapepoutProject.parse(sys.argv[1]))
