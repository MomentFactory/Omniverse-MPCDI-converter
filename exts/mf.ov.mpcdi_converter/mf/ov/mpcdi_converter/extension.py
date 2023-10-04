import os
import time
from typing import List
import omni.ext
import omni.client
import carb
import omni.kit.notification_manager as nm
from omni.kit.notification_manager import NotificationStatus
from omni.kit.menu import utils
from omni.kit.tool.asset_importer.file_picker import FilePicker
from omni.kit.tool.asset_importer.filebrowser import FileBrowserMode, FileBrowserSelectionType
import omni.ui as ui
import omni.kit.tool.asset_importer as ai
import omni.kit.window.content_browser as content
from .omni_client_wrapper import OmniClientWrapper
import xml.etree.ElementTree as ET
from pxr import UsdGeom, Sdf, Gf, Tf
import math
import logging


class MPCDIConverterContext:
    usd_reference_path = ""


class MPCDIConverterHelper:
    def __init__(self):
        pass

    def _cleanNameForUSD(self, strIn: str) -> str:
        strOut = strIn
        # Do not allow for a blank name
        if len(strOut) == 0:
            return "Default"
        elif len(strOut) == 1 and strIn.isnumeric():
            # If we have an index as a name, we only need to add _ beforehand.
            return "_" + strIn

        return Tf.MakeValidIdentifier(strIn)

    def _convert_xml_to_usd(self, absolute_path_xml):
        result = 0

        try:
            _, _, content = omni.client.read_file(absolute_path_xml)

            data = memoryview(content).tobytes()

            # Read xml file here
            root = ET.fromstring(data)

            hasLensShifting = False
            stage = omni.usd.get_context().get_stage()

            mpcdiId = "/MPCDI"
            stage.DefinePrim(mpcdiId, "Xform")

            # Create usd content here
            for display in root:
                if display.tag != 'display':
                    continue

                for buffer in display:
                    bufferId = buffer.attrib['id']
                    bufferPath = mpcdiId + '/' + self._cleanNameForUSD(bufferId)
                    stage.DefinePrim(bufferPath, "Scope")

                    # A region is a projector
                    for region in buffer:
                        # GetCoordFrams
                        coordinateFrame = region.find('coordinateFrame')

                        # Get Position
                        posX = float(coordinateFrame.find('posx').text) * 10
                        posY = float(coordinateFrame.find('posy').text) * 10
                        posZ = float(coordinateFrame.find('posz').text) * 10

                        # Get Axis up
                        upX = float(coordinateFrame.find('yawx').text)
                        upY = float(coordinateFrame.find('yawy').text)
                        upZ = float(coordinateFrame.find('yawz').text)

                        # Get Axis right
                        rightX = float(coordinateFrame.find('pitchx').text)
                        rightY = float(coordinateFrame.find('pitchy').text)
                        rightZ = float(coordinateFrame.find('pitchz').text)

                        # Get Axis down
                        forwardX = float(coordinateFrame.find('rollx').text)
                        forwardY = float(coordinateFrame.find('rolly').text)
                        forwardZ = float(coordinateFrame.find('rollz').text)

                        # The "coordinateFrame" provided in the MPCDI comes with three vectors to solve any coordinate
                        # system ambiguity we meed to convert the position from the "source" coordinate system to the
                        # standard MPCDI system And then convert from the standard to the Omniverse system
                        sourceToStandard = Gf.Matrix3f(
                            rightX, rightY, rightZ,
                            upX, upY, upZ,
                            forwardX, forwardY, forwardZ)

                        # Omniverse uses the same axis for Roll/Pitch/Yaw than the standard, so we have a diagonal matrix
                        # BUT the Y and Z axis are pointing to the opposite direction, so we need to invert them
                        # in the matrix. Here we'll avoid a second matrix product and simply invert Y and Z of the
                        # vector instead.
                        newPos = sourceToStandard * Gf.Vec3f(posX, posY, posZ)
                        newPos[1] = newPos[1] * -1.0
                        newPos[2] = newPos[2] * -1.0

                        frustum = region.find('frustum')
                        yaw = float(frustum.find('yaw').text) * -1
                        pitch = float(frustum.find('pitch').text)
                        roll = float(frustum.find('roll').text)

                        # For the moment we do not support lens shifting, so we simply add the two angles and assume
                        # They are the same on both sides of the angle.
                        fovRight = float(frustum.find('rightAngle').text)
                        fovLeft = float(frustum.find('leftAngle').text)
                        fovTop = float(frustum.find('upAngle').text)
                        fovBottom = float(frustum.find('downAngle').text)

                        focalLength = 10  # We chose a fixed focal length.
                        tanRight = math.tan(math.radians(fovRight))
                        tanLeft = math.tan(math.radians(fovLeft))
                        tanUp = math.tan(math.radians(fovTop))
                        tanDown = math.tan(math.radians(fovBottom))
                        apertureH = (abs(tanRight) + abs(tanLeft)) * focalLength
                        apertureV = (abs(tanUp) + abs(tanDown)) * focalLength
                        lightWidth = abs(tanRight) + abs(tanLeft)
                        lightHeight = abs(tanUp) + abs(tanDown)

                        horizLensShiftAmount = (tanLeft + tanRight) / (tanLeft - tanRight)
                        vertLensShiftAmount = (tanUp + tanDown) / (tanUp - tanDown)
                        horizApertureOffset = horizLensShiftAmount * apertureH / 2.0
                        vertApertureOffset = vertLensShiftAmount * apertureV / 2.0

                        if fovRight != fovLeft or fovTop != fovBottom:
                            hasLensShifting = True

                        regionId = region.attrib['id']
                        primPath = bufferPath + '/' + self._cleanNameForUSD(regionId)

                        prim = stage.DefinePrim(primPath, "Camera")
                        prim.GetAttribute('focalLength').Set(focalLength)
                        prim.GetAttribute('focusDistance').Set(2000.0)

                        prim.GetAttribute('horizontalAperture').Set(apertureH)
                        prim.GetAttribute('horizontalApertureOffset').Set(horizApertureOffset)
                        prim.GetAttribute('verticalAperture').Set(apertureV)
                        prim.GetAttribute('verticalApertureOffset').Set(vertApertureOffset)

                        primXform = UsdGeom.Xformable(prim)

                        # This prevents from trying to add another Operation if overwritting nodes.
                        primXform.ClearXformOpOrder()

                        primXform.AddTranslateOp().Set(value=(newPos * 10.0))
                        primXform.AddRotateYOp().Set(value=yaw)
                        primXform.AddRotateXOp().Set(value=pitch)
                        primXform.AddRotateZOp().Set(value=roll)

                        # Create rectLight node
                        rectLightpath = primPath + '/ProjectLight'
                        rectLight = stage.DefinePrim(rectLightpath, 'RectLight')

                        # We need to create those attributes as they are not standard in USD and they are omniverse
                        # Specific. At this point in time Omniverse hasn't added their own attributes.
                        # We simply do it ourselves.
                        rectLight.CreateAttribute('isProjector', Sdf.ValueTypeNames.Bool).Set(True)
                        rectLight.CreateAttribute('intensity', Sdf.ValueTypeNames.Float).Set(15000)
                        rectLight.CreateAttribute('exposure', Sdf.ValueTypeNames.Float).Set(5)
                        rectLight.GetAttribute('inputs:width').Set(lightWidth)
                        rectLight.GetAttribute('inputs:height').Set(lightHeight)

                        # Creating projector box mesh to simulate the space a projector takes in the space
                        projectorBoxPath = primPath + '/ProjectorBox'
                        projector = stage.DefinePrim(projectorBoxPath, 'Cube')
                        projectorXform = UsdGeom.Xformable(projector)

                        projectorXform.ClearXformOpOrder()
                        projectorXform.AddTranslateOp().Set(value=(0, 0, 42.0))
                        projectorXform.AddScaleOp().Set(value=(50.0, 15, 40.0))
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to parse MPCDI file. Make sure it is not corrupt. {e}")
            return -1

        if hasLensShifting:
            message = "Lens shifting detected in MPCDI. Lens shifting is not supported."
            logger = logging.getLogger(__name__)
            logger.warn(message)
            nm.post_notification(message, status=NotificationStatus.WARNING)

        return result

    def _create_import_task(self, absolute_path, relative_path, export_folder, _):
        stage = omni.usd.get_context().get_stage()
        usd_path = ""

        # If the stage is not saved save the imported USD next to the original asset.
        if not stage or stage.GetRootLayer().anonymous:
            now = time.localtime()
            ext = time.strftime("_%H%M%S", now)
            basename = relative_path[:relative_path.rfind(".")]
            no_folder_name = absolute_path[:absolute_path.find("/" + relative_path)]
            host_dir = os.path.join(no_folder_name, "convertedAssets", basename + ext).replace("\\", "/")

        # Save the imported USD next to the saved stage.
        path_out = omni.usd.get_context().get_stage_url()

        # If user makes a selection for the output folder use it.
        if export_folder is not None:
            path_out = export_folder

        path_out_index = path_out.rfind("/")

        success = self._convert_xml_to_usd(absolute_path)  # self._hi.convert_cad_file_to_usd(absolute_path, path_out[:path_out_index])
        ext_index = relative_path.rfind(".")
        relative_path = self._cleanNameForUSD(relative_path[:ext_index]) + ".usd"
        usd_path = os.path.join(path_out[:path_out_index], relative_path).replace("\\", "/")

        logger = logging.getLogger(__name__)
        if success == 0:
            message = "Import succesful"
            logger.info(message)
            nm.post_notification(message)
            return usd_path
        elif success == -10002:
            # TODO this is when we have problem reading the file from OV, might need to download it locally
            logger.info("NOT IMPLEMENTED: Failure to load model form omniverse server, please select a file from local disk.")
            nm.post_notification(
                        f"Failed to convert file {os.path.basename(absolute_path)}.\n"
                        "Please check console for more details.",
                        status=nm.NotificationStatus.WARNING,
                    )
            return None
        else:
            logger.info("IMPORT FAILED")
            nm.post_notification(
                        f"Failed to convert file {os.path.basename(absolute_path)}.\n"
                        "Please check console for more details.",
                        status=nm.NotificationStatus.WARNING,
                    )
            return None

    async def create_import_task(self, absolute_paths, relative_paths, export_folder, hoops_context):
        converted_assets = {}
        for i in range(len(absolute_paths)):
            converted_assets[absolute_paths[i]] = self._create_import_task(absolute_paths[i], relative_paths[i],
                export_folder, hoops_context)
        return converted_assets

