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

    # get seed tiles to make sure we correctly order pins on termination tiles
    term_seeds = dict()
    for (y, row) in enumerate(fab.tilegrid):
        for (x, col) in enumerate(row):
            if col == "NULL" or col in term_seeds:
                continue
            if y == 0:
                term_seeds[col] = fab.tilegrid[y+1][x]
            elif y == len(fab.tilegrid) - 1:
                term_seeds[col] = fab.tilegrid[y-1][x]
            elif x == 0:
                term_seeds[col] = row[x+1]
            elif x == len(row) - 1:
                term_seeds[col] = row[x-1]
    used_tiles = list(sorted(used_tiles))

    # build termination tiles last, once we've figured out pin orders...
    for tt in used_tiles:
        if tt in term_seeds:
            continue
        print(f"Generating files for {tt}...")
        builder = TileBuilder(prj=args.prj, workdir=f"{args.workdir}/{tt}", tile=tt)
        builder.run()
    for tt in used_tiles:
        if tt not in term_seeds:
            continue
        print(f"Generating files for termination tile {tt}...")
        builder = TileBuilder(prj=args.prj, workdir=f"{args.workdir}/{tt}", tile=tt, seed_tile=term_seeds[tt])
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
