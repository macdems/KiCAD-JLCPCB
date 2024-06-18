import glob
import os
import re
import shutil
import time
import traceback

import pcbnew
import wx

from .outline_measure import create_board_size_label
from .normalize_string import normalize

PLUGIN_NAME = 'JLCPCB'
OUTPUT_DIR = 'JLCPCB'
RETRY_COUNT = 10
RETRY_WAIT_SECOND = 0.1

version_major = int(re.match(r"^([0-9]*)\..*", pcbnew.Version()).group(1))
is_kicad_7plus = version_major >= 7

# https://jlcpcb.com/help/article/362-how-to-generate-gerber-and-drill-files-in-kicad-7
# https://jlcpcb.com/help/article/233-Suggested-Naming-Patterns

LAYERS = [
    (pcbnew.F_Cu, 'F_Cu', 0, '{}.gtl'),
    (pcbnew.B_Cu, 'B_Cu', 0, '{}.gbl'),
    (pcbnew.F_SilkS, 'F_Silks', 0, '{}.gto'),
    (pcbnew.B_SilkS, 'B_Silks', 0, '{}.gbo'),
    (pcbnew.F_Mask, 'F_Mask', 0, '{}.gts'),
    (pcbnew.B_Mask, 'B_Mask', 0, '{}.gbs'),
    (pcbnew.Edge_Cuts, 'Edge_Cuts', 0, '{}.gko'),
    (pcbnew.In1_Cu, 'In1_Cu', 3, '{}.g2l'),
    (pcbnew.In2_Cu, 'In2_Cu', 4, '{}.g3l'),
    (pcbnew.In3_Cu, 'In3_Cu', 5, '{}.g4l'),
    (pcbnew.In4_Cu, 'In4_Cu', 6, '{}.g5l'),
]


def remove_file_if_exists(file_patten, retry_count=RETRY_COUNT):
    for file_name in glob.glob(file_patten):
        if os.path.exists(file_name):
            os.remove(file_name)
            while (os.path.exists(file_name) and retry_count > 0):
                time.sleep(RETRY_WAIT_SECOND)
                retry_count -= 1


def rename_file_if_exists(src, dst):
    if os.path.exists(src):
        rename_file(src, dst)


def rename_file(src, dst, retry_count=RETRY_COUNT):
    try:
        remove_file_if_exists(dst)
        os.rename(src, dst)
    except Exception:
        if retry_count > 0:
            time.sleep(RETRY_WAIT_SECOND)
            rename_file(src, dst, retry_count - 1)
        else:
            raise Exception(f'Cannot rename {src} to {dst}')


def remove_dir_if_exits(dir_path_patten, retry_count=RETRY_COUNT):
    for dir_path in glob.glob(dir_path_patten):
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            while (os.path.exists(dir_path) and retry_count > 0):
                time.sleep(RETRY_WAIT_SECOND)
                retry_count -= 1


def make_dir(dir_path, retry_count=RETRY_COUNT):
    os.mkdir(dir_path)
    while (not os.path.exists(dir_path) and retry_count > 0):
        time.sleep(RETRY_WAIT_SECOND)
        retry_count -= 1


def plot_layers(board, gerber_dir, board_project_name):
    pc = pcbnew.PLOT_CONTROLLER(board)
    po = pc.GetPlotOptions()

    po.SetOutputDirectory(gerber_dir)
    po.SetPlotValue(True)
    po.SetPlotReference(True)
    if hasattr(po, "SetExcludeEdgeLayer"):
        po.SetExcludeEdgeLayer(True)
    if hasattr(po, "SetLineWidth"):
        po.SetLineWidth(pcbnew.FromMM(0.1))
    else:
        po.SetSketchPadLineWidth(pcbnew.FromMM(0.1))
    po.SetSubtractMaskFromSilk(False)
    po.SetUseAuxOrigin(False)
    po.SetUseGerberProtelExtensions(True)
    if hasattr(pcbnew, "PCB_PLOT_PARAMS.NO_DRILL_SHAPE"):
        po.SetDrillMarksType(pcbnew.PCB_PLOT_PARAMS.NO_DRILL_SHAPE)
    po.SetSkipPlotNPTH_Pads(False)

    layer_count = board.GetCopperLayerCount()

    for layer_id, layer_type, counter, rename_rule in LAYERS:
        if counter > layer_count:
            break
        pc.SetLayer(layer_id)
        pc.OpenPlotfile(layer_type, pcbnew.PLOT_FORMAT_GERBER, layer_type)
        pc.PlotLayer()
        plot_file_name = pc.GetPlotFileName()
        new_file_name = rename_rule.format(board_project_name)
        rename_file(plot_file_name, f'{gerber_dir}/{new_file_name}')

    pc.ClosePlot()


def plot_drill(board, gerber_dir, board_project_name):
    board_file_name = os.path.splitext(os.path.basename(board.GetFileName()))[0]
    ew = pcbnew.EXCELLON_WRITER(board)
    ew.SetFormat(True, pcbnew.EXCELLON_WRITER.DECIMAL_FORMAT, 3, 3)
    offset = pcbnew.VECTOR2I(0, 0) if is_kicad_7plus else pcbnew.wxPoint(0, 0)
    ew.SetOptions(False, False, offset, False)
    ew.SetMapFileFormat(pcbnew.PLOT_FORMAT_GERBER)
    ew.CreateDrillandMapFilesSet(gerber_dir, True, True)
    for suffix in ('PTH', 'NPTH'):
        rename_file_if_exists(f'{gerber_dir}/{board_file_name}-{suffix}.drl', f'{gerber_dir}/{board_project_name}-{suffix}.xln')
        rename_file_if_exists(
            f'{gerber_dir}/{board_file_name}-{suffix}-drl_map.gbr', f'{gerber_dir}/{board_project_name}-{suffix}.drl_map'
        )


def create_zip():
    board = pcbnew.GetBoard()
    size_label = create_board_size_label(board)
    board_file_name = board.GetFileName()
    board_dir = os.path.dirname(board_file_name)
    board_project_name = normalize(os.path.splitext(os.path.basename(board_file_name))[0])
    output_dir = os.path.join(board_dir, OUTPUT_DIR)
    gerber = board_project_name
    if size_label is not None:
        gerber += '-' + size_label
    gerber_dir = os.path.join(output_dir, gerber)
    zip_file = gerber_dir + '.zip'

    if not os.path.exists(output_dir):
        make_dir(output_dir)

    remove_dir_if_exits(gerber_dir)
    make_dir(gerber_dir)

    plot_layers(board, gerber_dir, board_project_name)

    plot_drill(board, gerber_dir, board_project_name)

    remove_file_if_exists(zip_file)
    shutil.make_archive(gerber_dir, 'zip', os.path.join(output_dir, gerber))

    return zip_file


class JlcPcbAction(pcbnew.ActionPlugin):

    def defaults(self):
        self.name = PLUGIN_NAME
        self.category = "Manufacturing"
        self.description = 'A plugin to create zip compressed gerber files to order PCB for JLCPCB.'
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'icon.png')

    def Run(self):
        try:
            zip_name = create_zip()
        except Exception as err:
            wx.MessageBox(f"Error: {err}\n\n" + traceback.format_exc(), PLUGIN_NAME, wx.OK | wx.ICON_INFORMATION)
        else:
            wx.MessageBox(f"Exported {zip_name}", PLUGIN_NAME, wx.OK | wx.ICON_INFORMATION)


JlcPcbAction().register()
