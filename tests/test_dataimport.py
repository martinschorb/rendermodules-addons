import json
import tempfile
import pytest
import copy
import os

import renderapi
from marshmallow.exceptions import ValidationError

from asap.module.render_module import RenderModuleException
# from asap.dataimport import generate_EM_tilespecs_from_metafile
# from asap.dataimport import generate_mipmaps
# from asap.dataimport import apply_mipmaps_to_render

from rmaddons.dataimport import generate_EM_tilespecs_from_SBEMImage

from test_data import (render_params,
                       example_sbem)



@pytest.fixture(scope='module')
def render():
    return renderapi.connect(**render_params)

def test_generate_SBEM(render):
    # print(render_params)
    # os.system('ping '+render_params["host"] + ' -c 3')
    assert isinstance(render, renderapi.render.Render)

    ex = copy.deepcopy(generate_EM_tilespecs_from_SBEMImage.example_input)
    ex['render'] = render.make_kwargs()


    with tempfile.NamedTemporaryFile(suffix='.json') as probablyemptyfn:
        outfile = probablyemptyfn.name

    # test non existing directory
    ex['image_directory'] = example_sbem + 'notexistingdir'

    with pytest.raises(ValidationError):
        mod1 = generate_EM_tilespecs_from_SBEMImage.GenerateSBEMImageTileSpecs(input_data=ex,
                                                                           args=['--output_json', outfile])

    ex['image_directory'] = example_sbem

    # test non existing "meta" directory
    os.rename(example_sbem + '/meta', example_sbem + '/meta123')

    mod = generate_EM_tilespecs_from_SBEMImage.GenerateSBEMImageTileSpecs(input_data=ex,
                                                                           args=['--output_json', outfile])
    with pytest.raises(FileNotFoundError):
        mod.run()

    os.rename(example_sbem + '/meta123', example_sbem + '/meta')

    # test missing tile image reporting to log
    os.remove(example_sbem + '/tiles/g0000/t0008/test_example_g0000_t0008_s00005.jpg')

    mod.run()


#
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