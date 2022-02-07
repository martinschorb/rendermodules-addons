import json
from six.moves import urllib
from six import viewkeys, iteritems
import tempfile
import logging
import pytest
import renderapi
import marshmallow as mm
from asap.utilities.pillow_utils import Image
from asap.module.render_module import RenderModuleException
from asap.dataimport import generate_EM_tilespecs_from_metafile
from asap.dataimport import generate_mipmaps
from asap.dataimport import apply_mipmaps_to_render
from test_data import (render_params,
                       )
import os
import copy


@pytest.fixture(scope='module')
def render():
    return renderapi.connect(**render_params)

def test_generate_SBEM(render):
    print(render_params)
    # os.system('ping '+render_params["host"] + ' -c 3')
    assert isinstance(render, renderapi.render.RenderClient)

#     with open(METADATA_FILE, 'r') as f:
#         md = json.load(f)
#     ex = copy.deepcopy(generate_EM_tilespecs_from_metafile.example_input)
#     ex['render'] = render.make_kwargs()
#     ex['metafile'] = METADATA_FILE
#     with tempfile.NamedTemporaryFile(suffix='.json') as probablyemptyfn:
#         outfile = probablyemptyfn.name
#     mod = generate_EM_tilespecs_from_metafile.GenerateEMTileSpecsModule(
#         input_data=ex, args=['--output_json', outfile])
#     mod.run()
#
#     with open(outfile, 'r') as f:
#         outjson = json.load(f)
#
#     assert outjson['stack'] == ex['stack']
#
#     expected_tileIds = {mod.tileId_from_basename(img['img_path'])
#                         for img in md[1]['data']}
#     delivered_tileIds = set(renderapi.stack.get_stack_tileIds(
#         ex['stack'], render=render))
#
#     renderapi.stack.delete_stack(ex['stack'], render=render)
#     assert len(expected_tileIds.symmetric_difference(delivered_tileIds)) == 0