from enum import Enum


class PanelizeType(Enum):
    V_CUT = "v-cut"
    MOUSEBITE = "mousebite"


class PanelizeItem:
    def __init__(
        self,
        path_prefix: str = "",
        outline_ext: str = "GM1",
        drill_suffix_pattern: str = ".TXT$",
        drill_output_ext: str = "TXT",
        x: float = 0.0,
        y: float = 0.0,
        angle: float = 0.0,
        row: int = 1,
        column: int = 1,
    ) -> None:
        self.path_prefix = path_prefix
        self.x = x
        self.y = y
        self.outline_ext = outline_ext
        self.drill_suffix_pattern = drill_suffix_pattern
        self.drill_output_ext = drill_output_ext
        self.angle = angle
        if row < 1:
            raise ValueError("row must be greater than 0")
        self.row = row
        if column < 1:
            raise ValueError("column must be greater than 0")
        self.column = column


class MouseBiteOption:
    def __init__(self, enable: bool = False, dxf_path: str = "") -> None:
        self.enable = enable
        self.dxf_path = dxf_path


class OutlineOption:
    def __init__(self, enable: bool = False, dxf_path: str = "") -> None:
        self.enable = enable
        self.dxf_path = dxf_path


class VCutOption:
    def __init__(self, offset: float = 0.0) -> None:
        self.offset = offset


class PanelizeScript:
    def __init__(
        self,
        type: PanelizeType = PanelizeType.V_CUT,
        width: float = 100.0,
        height: float = 100.0,
        fill: bool = False,
        target_extensions: list[str] = [
            "GTL",
            "GTO",
            "GTP",
            "GTS",
            "GBL",
            "GBO",
            "GBP",
            "GBS",
            "TXT",
        ],
        output: str = "",
        mousebite: MouseBiteOption = None,
        v_cut: VCutOption = None,
        custom_outline: OutlineOption = None,
        files: list[PanelizeItem] = [],
    ) -> None:
        self.type = type
        self.width = width
        self.height = height
        self.fill = fill
        self.target_extensions = target_extensions
        self.output = output
        self.mousebite = mousebite
        self.files = files
        self.v_cut = v_cut
        self.custom_outline = custom_outline
