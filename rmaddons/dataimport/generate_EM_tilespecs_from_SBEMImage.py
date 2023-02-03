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

example_input = {
    "render": {
        "host": "localhost",
        "port": 8080,
        "owner": "000tests",
        "project": "tests",
        "client_scripts": (
            "/render/render-ws-java-client/src/main/scripts/")},
    "image_directory": "",
    "stack": "test_sbem",
    "overwrite_zlayer": True,
    "pool_size": 1,
    "close_stack": True,
    "z_index": 1,
    "output_stackVersion": {
        "stackResolutionX": 10.1
    }
}


class GenerateSBEMImageTileSpecs(StackOutputModule):
    default_schema = GenerateSBEMTileSpecsParameters
    default_output_schema = GenerateEMTileSpecsOutput

    def rotmatrix(self, angle):
        th = np.radians(angle)
        c, s = np.cos(th), np.sin(th)
        M = np.array(((c, -s), (s, c)))
        return M

    def parse_adoc(self, lines, delim=' = '):
        """
        converts an adoc-format string list into a dictionary

        :param list lines: adoc string list,
        :param str delim: delimiter of the dictionary assignment
        :return: dict of adoc key-value pairs

        """

        output = {}
        mainkey = None

        for line in lines:
            entry = line.split(delim)
            if entry != ['']:
                if len(entry) < 2:
                    mainkey = entry[0].strip('[]')
                    output[mainkey] = {}
                else:
                    output[mainkey].update({entry[0]: entry[2:]})

        return output

    imgdir = []

    def ts_from_SBEMtile(self, tile, pxs, rotation):
        """
        Generates a tilespec entry from a line in a SBEMImage tile definition

        :param dict tile:  SBEMImage tile definition
        :param float pxs:  Pixelsize
        :param float rotation: rotation from SBEMImage parameters
        :return f1: path to the raw image of the tile
        :return tilespec: a :class:`renderapi.tilespec.TileSpec` object with the metadata for this tile

        """

        # curr_posid = [int(tile['tileid'].split('.')[0]),int(tile['tileid'].split('.')[1])]
        # curr_pos = tilepos[posid.index(str(curr_posid[0])+'.'+str(curr_posid[1]))]

        # 2) The translation matrix to position the object in space (lower left corner)
        # mat_t = np.concatenate((np.eye(3),[[tile['glob_x']],[tile['glob_y']],[tile['glob_z']]]),axis=1)
        # mat_t = np.concatenate((mat_t,[[0,0,0,1]]))

        f1 = os.path.realpath(os.path.join(self.imgdir, tile['filename']))

        filepath = groupsharepath(f1)

        ip = renderapi.image_pyramid.ImagePyramid()
        ip[0] = renderapi.image_pyramid.MipMap(imageUrl='file://' + filepath)

        width = tile['tile_width']
        height = tile['tile_height']

        xpos = float(tile['glob_x']) / pxs
        ypos = float(tile['glob_y']) / pxs
        M = self.rotmatrix(rotation)
        
        rotshift = -np.array([width/2, height/2])
        rotshift1 = -rotshift
        pos = [xpos, ypos]

        tf_trans = renderapi.transform.AffineModel(
            B0=pos[0],
            B1=pos[1])

        tf_rot = renderapi.transform.AffineModel(
            M00=M[0, 0],
            M01=M[0, 1],
            M10=M[1, 0],
            M11=M[1, 1])

        tf_rot_shift = renderapi.transform.AffineModel(
            B0=rotshift[0],
            B1=rotshift[1])

        tf_rot_shift1 = renderapi.transform.AffineModel(
            B0=rotshift1[0],
            B1=rotshift1[1])


        print("Processing tile " + tile['tileid'] + " metadata for Render.")

        ts = renderapi.tilespec.TileSpec(
            tileId=tile['tileid'],
            imagePyramid=ip,
            z=tile['slice_counter'],  # tile['glob_z'],
            width=tile['tile_width'],
            height=tile['tile_height'],
            minint=0, maxint=255,
            tforms=[tf_rot_shift, tf_rot, tf_rot_shift1, tf_trans],
            # imagePyramid=ip,
            sectionId=tile['slice_counter'],
            scopeId='3View',
            cameraId='3View',
            # imageCol=imgdata['img_meta']['raster_pos'][0],
            # imageRow=imgdata['img_meta']['raster_pos'][1],
            stageX=pos[0],
            stageY=pos[1],
            rotation=0,
            pixelsize=pxs)

        # json_file = os.path.realpath(os.path.join(
        #     tilespecdir,outputProject+'_'+outputOwner+'_'+outputStack+'_%04d.json'%z))
        # fd=open(json_file, "w")
        # renderapi.utils.renderdump(tilespeclist,fd,sort_keys=True, indent=4, separators=(',', ': '))
        # fd.close()

        return f1, ts

    def ts_from_sbemimage(self, imgdir):
        """

        :param imgdir: input directory - SBEMImage project folder.
        :return: list of :class:`renderapi.tilespec.TileSpec` objects for all tiles.

        """
        imgdir = os.path.realpath(imgdir)
        self.imgdir = imgdir

        timestamp = time.localtime()

        log_name = '_{}{:02d}{:02d}-{:02d}{:02d}'.format(timestamp.tm_year, timestamp.tm_mon, timestamp.tm_mday,
                                                         timestamp.tm_hour, timestamp.tm_min)

        logfile = os.path.join(imgdir, 'conv_log', 'Render_convert' + log_name + '.log')

        if not os.path.exists(os.path.join(imgdir, 'meta')):
            raise FileNotFoundError('Change to proper directory!')

        mfile0 = os.path.join(imgdir, 'meta', 'logs', 'imagelist_')

        mfiles = glob.glob(mfile0 + '*')

        tspecs = []
        allspecs = []
        curr_res = -1
        stack_idx = 0

        for mfile in mfiles:

            if '_ov_' in mfile:
                if mfile.replace('_ov_', '_') in mfiles:
                    continue

            stackname = self.args.get("output_stack")

            # with open(mfile) as mf: ml = mf.read().splitlines()
            acq_suffix = mfile[mfile.rfind('_'):]

            mdfile = os.path.join(imgdir, 'meta', 'logs', 'metadata' + acq_suffix)

            with open(mdfile) as mdf:
                mdl = mdf.read().splitlines()

            conffile = os.path.join(imgdir, 'meta', 'logs', 'config' + acq_suffix)

            with open(conffile) as cf:
                cl = cf.read().splitlines()

            config = self.parse_adoc(cl[:cl.index('[overviews]')])

            sessioninfo = json.loads(mdl[0].replace("'", '"').lstrip('SESSION: '))

            z_thick = sessioninfo['slice_thickness']

            for line in mdl[1:]:
                if line.startswith('TILE: '):

                    tile = json.loads(line.replace("'", '"').lstrip('TILE: '))

                    grid_id = tile['tileid'].split('.')[0]

                    if grid_id not in sessioninfo['grids']:
                        raise ValueError('Problem with the SBEMImage metadata! Grid ID not found.')

                    grididx = sessioninfo['grids'].index(grid_id)

                    pxs = sessioninfo['pixel_sizes'][grididx]
                    rotation = sessioninfo['rotation_angles'][grididx]

                    # ----   CHECK if resolution changes during run
                    if not curr_res == -1:
                        if not pxs == curr_res:
                            raise ValueError('Change in pixel resolution currently not supported!')

                            # stack_idx += 1
                            # allspecs.append([stackname,tspecs,curr_res])
                            # stackname += '_' + '%02d' %stack_idx
                            # tspecs=[]

                    curr_res = pxs

                    f1, tilespeclist = self.ts_from_SBEMtile(tile, pxs, rotation)

                    if os.path.exists(f1):
                        tspecs.append(tilespeclist)
                    else:
                        fnf_error = 'ERROR: File ' + f1 + ' does not exist, skipping tile creation.'
                        if not os.path.exists(os.path.join(imgdir, 'conv_log')):
                            os.makedirs(os.path.join(imgdir, 'conv_log'))
                        print(fnf_error)
                        with open(logfile, 'w') as log:
                            log.writelines(fnf_error)

        resolution = [pxs, pxs, z_thick]

        allspecs.append([stackname, tspecs, resolution])

        return allspecs  # ,mipmap_args

    def run(self):
        # with open(self.args['metafile'], 'r') as f:
        #     meta = json.load(f)

        imgdir = self.args.get('image_directory')

        # print(imgdir)

        allspecs = self.ts_from_sbemimage(imgdir)

        # create stack and fill resolution parameters

        for specs in allspecs:
            self.args["output_stack"] = specs[0]

            # create stack and fill resolution parameters
            self.output_tilespecs_to_stack(specs[1])

            resolution = specs[2]
            url = 'http://' + self.args["render"]["host"].split('http://')[-1] + ':' + str(self.args["render"]["port"])
            url += '/render-ws/v1/owner/' + self.args["render"]["owner"]
            url += '/project/' + self.args["render"]["project"]
            url += '/stack/' + self.args["output_stack"]
            url += '/resolutionValues'

            requests.put(url, json=resolution)


if __name__ == "__main__":
    mod = GenerateSBEMImageTileSpecs(input_data=example_input)
    mod.run()