class MPCDIConverterOptions:
    def __init__(self):
        self.cad_converter_context = MPCDIConverterContext()
        self.export_folder: str = None


class MPCDIConverterOptionsBuilder:
    def __init__(self, usd_context):
        super().__init__()
        self._file_picker = None
        self._usd_context = usd_context
        self._export_context = MPCDIConverterOptions()
        self._folder_button = None
        self._refresh_default_folder = False
        self._default_folder = None
        self._clear()

    def _clear(self):
        self._built = False
        self._export_folder_field = None
        if self._folder_button:
            self._folder_button.set_clicked_fn(None)
            self._folder_button = None

    def set_default_target_folder(self, folder: str):
        self._default_folder = folder
        self._refresh_default_folder = True

    def build_pane(self, asset_paths: List[str]):
        self._export_context = self.get_import_options()
        if self._refresh_default_folder:
            self._export_context.export_folder = self._default_folder
            self._default_folder = None
            self._refresh_default_folder = False

        self._built = True

        OPTIONS_STYLE = {
             "Rectangle::hovering": {"background_color": 0x0, "border_radius": 2, "margin": 0, "padding": 0},
             "Rectangle::hovering:hovered": {"background_color": 0xFF9E9E9E},
             "Button.Image::folder": {"image_url": Icons().get("folder")},
             "Button.Image::folder:checked": {"image_url": Icons().get("folder")},
             "Button::folder": {"background_color": 0x0, "margin": 0},
             "Button::folder:checked": {"background_color": 0x0, "margin": 0},
             "Button::folder:pressed": {"background_color": 0x0, "margin": 0},
             "Button::folder:hovered": {"background_color": 0x0, "margin": 0},
        }
        with ui.VStack(height=0, style=OPTIONS_STYLE):
             ui.Spacer(width=0, height=5)
             with ui.HStack(height=0):
                ui.Label("Convert To:", width=0)
                ui.Spacer(width=3)
                with ui.VStack(height=0):
                    ui.Spacer(height=4)
                    self._export_folder_field = ui.StringField(height=20, width=ui.Fraction(1), read_only=False)
                    self._export_folder_field.set_tooltip(
                        "Left this empty will export USD to the folder that assets are under."
                    )
                    ui.Spacer(height=4)
                with ui.VStack(height=0, width=0):
                    ui.Spacer(height=4)
                    with ui.ZStack(width=20, height=20):
                        ui.Rectangle(name="hovering")
                        self._folder_button = ui.Button(name="folder", width=24, height=24)
                    self._folder_button.set_tooltip("Choose folder")
                    ui.Spacer(height=4)
                ui.Spacer(width=2)
                self._folder_button.set_clicked_fn(self._show_file_picker)
             ui.Spacer(width=0, height=10)

        if self._export_context.export_folder:
            self._export_folder_field.model.set_value(self._export_context.export_folder)
        else:
            self._export_folder_field.model.set_value("")

    def _select_picked_folder_callback(self, paths):
        if paths:
            self._export_folder_field.model.set_value(paths[0])

    def _cancel_picked_folder_callback(self):
        pass

    def _show_file_picker(self):
        if not self._file_picker:
            mode = FileBrowserMode.OPEN
            file_type = FileBrowserSelectionType.DIRECTORY_ONLY
            filters = [(".*", "All Files (*.*)")]
            self._file_picker = FilePicker("Select Folder", mode=mode, file_type=file_type, filter_options=filters)
            self._file_picker.set_file_selected_fn(self._select_picked_folder_callback)
            self._file_picker.set_cancel_fn(self._cancel_picked_folder_callback)

        folder = self._export_folder_field.model.get_value_as_string()
        if utils.is_folder(folder):
            self._file_picker.show(folder)
        else:
            self._file_picker.show(self._get_current_dir_in_content_window())

    def _get_current_dir_in_content_window(self):
        content_window = content.get_content_window()
        return content_window.get_current_directory()

    def get_import_options(self):
        context = MPCDIConverterOptions()
        # TODO enable this after the filepicker bugfix: OM-47383
        # if self._built:
        #     context.export_folder = str.strip(self._export_folder_field.model.get_value_as_string())
        #     context.export_folder = context.export_folder.replace("\\", "/")

        return context

    def destroy(self):
        self._clear()
        if self._file_picker:
            self._file_picker.destroy()


