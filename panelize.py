#!/usr/bin/env python

import sys, os, json, re
import gerberex
from gerberex import DxfFile, GerberComposition, DrillComposition, PanelizeScript
from gerberex.panelize_script import PanelizeItem

f = open("panelize.json", "r")
ps = PanelizeScript(**json.load(f))

os.chdir(os.path.dirname(__file__))
try:
    os.mkdir("outputs")
except FileExistsError:
    pass


# output chars to stdout immediately
def putstr(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def merge_drill_to_ctx(
    filepath: str,
    target_ctx: DrillComposition = None,
    panelize_offset: tuple[int, int] = None,
    board_offset: tuple[int, int] = None,
) -> DrillComposition:
    if target_ctx:
        ctx = target_ctx
    else:
        ctx = DrillComposition()
    print(filepath)
    file = gerberex.read(filepath)
    file.draw_mode = DxfFile.DM_MOUSE_BITES
    file.to_metric()
    file.width = 0.5
    file.format = (3, 3)
    if panelize_offset:
        file.offset(
            -board_offset[0] + panelize_offset[0], -board_offset[1] + panelize_offset[1]
        )
    else:
        file.offset(-board_offset[0], -board_offset[1])
    ctx.merge(file)
    if not target_ctx:
        ctx.dump(ps.output + "." + ext)
    putstr("drill %s\n" % filepath)
    return ctx


def process_gerber(
    item: PanelizeItem,
    ext: str,
    panelize_offset: tuple[int, int] = None,
    board_offset: tuple[int, int] = None,
) -> tuple[tuple[int, int], tuple[int, int] | None]:
    ctx = GerberComposition()
    for y_count in range(0, item.row):
        for x_count in range(0, item.column):
            file = gerberex.read(f"{item.path_prefix}.{ext}")
            file.to_metric()
            size = file.size
            if board_offset:
                base_offset_x = item.x - board_offset[0]
                base_offset_y = item.y - board_offset[1]
            else:
                base_offset_x = item.x
                base_offset_y = item.y
            min_x = file.bounds[0][0]
            min_y = file.bounds[1][0]
            est_offset = (min_x, min_y)
            file.rotate(item.angle)
            if panelize_offset:
                file.offset(
                    base_offset_x + panelize_offset[0] * x_count,
                    base_offset_y + panelize_offset[1] * y_count,
                )
            else:
                file.offset(
                    base_offset_x - min_x + size[0] * x_count,
                    base_offset_y - min_y + size[1] * y_count,
                )
            putstr("_")
            ctx.merge(file)
    putstr(".")
    ctx.dump(ps.output + "." + ext)
    return (size, est_offset)


for v in ps.files:
    item = PanelizeItem(**v)

    # stage 1. Process PCB outline
    putstr("merging outline(%s): " % item.outline_ext)
    size, est_offset = process_gerber(item, item.outline_ext)
    putstr("\n")
    print("single board size: %.2fx%.2f" % size)
    print("estimated board offset: %.2fx%.2f" % est_offset)

    # stage 2. Process other gerber files
    for ext in ps.target_extensions:
        putstr("merging %s: " % ext)

        match ext:
            case "TXT":
                # if ps.mousebite and ps.mousebite["enable"] and ps.mousebite["dxf_path"]:
                merge_drill_to_ctx(ps.mousebite["dxt_path"])
            case _:
                process_gerber(item, ext, size, est_offset)
        putstr("\n")

    # stage 3. process drill files
    pattern = re.compile(os.path.basename(item.path_prefix) + item.drill_suffix_pattern)
    dir_name = os.path.dirname(item.path_prefix)
    matching_files = [
        os.path.join(dir_name, f) for f in os.listdir(dir_name) if pattern.match(f)
    ]
    ctx = DrillComposition()
    for f in matching_files:
        for y_count in range(0, item.row):
            for x_count in range(0, item.column):
                panel_offset = (size[0] * x_count, size[1] * y_count)
                merge_drill_to_ctx(
                    f,
                    target_ctx=ctx,
                    panelize_offset=panel_offset,
                    board_offset=est_offset,
                )
    ctx.dump(ps.output + "." + item.drill_output_ext)
    print(ps.output + "." + item.drill_output_ext)


if ps.custom_outline and ps.custom_outline["dxf_path"]:
    putstr("generating GML: ")
    file = gerberex.read(ps.custom_outline["dxf_path"])
    file.write(ps.output + ".GML")
    putstr(".")
    putstr(" end\n")

if ps.fill:
    ctx = GerberComposition()
    base = gerberex.rectangle(
        width=ps.width, height=ps.height, left=0, bottom=0, units="metric"
    )
    base.draw_mode = DxfFile.DM_FILL
    ctx.merge(base)
    file.draw_mode = DxfFile.DM_FILL
    file.negate_polarity()
    ctx.merge(file)
    ctx.dump(ps.output + "-fill.GML")

putstr(". end\n")
