set ::env(PDK) "gf180mcuC"
set ::env(STD_CELL_LIBRARY) "gf180mcu_fd_sc_mcu7t5v0"

set ::env(CLOCK_PERIOD) "80"
set ::env(CLOCK_PORT) ""
set ::env(CLOCK_TREE_SYNTH) 1
set ::env(CELL_PAD) 4

set ::env(FP_SIZING) "absolute"

# set ::env(SYNTH_FLAT_TOP) "0"
# set ::env(SYNTH_NO_FLAT) "1"
# DESIGN_IS_CORE 1 default, 0 is a macro
set ::env(DESIGN_IS_CORE) 0  
set ::env(FP_PDN_CORE_RING) 0
set ::env(RT_MAX_LAYER) "Metal4"

set ::env(SYNTH_MAX_FANOUT) 10

set ::env(FP_IO_VLENGTH) 0.8
set ::env(FP_IO_HLENGTH) 0.8
set ::env(FP_IO_HTHICKNESS_MULT) 2
set ::env(FP_IO_VTHICKNESS_MULT) 2

set ::env(ROUTING_CORES) 12
set ::env(TOP_MARGIN_MULT) 2
set ::env(BOTTOM_MARGIN_MULT) 2
set ::env(FP_IO_MODE) 0

set ::env(VDD_NETS) [list {vdd}]
set ::env(GND_NETS) [list {vss}]
set ::env(VDD_PINS) [list {vdd}]
set ::env(GND_PINS) [list {vss}]
set ::env(DIODE_INSERTION_STRATEGY) 4

set ::env(EXTRA_LEFS) $::env(DESIGN_DIR)/gf180mcu_fpga_bitmux.lef
set ::env(EXTRA_GDS_FILES) $::env(DESIGN_DIR)/gf180mcu_fpga_bitmux.gds
set ::env(STA_WRITE_LIB) 0

set ::env(PL_MAX_DISPLACEMENT_X) 1000
set ::env(PL_MAX_DISPLACEMENT_Y) 1000
set ::env(SYNTH_BUFFERING) {0}
set ::env(PL_RESIZER_BUFFER_INPUT_PORTS) {0}
set ::env(PL_RESIZER_BUFFER_OUTPUT_PORTS) {0}
set ::env(PL_RESIZER_DESIGN_OPTIMIZATIONS) {0}
set ::env(GRT_ALLOW_CONGESTION) 1
