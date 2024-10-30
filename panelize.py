#!/usr/bin/env python

import sys, os, json
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


def process_drill():
    ctx = DrillComposition()
    file = gerberex.read(ps.mousebite["dxf_path"])
    file.draw_mode = DxfFile.DM_MOUSE_BITES
    file.to_metric()
    file.width = 0.5
    file.format = (3, 3)
    ctx.merge(file)
    putstr("output mousebite")


def process_gerber(
    item: PanelizeItem, ext: str, offset: tuple[int, int] = None
) -> tuple[tuple[int, int], tuple[int, int] | None]:
    ctx = GerberComposition()
    for y_count in range(0, item.row):
        for x_count in range(0, item.column):
            file = gerberex.read(f"{item.path_prefix}.{ext}")
            file.to_metric()
            size = file.size
            base_offset_x = item.x
            base_offset_y = item.y
            min_x = file.bounding_box[0][0]
            min_y = file.bounding_box[1][0]
            est_offset = (min_x, min_y)
            file.rotate(item.angle)
            if offset:
                file.offset(
                    base_offset_x + offset[0] * x_count,
                    base_offset_y + offset[1] * y_count,
                )
            else:
                file.offset(
                    base_offset_x + min_x + size[0] * x_count,
                    base_offset_y + min_y + size[1] * y_count,
                )
            putstr("_")
            ctx.merge(file)
    putstr(".")
    ctx.dump(ps.output + "." + ext)
    return (size, est_offset)


for v in ps.files:
    item = PanelizeItem(**v)
    putstr("merging outline(%s): " % item.outline_ext)
    size, est_offset = process_gerber(item, item.outline_ext)
    putstr("\n")
    print("single board size: %.2fx%.2f" % size)
    print("estimated offset: %.2fx%.2f" % est_offset)

    for ext in ps.target_extensions:
        putstr("merging %s: " % ext)

        match ext:
            case "TXT":
                # if ps.mousebite and ps.mousebite["enable"] and ps.mousebite["dxf_path"]:
                process_drill()
            case _:
                process_gerber(item, ext, size)

        putstr("\n")

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
