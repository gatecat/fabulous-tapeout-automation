from ..util.project import *
from ..util import yosys
from os import path
import pathlib
import shutil
import argparse

from .gen_tile_build import TileBuilder

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prj', dest='prj', required=True)
    parser.add_argument('--workdir', dest='workdir', required=True)
    args = parser.parse_args()
    prj = TapeoutProject.parse(args.prj)

    fab = prj.get_fabric()
    used_tiles = set()
    for row in fab.tilegrid:
        for col in row:
            if col != "NULL":
                used_tiles.add(col)

    used_tiles = list(sorted(used_tiles))

    for tt in used_tiles:
        print(f"Generating files for {tt}...")
        builder = TileBuilder(prj=args.prj, workdir=f"{args.workdir}/{tt}", tile=tt)
        builder.run()

    with open(f"{args.workdir}/Makefile", "w") as mf:
        print(f"TARGETS={' '.join(f'{tt}/runs/build_tile/results/final/gds/{tt}.gds' for tt in used_tiles)}", file=mf)
        print("all: $(TARGETS)", file=mf)
        print()
        for tt in used_tiles:
            print(f"{tt}/runs/build_tile/results/final/gds/{tt}.gds:", file=mf)
            print(f"\t$(MAKE) -C {tt}", file=mf)

if __name__ == '__main__':
    main()
