set ::env(CLOCK_PERIOD) "40"
set ::env(CLOCK_PORT) "UserCLK"
set ::env(CLOCK_TREE_SYNTH) 1
set ::env(CELL_PAD) 4

set ::env(FP_SIZING) "absolute"

# DESIGN_IS_CORE 1 default, 0 is a macro
set ::env(DESIGN_IS_CORE) 0  
set ::env(FP_PDN_CORE_RING) 0
set ::env(GLB_RT_MAXLAYER) 5

set ::env(SYNTH_MAX_FANOUT) 10

set ::env(FP_IO_VLENGTH) 0.8
set ::env(FP_IO_HLENGTH) 0.8
set ::env(FP_IO_HTHICKNESS_MULT) 2
set ::env(FP_IO_VTHICKNESS_MULT) 2

set ::env(ROUTING_CORES) 12
set ::env(TOP_MARGIN_MULT) 2
set ::env(BOTTOM_MARGIN_MULT) 2
set ::env(FP_IO_MODE) 0

set ::env(EXTRA_LEFS) "$::env(DESIGN_DIR)/sky130_fpga_bitmux.lef $::env(DESIGN_DIR)/sky130_fpga_routebuf.lef"
set ::env(EXTRA_GDS_FILES) $::env(DESIGN_DIR)/sky130_fpga_bitmux.gds

set ::env(VDD_PINS) "vccd1"
set ::env(GND_PINS) "vssd1"

set ::env(STA_WRITE_LIB) 0
set ::env(SYNTH_BUFFERING) {0}
set ::env(PL_RESIZER_BUFFER_INPUT_PORTS) {0}
set ::env(PL_RESIZER_BUFFER_OUTPUT_PORTS) {0}
set ::env(PL_RESIZER_DESIGN_OPTIMIZATIONS) {0}
set ::env(GRT_ALLOW_CONGESTION) 1
