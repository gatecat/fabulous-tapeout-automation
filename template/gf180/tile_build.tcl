set ::env(PDK) "gf180mcuC"
set ::env(STD_CELL_LIBRARY) "gf180mcu_fd_sc_mcu7t5v0"

set ::env(CLOCK_PERIOD) "80"
set ::env(CLOCK_PORT) "UserCLK"
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
set ::env(DIODE_INSERTION_STRATEGY) 4