class MPCDIConverterDelegate(ai.AbstractImporterDelegate):
    def __init__(self, usd_context, name, filters, descriptions):
        super().__init__()
        self._hoops_options_builder = MPCDIConverterOptionsBuilder(usd_context)
        self._hoops_converter = MPCDIConverterHelper()
        self._name = name
        self._filters = filters
        self._descriptions = descriptions

    def destroy(self):
        if self._hoops_converter:
            self._hoops_converter.destroy()
            self._hoops_converter = None
        if self._hoops_options_builder:
            self._hoops_options_builder.destroy()
            self._hoops_options_builder = None

    @property
    def name(self):
        return self._name

    @property
    def filter_regexes(self):
        return self._filters

    @property
    def filter_descriptions(self):
        return self._descriptions

    def build_options(self, paths):
        pass
        # TODO enable this after the filepicker bugfix: OM-47383
        # self._hoops_options_builder.build_pane(paths)

    async def convert_assets(self, paths):
        context = self._hoops_options_builder.get_import_options()
        hoops_context = context.cad_converter_context
        absolute_paths = []
        relative_paths = []
        for file_path in paths:
            if self.is_supported_format(file_path):
                absolute_paths.append(file_path)
                filename = os.path.basename(file_path)
                relative_paths.append(filename)
        converted_assets = await self._hoops_converter.create_import_task(
             absolute_paths, relative_paths, context.export_folder, hoops_context
         )

        return converted_assets


_global_instance = None


# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MfMpcdiConverterExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    def on_startup(self, ext_id):
        global _global_instance
        _global_instance = self
        self._usd_context = omni.usd.get_context()

        self.delegate_mpcdi = MPCDIConverterDelegate(
            self._usd_context,
            "MPCDI Converter",
            ["(.*\\.mpcdi\\.xml$)"],
            ["mpcdi XML Files (*.mpdci.xml)"]
        )

        ai.register_importer(self.delegate_mpcdi)

    def on_shutdown(self):
        global _global_instance
        _global_instance = None

        ai.remove_importer(self.delegate_mpcdi)
        self.delegate_mpcdi = None
