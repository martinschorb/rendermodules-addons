import json
import tempfile
import pytest
import copy
import os
import requests
import numpy as np

import renderapi
from marshmallow.exceptions import ValidationError

# from asap.module.render_module import RenderModuleException
# from asap.dataimport import generate_EM_tilespecs_from_metafile
# from asap.dataimport import generate_mipmaps
# from asap.dataimport import apply_mipmaps_to_render

from rmaddons.dataimport import generate_EM_tilespecs_from_SBEMImage

from test_data import (render_params,
                       example_sbem,
                       sbemimage_template
                       )


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

    assert os.path.exists(example_sbem + '/conv_log')
    with open(os.path.join(example_sbem, 'conv_log', os.listdir(example_sbem + '/conv_log')[0])) as file:
        importlog = file.read()

    assert importlog == sbemimage_template['errorlog0'] + example_sbem + sbemimage_template['errorlog1']


    with open(outfile, 'r') as f:
        outjson = json.load(f)

    # test correct output
    assert outjson['stack'] == ex['stack']

    expected_tileIds = set(sbemimage_template['tileids'])
    delivered_tileIds = set(renderapi.stack.get_stack_tileIds(ex['stack'], render=render))


    # test if all tiles are imported
    assert len(expected_tileIds.symmetric_difference(delivered_tileIds)) == 0

    url = 'http://'+render_params["host"] + ':' + str(render_params["port"])
    url += '/render-ws/v1/owner/' + render_params["owner"]
    url += '/project/' + render_params["project"]
    url += '/stack/' + ex["stack"]
    url += '/resolutionValues'

    r = requests.get(url)

    expected_resolution = sbemimage_template['resolution']
    delivered_resolution = r.json()

    # test if resolution of stack is correct
    assert (np.array(expected_resolution)-np.array(delivered_resolution)==[0,0,0]).all()

    # cleanup
    os.system('rm -rf ' + example_sbem)
    renderapi.stack.delete_stack(ex['stack'], render=render)



