import re, math
from dataclasses import dataclass
from random import Random
# (pin, x, y)
def parse_layout(file):
    pins = []
    with open(file, "r") as f:
        curr_pin = ""
        for line in f:
            if m := re.search(r'- ([A-Za-z0-9_*\[\]]*) \+ NET', line):
                curr_pin = m.group(1)
            if m := re.search(r'\+ PLACED \( (\d+) (\d+) \) ', line):
                if curr_pin != "":
                    pins.append((curr_pin, int(m.group(1)), int(m.group(2))))
                curr_pin = ""
    return pins

@dataclass
class MuxBit:
    src: str
    dst: str
    word: int
    bit: int
    src_line: int

def parse_verilog(file):
    mux_bits = []
    input_bits = dict()
    curr_bitmux = ()
    with open(file, "r") as f:
        for lineno, line in enumerate(f):
            if curr_bitmux != ():
                m = re.search(r'.I\(([A-Za-z0-9_]+)_input\[(\d+)\]\), .O\([A-Za-z0-9_]+\)', line)
                assert m
                mux_bits.append(MuxBit(
                    src=input_bits[m.group(1)][int(m.group(2))],
                    dst=m.group(1),
                    word=curr_bitmux[0],
                    bit=curr_bitmux[1],
                    src_line=curr_bitmux[2]
                ))
                curr_bitmux = ()
            if m := re.search(r'assign ([A-Za-z0-9_]+)_input = {([A-Za-z0-9,\[\]_]+)}', line):
                input_bits[m.group(1)] = [x.strip() for x in m.group(2).split(",")]
                input_bits[m.group(1)].reverse()
            if m := re.search(r'\.BLP\(bitline_p\[(\d+)\]\), \.BLN\(bitline_n\[\d+\]\), \.WL\(wordline\[(\d+)\]\),', line):
                curr_bitmux = (int(m.group(2)), int(m.group(1)), lineno)
    return mux_bits

def do_solve(verilog, layout):
    pin_layout = parse_layout(layout)
    mux_bits = parse_verilog(verilog)
    bit_to_mux = dict()
    pin_to_mux = dict()
    pin_to_ext = dict()
    r  = Random(1)

    def normalise_wire(wire):
        # normalise jump wires
        if not wire.startswith("J"):
            return wire
        wire = wire.replace("JIN", "JOUT")
        wire = wire.replace("BEG", "END")
        return wire

    words = 0
    bits = 0

    for mux in mux_bits:
        bit_to_mux[(mux.bit, mux.word)] = mux
        words = max(words, mux.word+1)
        bits = max(bits, mux.bit+1)
        for wire in (mux.src, mux.dst):
            wire = normalise_wire(wire)
            if wire not in pin_to_mux:
                pin_to_mux[wire] = []
            pin_to_mux[wire].append(mux)

    print(f"{len(mux_bits)} muxes across {words} words, {bits} bits per word")

    width = 0
    height = 0
    for pin, x, y in pin_layout:
        width = max(width, x)
        height = max(height, y)
        pin_to_ext[pin.replace("[", "").replace("]", "")] = (x, y)

    def bit_pos(w, b):
        # assume config bits form an even grid, very approximate
        x = width * ((bits - 1) - b) / bits
        y = height * ((words - 1) - w) / words
        return (x, y)

    def hpwl(wire):
        locs = []
        if wire in pin_to_mux:
            for mux in pin_to_mux[wire]:
                locs.append(bit_pos(mux.word, mux.bit))
        x0 = min(p[0] for p in locs)
        x1 = max(p[0] for p in locs)
        y0 = min(p[1] for p in locs)
        y1 = max(p[1] for p in locs)
        mux_hpwl = (y1 - y0) + (x1 - x0)
        ext_hpwl = 0
        if wire in pin_to_ext:
            ext_dx = pin_to_ext[wire][0] - ((x1 + x0) // 2)
            ext_dy = pin_to_ext[wire][1] - ((y1 + y0) // 2)
            ext_hpwl = (abs(ext_dy) + abs(ext_dx))
        return mux_hpwl + ext_hpwl
    def total_hpwl():
        return sum(hpwl(w) for w in pin_to_mux.keys())

    temperature = 1
    n_accept = 0
    n_moves = 0
    def move_mux(mux, word, bit):
        mux.word = word
        mux.bit = bit
        bit_to_mux[(word, bit)] = mux

    def anneal_swap(mux, word, bit):
        nonlocal n_moves, n_accept
        n_moves += 1
        old_word = mux.word
        old_bit = mux.bit
        # see if position we are swapping to is occupied
        other_mux = bit_to_mux.get((word, bit), None)
        wires = set()
        wires.add(normalise_wire(mux.src))
        wires.add(normalise_wire(mux.dst))
        if other_mux:
            wires.add(normalise_wire(other_mux.src))
            wires.add(normalise_wire(other_mux.dst))
        old_hpwl = sum(hpwl(w) for w in wires)
        # perform swap and compute new HPWL
        move_mux(mux, word, bit)
        if other_mux:
            move_mux(other_mux, old_word, old_bit)
        else:
            bit_to_mux[(old_word, old_bit)] = None
        new_hpwl = sum(hpwl(w) for w in wires)
        delta = new_hpwl - old_hpwl
        if delta < 0 or (temperature > 1e-8 and (r.random() / 2) <= math.exp(-delta/temperature)):
            # accept
            n_accept += 1
        else:
            # revert
            move_mux(mux, old_word, old_bit)
            if other_mux:
                move_mux(other_mux, word, bit)
            else:
                bit_to_mux[(word, bit)] = None

    radius = words // 2
    i = 0
    avg_hpwl = total_hpwl()
    while temperature >= 1e-9:
        print(f"i={i} hpwl={total_hpwl()} T={temperature:.2f}")
        for j in range(10):
            for m in r.sample(mux_bits, k=len(mux_bits)):
                new_word = m.word + r.randint(-radius, radius)
                new_bit = m.bit + r.randint(-radius, radius)
                if new_word < 0 or new_word >= words or new_bit < 0 or new_bit >= bits:
                    # oob
                    continue
                anneal_swap(m, new_word, new_bit)
        r_accept = n_accept / n_moves
        curr_hpwl = total_hpwl()
        if curr_hpwl < (0.95 * avg_hpwl):
            avg_hpwl = 0.8 * avg_hpwl + 0.2 * curr_hpwl
        else:
            radius = max(1, min(words//2, int(radius * (1.0 - 0.44 + r_accept) + 0.5)))
            if r_accept > 0.96: temperature *= 0.5
            elif r_accept > 0.8: temperature *= 0.9
            elif r_accept > 0.15 and radius > 1: temperature *= 0.95
            else: temperature *= 0.8
        n_accept = 0
        n_moves = 0
        i += 1

    verilog_lines = []
    with open(verilog, "r") as f:
        verilog_lines = list(l for l in f)
    with open(f"{verilog}.bak", "w") as f:
        for l in verilog_lines:
            f.write(l)
    for m in mux_bits:
        assert "BLP" in verilog_lines[m.src_line], route_line # quick check we got roughly the right line...
        verilog_lines[m.src_line] = f"     .BLP(bitline_p[{m.bit}]), .BLN(bitline_n[{m.bit}]), .WL(wordline[{m.word}]),\n"
    with open(f"{verilog}", "w") as f:
        for l in verilog_lines:
            f.write(l)

if __name__ == '__main__':
    import sys
    do_solve(sys.argv[1], sys.argv[2])

