import argschema
import os
import sys
from argschema.fields import (Str, OutputDir, Int, Boolean, Float,
                              List, Field, InputDir, Nested)
from asap.materialize.schemas import (RenderSectionAtScaleParameters)

from argschema.fields.files import validate_input_path

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
                raise mm.exceptions.ValidationError(
                    "%s is not a readable directory" % value)
        else:
            if not os.access(value, os.R_OK):
                raise mm.exceptions.ValidationError(
                    "%s is not a readable directory" % value)


class ResolutionList(List):
    """
    ResolutionList: subclass of  :class:`marshmallow.fields.List` that needs to have length 3.
    """
    def _validate(self, value):
        if len(value) != 3 :
                    raise mm.exceptions.ValidationError(
                            "Wrong dimensions for resolution list %s" % value)

class ScaleList(List):
    def _validate(self, value):

        if any(len(item) != 3 for item in value):
            raise mm.exceptions.ValidationError(
                "Wrong dimensions for scale list %s" % value)

        flattened_list = [item for sublist in value for item in sublist]

        if any(type(item) != int for item in flattened_list):
            raise mm.exceptions.ValidationError(
                "All entries in lists of scale list %s need to be integers." % value)

        for idx,item in enumerate(value):
            if item != value[idx-1]:
                raise mm.exceptions.ValidationError(
                    "Scale factors need to be consistent!")


class MakeXMLParameters(argschema.ArgSchema):
    path = InFileOrDir(required=True, description=(
        "Path to the image data. Supports N5 and HDF5"))
    scale_factors = ScaleList(List(Field),required=False,description=(
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


class RenderSectionAtScale_extendedParameters(RenderSectionAtScaleParameters):
    customPath = Boolean(
        required=False,
        default=True,
        missing=True,
        description='Use custom path name (default - True)')
    minInt = Int(
        required=False,
        default=-1,
        missing=-1,
        description='minimum intensity for scaling output contrast')
    maxInt = Int(
        required=False,
        default=-1,
        missing=-1,
        description='maximum intensity for scaling output contrast')
    imtype = Int(
        required=False,
        default=-1,
        missing=-1,
        description='8,16,24 to specify what kind of image type to save')



