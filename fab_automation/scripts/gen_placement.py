from ..util.project import *
import argparse

def gen_placement(prj):
    fab = prj.get_fabric()
    col_widths = [0 for x in range(fab.width())]
    row_heights = [0 for y in range(fab.height())]
    for (y, row) in enumerate(fab.tilegrid):
        for (x, tt) in enumerate(row):
            if tt == "NULL":
                continue
            tile_cfg = prj.tiles[tt]
            col_widths[x] = max(col_widths[x], tile_cfg.width / prj.prj_cfg.micron_scale)
            row_heights[y] = max(row_heights[y], tile_cfg.height / prj.prj_cfg.micron_scale)

    col_dx = [prj.fab_cfg.edge_space_e]
    col_dy = [prj.fab_cfg.edge_space_n]
    for w in col_widths:
        col_dx.append(col_dx[-1] + prj.fab_cfg.tile_space_h + w)
    for h in reversed(row_heights):
        col_dy.append(col_dy[-1] + prj.fab_cfg.tile_space_v + h)
    col_dy = list(reversed(col_dy))[1:]
    result = []
    for (y, row) in enumerate(fab.tilegrid):
        for (x, tt) in enumerate(row):
            if tt == "NULL":
                continue
            dx = int(col_dx[x] * prj.prj_cfg.micron_scale / 1000 + 0.1)
            dy = int(col_dy[y] * prj.prj_cfg.micron_scale / 1000 + 0.1)
            result.append((f"Inst_eFPGA_top.Inst_eFPGA.Tile_X{x}Y{y}_{tt}", dx, dy))
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prj', dest='prj', required=True)
    parser.add_argument('--out', dest='out', required=True)
    parser.add_argument('--gen_pdn', action='store_true')

    args = parser.parse_args()
    prj = TapeoutProject.parse(args.prj)
    plc = gen_placement(prj)
    with open(args.out, "w") as f:
        for m, x, y in plc:
            print(f"{m} {x} {y} N", file=f)
    if args.gen_pdn:
        print('set ::env(FP_PDN_MACRO_HOOKS) "\\')
        hooks = []
        for m, x, y in plc:
            if prj.prj_cfg.process == "gf180":
                hooks.append(f'{m} vdd vss vdd vss')
            else:
                hooks.append(f'"{m} vccd1 vssd1 vccd1 vssd1')
        for i, h in enumerate(hooks):
            term = '"' if i == len(hooks)-1 else ', \\'
            print(f"    {h}{term}")

if __name__ == '__main__':
    main()