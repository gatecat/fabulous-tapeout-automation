# FABulous tapeout automation

## Overview

The ultimate aim of this project is to provide "push-button" tapeouts of custom [FABulous](https://github.com/FPGA-Research-Manchester/FABulous) eFPGA fabrics using the OpenLane open VLSI flow and open Sky130/GF180 PDKs. Support for proprietary toolchains and PDKs will be considered in the future, too.

## Current Status

Currently this framework can automate the build of all tiles into hard macros given a configuration project (see the examples in `template/`). 

### Building tile macros

Once a tapeout project is created including the `tapeout.prj` configuration file for this tooling (based on a template), run the following command to generate OpenLane configurations for every tile in a build folder:

```
python3 -m fab_automation.scripts.gen_all_tiles --prj path/to/tapeout.prj --workdir /path/to/build/dir
```

After this, inside the specified build directory, running `make` will call OpenLane to build each tile's GDS (make sure any environemnt variables are set, and Docker is started, if necessary).

### Building Fabric/SoC

Building the final fabric is not yet fully automated, although a partial macro placement (currently excluding BRAM or other periphery IPs) can be generated using `scripts.gen_placement`. This can also generate a list of PDN hooks to paste into the OpenLane configuration.
This will be improved in a future version.

### Case Study

This tooling is being used to port FABulous to the new GF180 process, targetting the MPW0 shuttle, in [this project](https://github.com/gatecat/fabulous_mpw0gf).

# Important Configuration Settings

### General

 - Environment variables can be used, for example `${HOME}` and will be expanded as on the shell
 - Constants can be defined using syntax like `.def CONST 1000`, then `.CONST` will be replaced with `1000` (see the gf180 project for an example)

### `fabulous` section

 - `fabric_csv` is a path to the CSV file containing the tile grid and other fabric configuration
 - `verilog_root` is a path to the folder containing generated and bel verilog

### `project` section
 - `process` is the name of the process used, e.g. `sky130`
 - `micron_scale` is the number of DEF units per micron, default 1000 if not specified
 - `cell_map` is a relative path to a Verilog file used to map cells such as muxes and latches in the FABulous-generated verilog to technology cells
 - `tile_base_config` is a relative path to a Tcl file containing OpenLane configuration common to all tiles.
 - Likewise, `tile_base_sdc` contains a path to a base SDC (timing constraints) file applying to all tiles and `tile_base_makefile` contains the Makefile used for all tiles which should provide a `harden` target that calls OpenLane.

### `fabric` section

Only used when generating the placement files for an entire fabric, not for indivual tile builds

 - `tile_space_h` and `tile_space_v` are the horizontal and vertical gaps between tiles in microns
 - `edge_space_n` and `edge_space_e` are the padding to leave on the north and east edges of the fabric

### `pin_config` section

Configures the interface pins at the boundary of tile macros, used to wire tiles together. Horizontal and vertical pins are configured separately, as they will usually be on different layers.
 - `{h,v}_layer` layer to use for horizontal or vertical pins
 - `{h,v}_grid` routing grid in DEF units
 - `{h,v}_width` routing thickness in DEF units
 - `pin_length` amount to extend pins in DEF units

### `tile <tiletype>` sections

There should be one section per tile/supertile type in the fabric.
 - `width` and `height` are the dimensions of the tile in DEF units
 - `target_density` is the optional target density to pass to OpenLane (default 0.6)
 - `ext_pin_edge` is required for termination tiles only and specifies the edge to place external (not inter-tile) pins on - `NORTH`, `EAST`, `SOUTH` or `WEST`.
