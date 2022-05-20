#!/usr/bin/env python
"""
Create tilespecs from SBEMImage dataset
"""

import os
import numpy as np
import renderapi
from asap.module.render_module import StackOutputModule

from asap.dataimport.schemas import GenerateEMTileSpecsOutput

from rmaddons.dataimport.schemas import GenerateSBEMTileSpecsParameters

from rmaddons.utilities.EMBL_file_utils import groupsharepath

import time
import requests
import glob

import json

# from pyEM import parse_adoc

example_input = {
    "render": {
        "host": "render.embl.de",
        "port": 8080,
        "owner": "FIBSEM",
        "project": "tests",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/src/main/scripts/")},
    "image_directory": "/g/emcf/ronchi/FINISHED/Arendt-Jake/Arendt_sponge_19-11-27/FIBSEM/jake_19-12-11_spongilla77-5/19-12-11_spongilla77-5_run",
    "pxs": [0.01,0.01,0.01],
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
        self.imgdir = imgdir

        timestamp = time.localtime()

        log_name = '_{}{:02d}{:02d}-{:02d}{:02d}'.format(timestamp.tm_year, timestamp.tm_mon, timestamp.tm_mday,
                                                         timestamp.tm_hour, timestamp.tm_min)

        logfile = os.path.join(imgdir, 'conv_log', 'Render_convert' + log_name + '.log')

        imfiles = glob.glob('*.[Tt][Ii][(F)(f)]')

        if imfiles is []:
            raise FileNotFoundError('No TIF files found!')

        imfile0 = os.path.join(imgdir,imfiles[0])

        tspecs = []

        stackname = self.args.get("output_stack")
        resolution = self.args.get("pxs")  # in um

        for idx,imfile in enumerate(imfiles):

            f1 = os.path.realpath(os.path.join(self.imgdir, imfile))

            filepath = groupsharepath(f1)

            ip = renderapi.image_pyramid.ImagePyramid()
            ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)

            slice = os.path.splitext(imfile)[0]

            slsplit = slice.split('_')

            if slsplit[0]=='slice' and slsplit[1].isnumeric():
                idx = int(slsplit[1])

            print("Importing " + slice + " for Render.")

            tspecs.append(renderapi.tilespec.TileSpec(
                tileId=slice,
                imagePyramid=ip,
                z=int,
                width=tile['tile_width'],
                height=tile['tile_height'],
                minint=0, maxint=255,
                sectionId=tile['slice_counter'],
                scopeId='TIFslice',
                cameraId='TIFslice',
                stageX=pos[0],
                stageY=pos[1],
                pixelsize=pxs))

        return tspecs

    def run(self):
        # with open(self.args['metafile'], 'r') as f:
        #     meta = json.load(f)

        imgdir = self.args.get('image_directory')

        # print(imgdir)

        tspecs = self.ts_from_tifpath(imgdir)

        # create stack and fill resolution parameters
        self.output_tilespecs_to_stack(tspecs)

        resolution = pxs
        url = 'http://' + self.args["render"]["host"].split('http://')[-1] + ':' + str(self.args["render"]["port"])
        url += '/render-ws/v1/owner/' + self.args["render"]["owner"]
        url += '/project/' + self.args["render"]["project"]
        url += '/stack/' + self.args["output_stack"]
        url += '/resolutionValues'

        requests.put(url, json=resolution)


if __name__ == "__main__":
    mod = GenerateTifStackTileSpecs(input_data=example_input)
    mod.run()
