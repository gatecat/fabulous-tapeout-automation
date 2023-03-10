from ..util.project import *
from ..util import yosys
from os import path
import pathlib
import shutil
import argparse

class TileBuilder:
    def __init__(self, prj, workdir, tile, seed_tile=None):
        self.prj = TapeoutProject.parse(prj)
        self.fabric = self.prj.get_fabric()
        self.workdir = workdir
        self.srcdir = f"{workdir}/src"
        self.tile = tile
        self.seed_tile = seed_tile
        self.verilog_src = []

    def prepare_dir(self):
        # create directory
        pathlib.Path(self.workdir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.srcdir).mkdir(parents=True, exist_ok=True)
        if self.tile in self.fabric.supertiles:
            # copy supertile verilog
            self.add_src(self.prj.verilog_path(f"./Tile/{self.tile}/{self.tile}.v"))
            seen_subtiles = set()
            for row in self.fabric.supertiles[self.tile].subtiles:
                for subtile in row:
                    if subtile in seen_subtiles:
                        continue
                    self.copy_tile_verilog(subtile, st_root=f"{self.tile}/")
                    seen_subtiles.add(subtile)
        else:
            self.copy_tile_verilog(self.tile)
        shutil.copy(self.prj.resolve_path(self.prj.prj_cfg.cell_map), self.workdir)
        yosys.create_blackboxes([self.prj.resolve_path(self.prj.prj_cfg.cell_map), ], f"{self.workdir}/cells_bb.v")

    def add_src(self, verilog):
        base = path.basename(verilog)
        shutil.copy(verilog, self.srcdir)
        self.verilog_src.append(base)

    def copy_tile_verilog(self, tile, st_root=""):
        tt = self.fabric.tiletypes[tile]
        self.add_src(self.prj.project_path(f"./Tile/{st_root}{tile}/{tile}.v"))
        switch_mat = self.prj.project_path(f"./Tile/{st_root}{tile}/{tile}_switch_matrix.v")
        if path.exists(switch_mat):
            self.add_src(switch_mat)
        cfg_mem = self.prj.project_path(f"./Tile/{st_root}{tile}/{tile}_ConfigMem.v")
        if path.exists(cfg_mem):
            self.add_src(cfg_mem)
        for bel in tt.bel_verilog:
            self.add_src(self.prj.project_path(bel))

    @property
    def tile_verilog(self):
        return self.prj.project_path(f"./Tile/{self.tile}/{self.tile}.v")

    def create_pin_order(self):
        from .gen_pin_order import parse_tile_pins, gen_pin_order
        pins = parse_tile_pins(self.tile_verilog,
            ext_pin_edge=self.prj.tiles[self.tile].ext_pin_edge)
        seed_pins = []
        if self.seed_tile is not None:
            seed_pins = parse_tile_pins(self.tile_verilog, ext_pin_edge="")
        gen_pin_order(pins, f"{self.workdir}/pin_order.cfg", seed_pins=seed_pins)

    def create_def_template(self):
        from .gen_def_template import parse_pin_config, gen_def_template
        tile_cfg = self.prj.tiles[self.tile]
        port_bits = yosys.get_port_bits([self.tile_verilog, ], self.tile)
        pin_config = parse_pin_config(f"{self.workdir}/pin_order.cfg")
        physp = self.prj.pin_cfg
        gen_def_template(
            macro_size=(tile_cfg.width, tile_cfg.height),
            micron_scale=self.prj.prj_cfg.micron_scale,
            pin_config=pin_config,
            pins=port_bits,
            h_layer=(physp.h_layer, physp.h_grid, physp.h_width),
            v_layer=(physp.v_layer, physp.v_grid, physp.v_width),
            pin_length=physp.pin_length,
            top=self.tile,
            def_file=f"{self.workdir}/template.def",
        )

    def create_openlane_tcl(self):
        tile_cfg = self.prj.tiles[self.tile]
        with open(f"{self.workdir}/config.tcl", "w") as f:
            with open(self.prj.resolve_path(self.prj.prj_cfg.tile_base_config), "r") as tf:
                # template
                f.write(tf.read())
            print("", file=f)
            print(f"set ::env(DESIGN_NAME) {self.tile}", file=f)
            print(f"set ::env(VERILOG_FILES) \"$::env(DESIGN_DIR)/cells_bb.v {' '.join(f'$::env(DESIGN_DIR)/src/{s}' for s in self.verilog_src)}\"", file=f)
            print(f'set ::env(DIE_AREA) "0 0 {tile_cfg.width/self.prj.prj_cfg.micron_scale:.3f} {tile_cfg.height/self.prj.prj_cfg.micron_scale:.3f}"', file=f)
            print(f"set ::env(SYNTH_LATCH_MAP) $::env(DESIGN_DIR)/{path.basename(self.prj.prj_cfg.cell_map)}", file=f)
            print(f"set ::env(FP_PIN_ORDER_CFG) $::env(DESIGN_DIR)/pin_order.cfg", file=f)
            print(f"set ::env(FP_DEF_TEMPLATE) $::env(DESIGN_DIR)/template.def", file=f)
            print(f"set ::env(PL_TARGET_DENSITY) {tile_cfg.target_density}", file=f)
            print(f"set ::env(BASE_SDC_FILE) $::env(DESIGN_DIR)/design.sdc", file=f)

    def create_makefile(self):
        with open(f"{self.workdir}/Makefile", "w") as f:
            with open(self.prj.resolve_path(self.prj.prj_cfg.tile_base_makefile), "r") as tf:
                # template
                f.write(tf.read())


    def create_sdc(self):
        with open(f"{self.workdir}/design.sdc", "w") as f:
            with open(self.prj.resolve_path(self.prj.prj_cfg.tile_base_sdc), "r") as tf:
                # template
                f.write(tf.read())
            # the name of the mux output pin
            if self.prj.prj_cfg.process == "gf180":
                opin = "Z"
            else:
                opin = "X"
            # add don't cares because multiplier paths could contain silly long loops
            if self.tile in self.fabric.supertiles:
                for y, row in enumerate(self.fabric.supertiles[self.tile].subtiles):
                    for x, subtile in enumerate(row):
                        print(f"set_disable_timing [get_pins Tile_X{x}Y{y}_{subtile}.Inst_{subtile}_switch_matrix.inst_cus_mux*/{opin}]", file=f)
            else:
                print(f"set_disable_timing [get_pins Inst_{self.tile}_switch_matrix.inst_cus_mux*/{opin}]", file=f)



    def run(self):
        self.prepare_dir()
        self.create_pin_order()
        self.create_def_template()
        self.create_sdc()
        self.create_openlane_tcl()
        self.create_makefile()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prj', dest='prj', required=True)
    parser.add_argument('--workdir', dest='workdir', required=True)
    parser.add_argument('--tile', dest='tile', required=True)
    args = parser.parse_args()
    builder = TileBuilder(**vars(args))
    builder.run()

if __name__ == '__main__':
    main()
