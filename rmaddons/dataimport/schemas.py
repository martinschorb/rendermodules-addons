from argschema.fields import (
    InputDir, InputFile, Str, Int, Boolean, Float, List)

from asap.module.schemas import (
    StackTransitionParameters, InputStackParameters, OutputStackParameters)

from rmaddons.materialize.schemas import ResolutionList

class GenerateSBEMTileSpecsParameters(OutputStackParameters):
    image_directory = InputDir(
        required=True,
        description=("directory used in determining absolute paths to images. "
                     "Defaults to parent directory containing metafile "
                     "if omitted."))

class GenerateTifStackTileSpecsParameters(GenerateSBEMTileSpecsParameters):
    pxs = ResolutionList(Float,
                         required=True,
                         cli_as_single_argument=True,
                         description=(
                             "List of voxel resolution."),
                         default=[0.05, 0.05, 0.05])


class GenerateSerialEMTileSpecsParameters(OutputStackParameters):
    image_file = InputFile(
        required=True,
        description="metadata file containing SerialEM acquisition data (idoc)")
    z_spacing = Float(
        required=False, default=100.0,
        description="spacing between slices/ section thickness")
