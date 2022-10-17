import subprocess
import json
import tempfile
import os
from dataclasses import dataclass

def get_yosys():
    if "YOSYS" in os.environ:
        return os.environ["YOSYS"]
    else:
        return "yosys"

def run_yosys(verilog_files, top, script=None):
    assert not isinstance(verilog_files, str)
    sfd, script_path = tempfile.mkstemp(suffix=".ys")
    jfd, json_path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(sfd, "w") as f:
        for v in verilog_files:
            if v.endswith(".sv"):
                print(f"read_verilog -sv {v}", file=f)
            else:
                print(f"read_verilog {v}", file=f)
        if script is not None:
            for line in script:
                print(line, file=f)
        else:
            print(f"hierarchy -top {top}", file=f)
        print(f"write_json {json_path}", file=f)
    subprocess.check_output([get_yosys(), "-s", script_path])
    with open(json_path, "r") as f:
        result = json.load(f)
    os.unlink(script_path)
    os.unlink(json_path)
    return result

def create_blackboxes(verilog_files, out):
    assert not isinstance(verilog_files, str)
    sfd, script_path = tempfile.mkstemp(suffix=".ys")
    with os.fdopen(sfd, "w") as f:
        for v in verilog_files:
            if v.endswith(".sv"):
                print(f"read_verilog -lib -sv {v}", file=f)
            else:
                print(f"read_verilog -lib {v}", file=f)
        print(f"hierarchy", file=f)
        print(f"setattr -unset src", file=f)
        print(f"setattr -mod -unset src", file=f)
        print(f"write_verilog -blackboxes {out}", file=f)
    subprocess.check_output([get_yosys(), "-s", script_path])
    os.unlink(script_path)

@dataclass
class ModulePort:
        name: str
        width: int
        direction: str

def get_module_ports(verilog_files, top):
    j = run_yosys(verilog_files, top)
    m = j["modules"][top]
    result = []
    for port, data in sorted(m["ports"].items(), key=lambda x:x[0]):
        result.append(ModulePort(port, len(data["bits"]), data["direction"]))
    return result

def get_port_bits(verilog_files, top):
    ports = get_module_ports(verilog_files, top)
    result = []
    for p in ports:
        if p.width == 1:
            result.append((p.name, p.direction))
        else:
            result += [(f"{p.name}[{i}]", p.direction) for i in range(p.width)]
    return result

