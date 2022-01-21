import warnings
import argschema
from asap.module.schemas import (
    RenderParameters, SparkParameters, MaterializedBoxParameters,
    ZRangeParameters, RenderParametersRenderWebServiceParameters)

from asap.materialize import (ScaleList,ResolutionList,InFileOrDir)

from argschema.fields import (Str, OutputDir, Int, Boolean, Float,
                              List, InputDir, Nested)
# from argschema.fields.files import validate_input_path
# from marshmallow import post_load
import marshmallow as mm
# import os
# import sys


class MakeXMLParameters(argschema.ArgSchema):
    path = InFileOrDir(required=True, description=(
        "Path to the image data. Supports N5 and HDF5"))
    scale_factors = ScaleList(List(Int,
                              cli_as_single_argument=True),
                              required=False,description=(
        "List of downsampling factors"),
        default = [[1,1,1]],
        cli_as_single_argument=True)
    resolution = ResolutionList(Float,required=False,
                                cli_as_single_argument=True,
                                description=(
        "List of voxel resolution."),
        default = [0.05, 0.015, 0.015])
    unit = mm.fields.Str(required=False,default='micrometer')




class MakeXMLOutput(argschema.schemas.DefaultSchema):
    pass



