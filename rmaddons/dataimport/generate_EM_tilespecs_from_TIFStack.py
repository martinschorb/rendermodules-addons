#!/usr/bin/env python
"""
Create tilespecs from SBEMImage dataset
"""

import os

import renderapi
from asap.module.render_module import StackOutputModule

from asap.dataimport.schemas import GenerateEMTileSpecsOutput

from rmaddons.dataimport.schemas import GenerateTifStackTileSpecsParameters

from rmaddons.utilities.EMBL_file_utils import groupsharepath

import requests
import glob
import numpy as np
from tifffile import TiffFile

# from pyEM import parse_adoc

example_input = {
    "render": {
        "host": "render.embl.de",
        "port": 8080,
        "owner": "FIBSEM",
        "project": "00tests",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/src/main/scripts/")},
    "image_directory":
        "/g/emcf/ronchi/Rompani-Andres/F128_test_voxelsize_22-05-18/"
	"F128_Santiago_Brain_8nm_XB550_22-05-18",
    "pxs": [0.01, 0.01, 0.01],
    "stack": "test_stack",
    "overwrite_zlayer": True,
    "pool_size": 1,
    "close_stack": True,
    "z_index": 1,
    "output_stackVersion": {
        "stackResolutionX": 10.1
    }
}


class GenerateTifStackTileSpecs(StackOutputModule):
    default_schema = GenerateTifStackTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput

    def ts_from_tifpath(self, imgdir):
        """

        :param imgdir: input directory - folder containing TIF slices.
        :return: list of :class:`renderapi.tilespec.TileSpec` objects for all tiles.

        """
        imgdir = os.path.realpath(imgdir)

        imfiles = glob.glob(os.path.join(imgdir, '*.[Tt][Ii][(F)(f)]'))

        if imfiles is []:
            raise FileNotFoundError('No TIF files found!')

        tspecs = []

        resolution = self.args.get("pxs")[-1]  # in um

        transform = renderapi.transform.AffineModel(B0=0, B1=0)

        for idx, imfile in enumerate(imfiles):

            f1 = os.path.realpath(os.path.join(imgdir, imfile))

            filepath = groupsharepath(f1)

            ip = renderapi.image_pyramid.ImagePyramid()
            ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)

            slice = os.path.basename(os.path.splitext(imfile)[0])

            slsplit = slice.split('_')

            if slsplit[0] == 'slice' and slsplit[1].isnumeric():
                idx = int(slsplit[1])

            if idx % 50 == 0:
                print("Importing " + slice + " for Render.")
                print("\n...")
            with TiffFile(imfile) as im:
                width = im.pages.pages[0].imagewidth
                height = im.pages.pages[0].imagelength
                dtype = im.pages.pages[0].dtype.type

            tspecs.append(renderapi.tilespec.TileSpec(
                tileId=slice,
                imagePyramid=ip,
                z=idx,
                width=width,
                height=height,
                minint=np.iinfo(dtype).min,
                maxint=np.iinfo(dtype).max,
                tforms=[transform],
                sectionId=idx,
                scopeId='TIFslice',
                cameraId='TIFslice',
                pixelsize=resolution))

        return tspecs

    def run(self):
        # with open(self.args['metafile'], 'r') as f:
        #     meta = json.load(f)

        imgdir = self.args.get('image_directory')

        # print(imgdir)

        tspecs = self.ts_from_tifpath(imgdir)

        # create stack and fill resolution parameters
        self.output_tilespecs_to_stack(tspecs)

        resolution = self.args.get("pxs")
        url = 'http://' + self.args["render"]["host"].split('http://')[-1] + ':' + str(self.args["render"]["port"])
        url += '/render-ws/v1/owner/' + self.args["render"]["owner"]
        url += '/project/' + self.args["render"]["project"]
        url += '/stack/' + self.args["output_stack"]
        url += '/resolutionValues'

        requests.put(url, json=resolution)


if __name__ == "__main__":
    mod = GenerateTifStackTileSpecs(input_data=example_input)
    mod.run()
