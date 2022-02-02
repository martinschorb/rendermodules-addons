import argschema
import os
from argschema.fields import (Str, OutputDir, Int, Boolean, Float,
                              List, Number, InputDir, Nested)

import marshmallow as mm


class InFileOrDir(Str):
    """InFileOrDir: subclass of  :class:`marshmallow.fields.Str` is a path to a
       a file or directory that exists and is accesible to the user. This is checked with os.access.
    """

    def _validate(self, value):

        if not os.path.isdir(value):
            validate_input_path(value)

        if sys.platform == "win32":
            try:
                x = list(os.scandir(value))
            except PermissionError:
                raise mm.ValidationError(
                    "%s is not a readable directory" % value)
        else:
            if not os.access(value, os.R_OK):
                raise mm.ValidationError(
                    "%s is not a readable directory" % value)


class ResolutionList(List):
    """
    ResolutionList: subclass of  :class:`marshmallow.fields.List` that needs to have length 3.
    """
    def _validate(self, value):
        if len(value) != 3 :
                    raise mm.ValidationError(
                            "Wrong dimensions for resolution list %s" % value)

class ScaleList(List):
    def _validate(self, value):

        flattened_list = [item for sublist in value for item in sublist]
        if any(type(item) != int for item in flattened_list):
            raise mm.ValidationError(
                "All entries in scale list %s need to be integers." % value)

        if any(len(item) != 3 for item in value):
            raise mm.ValidationError(
                "Wrong dimensions for scale list %s" % value)

        for idx,item in enumerate(value):
            if item != value[idx-1]:
                raise mm.ValidationError(
                    "Scale factors need to be consistent!")


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



