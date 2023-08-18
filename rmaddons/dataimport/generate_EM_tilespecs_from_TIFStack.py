#!/usr/bin/env python
"""
Create tilespecs from a directory containing aplhabetically ordered tif files
"""

import os
from functools import partial

import tifffile

import renderapi
from asap.module.render_module import StackOutputModule

from asap.dataimport.schemas import GenerateEMTileSpecsOutput

from rmaddons.dataimport.schemas import GenerateTifStackTileSpecsParameters

from rmaddons.utilities.EMBL_file_utils import groupsharepath

import requests
import glob
import numpy as np
from tifffile import TiffFile

example_input = {
    "render": {
        "host": "localhost",
        "port": 8080,
        "owner": "FIBSEM",
        "project": "00tests",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/src/main/scripts/")},
    "image_directory":
        "/g/emcf/schorb/code/rendermodules-addons/tests/test_files/tif_testdata",
    "pxs": [10, 10, 20],
    "autocrop": False,
    "output_stack": "test_stack",
    "overwrite_zlayer": True,
    "pool_size": 1,
    "close_stack": True,
    "z": 1,
    "startidx": 0,
    "endidx": -1,
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

        poolclass = renderapi.client.WithPool
        pool_size = self.args.get("pool_size")

        imgdir = os.path.realpath(imgdir)

        imfiles = glob.glob(os.path.join(imgdir, '*.[Tt][Ii][Ff]'))
        imfiles.extend(glob.glob(os.path.join(imgdir, '*.[Tt][Ii][Ff][Ff]')))

        imfiles.sort()

        startidx = self.args.get("startidx")
        endidx = self.args.get("endidx")

        if endidx == -1:
            imfiles = imfiles[startidx:]
        else:
            imfiles = imfiles[startidx:endidx+1]

        if imfiles == []:
            raise FileNotFoundError('No TIF files found!')

        resolution = self.args.get("pxs")[-1]  # in um
        autocrop = self.args.get("autocrop")

        transform = renderapi.transform.AffineModel(B0=0, B1=0)

        mypartial = partial(self.tiffile_to_ts, autocrop, imgdir, resolution, transform)

        with poolclass(pool_size) as pool:
            tspecs = pool.map(mypartial, list(zip(imfiles, range(len(imfiles)))))
            pool.close()
            pool.join()

        return tspecs

    def tiffile_to_ts(self, autocrop, imgdir, resolution, transform, inputkey):
        """
        Generates Render tilespecs for a single TIF image

        :param bool autocrop: if black borders should be auto-cropped
        :param str imgdir: the image directory
        :param list resolution: pixel resolution
        :param renderapi.transform.AffineModel transform: tile transform
        :param tuple inputkey: (image_name, section index)
        :return: ts
        :rtype: renderapi.tilespec.TileSpec
        """

        imfile, idx = inputkey
        f1 = os.path.realpath(os.path.join(imgdir, imfile))

        filepath = groupsharepath(f1)
        basefile = os.path.splitext(filepath)[0]

        # need to rename files to *.tif extension, otherwise render won't work

        os.system('mv ' + filepath + ' ' + basefile + '.temp')
        os.system('mv ' + basefile + '.temp ' + basefile + '.tif')
        filepath = basefile + '.tif'
        filepath1 = filepath

        with TiffFile(filepath) as im:
            width = im.pages.pages[0].imagewidth
            height = im.pages.pages[0].imagelength
            dtype = im.pages.pages[0].dtype.type

            min_x = 0
            max_x = width
            min_y = 0
            max_y = height

            if autocrop:
                image = im.asarray()
                imcontent = np.argwhere(image != 0)  # assume blackground is zero

                fdir = os.path.dirname(filepath)
                filepath1 = os.path.join(fdir, 'autocrop', os.path.basename(filepath))

                if not os.path.exists(os.path.join(fdir, 'autocrop')):
                    os.makedirs(os.path.join(fdir, 'autocrop'), exist_ok=True)

                if imcontent.size > 0:
                    min_x = imcontent[:, 0].min()
                    max_x = imcontent[:, 0].max()
                    min_y = imcontent[:, 1].min()
                    max_y = imcontent[:, 1].max()

                    imcrop = image[min_x:max_x + 1, min_y:max_y + 1]
                    width = max_y - min_y
                    height = max_x - min_x
                    transform = renderapi.transform.AffineModel(B0=min_x, B1=min_y)
                    tifffile.imsave(filepath1, imcrop)
                else:
                    os.system('cp ' + filepath + ' ' + filepath1)

                im.close()

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath1)
        slice = os.path.basename(os.path.splitext(imfile)[0])
        slsplit = slice.split('_')

        if slsplit[0] == 'slice' and slsplit[1].isnumeric():
            idx = int(slsplit[1])
        if idx % 50 == 0:
            print("Importing " + slice + " for Render.")
            print("\n...")

        # with open(os.path.join(imgdir,'trafo.txt'),'a') as f:
        #     f.write(str(transform))

        ts = renderapi.tilespec.TileSpec(
            tileId=slice,
            imagePyramid=ip,
            minX=min_x,
            minY=min_y,
            maxX=max_x,
            maxY=max_y,
            z=idx,
            width=width,
            height=height,
            minint=np.iinfo(dtype).min,
            maxint=np.iinfo(dtype).max,
            tforms=[transform],
            sectionId=idx,
            scopeId='TIFslice',
            cameraId='TIFslice',
            pixelsize=resolution)
        return ts

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
