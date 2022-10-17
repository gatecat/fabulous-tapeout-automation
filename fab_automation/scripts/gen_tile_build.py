from ..util.project import *
from ..util import yosys
from os import path
import pathlib
import shutil
import argparse

class TileBuilder:
    def __init__(self, prj, workdir, tile):
        self.prj = TapeoutProject.parse(prj)
        self.fabric = self.prj.get_fabric()
        self.workdir = workdir
        self.srcdir = f"{workdir}/src"
        self.tile = tile
        self.verilog_src = []

    def prepare_dir(self):
        # create directory
        pathlib.Path(self.workdir).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.srcdir).mkdir(parents=True, exist_ok=True)
        if self.tile in self.fabric.supertiles:
            # copy supertile verilog
            self.add_src(self.prj.verilog_path(f"{self.tile}_tile.v"))
            seen_subtiles = set()
            for row in self.fabric.supertiles[self.tile].subtiles:
                for subtile in row:
                    if subtile in seen_subtiles:
                        continue
                    self.copy_tile_verilog(subtile)
                    seen_subtiles.add(subtile)
        else:
            self.copy_tile_verilog(self.tile)

    def add_src(self, verilog):
        base = path.basename(verilog)
        shutil.copy(verilog, self.srcdir)
        self.verilog_src.append(base)

    def rewrite_bel(self, bel):
        # hack, we should really just have a fixed fabric.csv...
        if bel.endswith(".vhdl"):
            bel = f"{bel[:-5]}.v"
        if bel == "LUT4c_frame_config.v":
            bel = "LUT4c_frame_config_dffesr.v"
        if bel == "MUX8LUT_frame_config.v":
            bel = "MUX8LUT_frame_config_mux.v"
        return bel

    def copy_tile_verilog(self, tile):
        tt = self.fabric.tiletypes[tile]
        self.add_src(self.prj.verilog_path(f"{tile}_tile.v"))
        switch_mat = self.prj.verilog_path(f"{tile}_switch_matrix.v")
        if path.exists(switch_mat):
            self.add_src(switch_mat)
        cfg_mem = self.prj.verilog_path(f"{tile}_ConfigMem.v")
        if path.exists(cfg_mem):
            self.add_src(cfg_mem)
        for bel in tt.bel_verilog:
            self.add_src(self.prj.verilog_path(self.rewrite_bel(bel)))

    def run(self):
        self.prepare_dir()

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
