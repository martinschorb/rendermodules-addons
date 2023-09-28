import argschema
from argschema.fields import Str, InputDir, List, Int


class RenderStackRange(List(Int)):

    def _validate(self, value):
        # TODO
        # 2 elements
        # second larger first element
        # (within range of render stack)
        pass


class AMSTParameters(argschema.ArgSchema):
    tile_pair_dir = InputDir(required=True, description=(
        "Path to tile pair directory"))
    stack = Str(required=True, description=(
        "Render stack to process"
    ))
    z_range = RenderStackRange(required=True, description=(
        "Slice range of the stack to process"
    ))

