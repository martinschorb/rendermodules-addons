
from argschema.fields import (
    InputDir, InputFile, Str, Int, Boolean, Float, List)

from asap.module.schemas import (
    StackTransitionParameters, InputStackParameters, OutputStackParameters)

class GenerateSBEMTileSpecsParameters(OutputStackParameters):
    
    image_directory = InputDir(
        required=True,
        description=("directory used in determining absolute paths to images. "
                     "Defaults to parent directory containing metafile "
                     "if omitted."))
    image_prefix = Str(
        required=False, description=(
            "prefix used in determining full uris of images in metadata. "
            "Defaults to using the / delimited prefix to "
            "the metadata_uri if omitted"))



class GenerateSerialEMTileSpecsParameters(OutputStackParameters):
    
    image_file = InputFile(
        required=True,
        description="metadata file containing SerialEM acquisition data (idoc)")
    z_spacing = Float(
        required=False, default=100.0,
        description="spacing between slices/ section thickness")
    
