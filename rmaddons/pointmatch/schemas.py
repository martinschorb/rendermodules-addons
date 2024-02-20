import argschema
from argschema.fields import Str, InputDir, List, Int, Float, Bool, Nested

from asap.pointmatch.schemas import PointMatchClientOutputSchema
from asap.module.schemas import (FeatureRenderParameters, MatchWebServiceParameters,
                                 FeatureStorageParameters, MatchDerivationParameters,
                                 RenderClientParameters, FeatureRenderClipParameters)


class RenderStackRange(List):
    def _validate(self, value):
        # TODO
        # 2 elements
        # second larger first element
        # (within range of render stack)
        pass # pragma: no cover


class PointMatchParameters(argschema.ArgSchema, MatchWebServiceParameters,
                           FeatureRenderParameters, FeatureRenderClipParameters,
                           FeatureStorageParameters, MatchDerivationParameters):
    render = Nested(RenderClientParameters, required=True)
    tile_pair_dir = InputDir(required=True, description=(
        "Path to tile pair directory"))


class CCParameters(PointMatchParameters):
    ccFullScaleSampleSize = Int(required=True, description=(
        "Full scale pixel height or width for each sample. Combined with clip size to determine sample area."
    ))
    ccFullScaleStepSize = Int(required=True, description=(
        "Full scale pixels to offset each sample from the previous sample."
    ))
    ccMinResultThreshold = Float(required=True, description=(
        "Minimum correlation value for feature candidates."
    ))
    ccSubpixelAccuracy = Bool(required=False, default=True, description=(
        "Indicates whether subpixel accuracy should be used for correlation."
    ))
    ccCheckPeaks = Int(required=False, default=50, description=(
        "Number of peaks to check during phase correlation."
    ))
    matchMaxEpsilonFullScale = Int(required=True, default=5, description=(
        ""
    ))
