#!/usr/bin/env python

from functools import partial
import time
import numpy as np

import renderapi
from asap.materialize.schemas import (RenderSectionAtScaleOutput)

from asap.materialize.render_downsample_sections import (check_stack_for_mipmaps,
                                                         create_tilespecs_without_mipmaps,
                                                         RenderSectionAtScale)
from asap.module.render_module import (RenderModuleException)

from rmaddons.materialize.schemas import RenderSectionAtScale_extendedParameters

example = {
    "render": {
        "host": "render.embl.de",
        "port": 8080,
        "owner": "SBEM",
        "project": "tests",
        "client_scripts": (
            "/g/emcf/software/render/render-ws-java-client/src/main/scripts")},
    "input_stack": "test_sliceexport",
    "image_directory": "./slicedata",
    "imgformat": "jpg",
    "scale": 0.1,
    "minZ": 2,
    "maxZ": 5,
    "customPath": True,
    "resolutionUnit": "nm",
    "output_json": './sliceexport.json'
}


class RenderSectionAtScale_extended(RenderSectionAtScale):
    default_schema = RenderSectionAtScale_extendedParameters
    default_output_schema = RenderSectionAtScaleOutput

    def downsample_specific_mipmapLevel(
            self, zvalues, input_stack=None, level=1, pool_size=1,
            image_directory=None, scale=None, imgformat=None,
            resolutionUnit=None, render=None, bounds=None,
            minInt=None, maxInt=None,
            **kwargs):
        """
        Exports a set of slices (or a subset defined by a bounding box) from a Render stack to image files.

        :param list zvalues: List of z values to select sections to export
        :param str input_stack: input stack name
        :param int level: mipmap level until which to downscale
        :param int pool_size: compute pool size
        :param str image_directory: output image directory
        :param float scale: output scaling
        :param str imgformat: image format ('tiff','png' or 'jpeg')
        :param str resolutionUnit: if output is TIF, include the resolution into the files' header(s)
        :param renderapi.render.Render render: :class:`renderapi.render.Render` Render connection
        :param dict bounds: :class:`asap.asap.materialize.schemas.Bounds` section boundaries
        :param int minInt: minimum Intensity to map the output
        :param int maxInt: maximum intensity to map the output
        :return: stack name that was processed
        """

        poolclass = renderapi.client.WithPool

        stack_has_mipmaps = check_stack_for_mipmaps(
            render, input_stack, zvalues)

        ds_source = input_stack
        # check if there are mipmaps in this stack
        temp_no_mipmap_stack = ""  # this needs initialization here for the delete to work
        if stack_has_mipmaps:
            print("stack has mipmaps")
            # clone the input stack to a temporary one with level 1 mip alone
            temp_no_mipmap_stack = "{}_no_mml_zs{}_ze{}_t{}".format(
                input_stack, min(zvalues), max(zvalues),
                time.strftime("%m%d%y_%H%M%S"))

            mypartial = partial(create_tilespecs_without_mipmaps,
                                render, input_stack, level)

            with poolclass(pool_size) as pool:
                all_resolved_ts = pool.map(mypartial, zvalues)

            # create stack - overwrites existing one
            render.run(renderapi.stack.create_stack, temp_no_mipmap_stack)

            # set stack state to LOADING
            render.run(renderapi.stack.set_stack_state,
                       temp_no_mipmap_stack, state='LOADING')

            for rtspecs in all_resolved_ts:
                render.run(renderapi.client.import_tilespecs_parallel,
                           temp_no_mipmap_stack,
                           rtspecs.tilespecs,
                           sharedTransforms=rtspecs.transforms,
                           poolsize=pool_size,
                           close_stack=True,
                           mpPool=poolclass)

            ds_source = temp_no_mipmap_stack

        if self.args.get("customPath"):
            cOF = '.'
            cSF = '.'
        else:
            cOF = None
            cSF = None

        if minInt == -1:
            minInt = None
        if maxInt == -1:
            maxInt = None

        # not implemented in render client scripts...
        # imtype = None
        #
        # if 'tif' in imgformat:
        #     imtype = 8

        render.run(renderapi.client.renderSectionClient,
                   ds_source,
                   image_directory,
                   zvalues,
                   scale=scale,
                   format=imgformat,
                   bounds=bounds,
                   customOutputFolder=cOF,
                   customSubFolder=cSF,
                   maxIntensity=maxInt,
                   minIntensity=minInt,
                   resolutionUnit=resolutionUnit,
                   convertToGray=True
                   )

        if stack_has_mipmaps:
            # delete the temp stack
            render.run(renderapi.stack.delete_stack,
                       temp_no_mipmap_stack)
        return ds_source

    def run(self):

        zvalues1 = self.render.run(
            renderapi.stack.get_z_values_for_stack,
            self.args['input_stack'])

        if self.args['minZ'] == -1:
            self.args['minZ'] = min(zvalues1)

        if self.args['maxZ'] == -1:
            self.args['maxZ'] = max(zvalues1)

        elif self.args['minZ'] > self.args['maxZ']:
            raise RenderModuleException('Invalid Z range: {} > {}'.format(
                self.args['minZ'], self.args['maxZ']))

        zvalues1 = np.array(zvalues1)
        zrange = range(int(self.args['minZ']), int(self.args['maxZ']) + 1)
        zvalues = list(set(zvalues1).intersection(set(zrange)))

        if self.args['bounds'] is None:
            if self.args['use_stack_bounds']:
                self.args['bounds'] = renderapi.stack.get_stack_bounds(
                    self.args['input_stack'], render=self.render)
                self.args['bounds'].pop('minZ')
                self.args['bounds'].pop('maxZ')

        if not zvalues:
            raise RenderModuleException(
                'No valid zvalues found in stack for '
                'given range {} - {}'.format(
                    self.args['minZ'], self.args['maxZ']))

        self.args['temp_stack'] = self.downsample_specific_mipmapLevel(
            zvalues, **dict(self.args, **{'render': self.render}))

        self.output({"image_directory": self.args['image_directory'],
                     "temp_stack": self.args['temp_stack']})


if __name__ == "__main__":
    mod = RenderSectionAtScale_extended(input_data=example)
    mod.run()
