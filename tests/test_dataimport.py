import tempfile
import pytest
import copy
import os
import numpy as np

import renderapi
from marshmallow.exceptions import ValidationError

from rmaddons.dataimport import (generate_EM_tilespecs_from_SBEMImage,
                                 generate_EM_tilespecs_from_SerialEMmontage,
                                 generate_EM_tilespecs_from_TIFStack)

from test_data import (render_params,
                       example_sbem,
                       sbemimage_template,
                       example_serialem,
                       serialem_template,
                       example_tif,
                       tif_template
                       )


@pytest.fixture(scope='module')
def render():
    return renderapi.connect(**render_params)

@pytest.mark.dependency()
def test_generate_SBEM(render):

    assert isinstance(render, renderapi.render.Render)

    ex = copy.deepcopy(generate_EM_tilespecs_from_SBEMImage.example_input)
    ex['render'] = render.make_kwargs()

    with tempfile.NamedTemporaryFile(suffix='.json') as probablyemptyfn:
        outfile = probablyemptyfn.name

    # test non existing directory
    ex['image_directory'] = example_sbem + 'notexistingdir'

    with pytest.raises(ValidationError):
        mod1 = generate_EM_tilespecs_from_SBEMImage.GenerateSBEMImageTileSpecs(input_data=ex)

    ex['image_directory'] = example_sbem

    # test non existing "meta" directory
    os.rename(example_sbem + '/meta', example_sbem + '/meta123')

    mod = generate_EM_tilespecs_from_SBEMImage.GenerateSBEMImageTileSpecs(input_data=ex)

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

    expected_tileIds = set(sbemimage_template['tileids'])
    delivered_tileIds = set(renderapi.stack.get_stack_tileIds(ex['stack'], render=render))

    # test if all tiles are imported
    assert len(expected_tileIds.symmetric_difference(delivered_tileIds)) == 0

    md = renderapi.stack.get_stack_metadata(render=render, stack=ex['stack'])

    expected_resolution = sbemimage_template['resolution']
    delivered_resolution = [md.stackResolutionX, md.stackResolutionY, md.stackResolutionZ]

    # test if resolution of stack is correct
    assert (np.array(expected_resolution) - np.array(delivered_resolution) == [0, 0, 0]).all()

    # this is needed for testing an export -> moved to 'test_materialize'
    # cleanup
    # os.system('rm -rf ' + example_sbem)
    # renderapi.stack.delete_stack(ex['stack'], render=render)


@pytest.mark.dependency()
def test_generate_SerialEM(render):

    assert isinstance(render, renderapi.render.Render)

    ex = copy.deepcopy(generate_EM_tilespecs_from_SerialEMmontage.example_input)
    ex['render'] = render.make_kwargs()

    with tempfile.NamedTemporaryFile(suffix='.json') as probablyemptyfn:
        outfile = probablyemptyfn.name

    # test non existing image file
    ex['image_file'] = os.path.join(example_serialem, 'notexistingfile')

    with pytest.raises(ValidationError):
        mod1 = generate_EM_tilespecs_from_SerialEMmontage.GenerateSEMmontTileSpecs(input_data=ex)

    ex['image_file'] = os.path.join(example_serialem, 'supermont.idoc')

    mod = generate_EM_tilespecs_from_SerialEMmontage.GenerateSEMmontTileSpecs(input_data=ex)

    stacks0 = mod.run()

    assert len(stacks0) == 1

    expected_stack0 = serialem_template['stack0']

    assert stacks0[0] == expected_stack0

    expected_tileIds = set(serialem_template['tileids0'])

    delivered_tileIds = set(renderapi.stack.get_stack_tileIds(stacks0[0], render=render))

    # test if all tiles are imported
    assert len(expected_tileIds.symmetric_difference(delivered_tileIds)) == 0

    md = renderapi.stack.get_stack_metadata(render=render, stack=stacks0[0])

    expected_resolution = serialem_template['resolution0']
    delivered_resolution = [md.stackResolutionX, md.stackResolutionY, md.stackResolutionZ]

    # test if resolution of stack is correct
    assert (np.array(expected_resolution) - np.array(delivered_resolution) == [0, 0, 0]).all()

    ex['image_file'] = os.path.join(example_serialem, 'mont01.idoc')

    mod = generate_EM_tilespecs_from_SerialEMmontage.GenerateSEMmontTileSpecs(input_data=ex)

    stacks = mod.run()

    assert len(stacks) == 5

    assert stacks == serialem_template['stacks']

    for stack in stacks:
        expected_tileIds = set(serialem_template['tileids'][stack])

        delivered_tileIds = set(renderapi.stack.get_stack_tileIds(stack, render=render))

        # test if all tiles are imported
        assert len(expected_tileIds.symmetric_difference(delivered_tileIds)) == 0

        md = renderapi.stack.get_stack_metadata(render=render, stack=stack)

        expected_resolution = serialem_template['resolutions'][stack]
        delivered_resolution = [md.stackResolutionX, md.stackResolutionY, md.stackResolutionZ]

        # test if resolution of stack is correct
        assert (np.array(expected_resolution) - np.array(delivered_resolution) == [0, 0, 0]).all()

        # cleanup
        renderapi.stack.delete_stack(stack, render=render)

    assert os.path.exists(example_serialem + '/conv_log')
    with open(os.path.join(example_serialem, 'conv_log', os.listdir(example_serialem + '/conv_log')[0])) as file:
        importlog = file.read()
    assert importlog == serialem_template['errorlog0'] + example_serialem + serialem_template['errorlog1']

    # cleanup
    os.system('rm -rf ' + example_serialem)
    renderapi.stack.delete_stack(stacks0[0], render=render)

@pytest.mark.dependency()
def test_generate_TIF(render):

    assert isinstance(render, renderapi.render.Render)

    ex = copy.deepcopy(generate_EM_tilespecs_from_TIFStack.example_input)
    ex['render'] = render.make_kwargs()

    with tempfile.NamedTemporaryFile(suffix='.json') as probablyemptyfn:
        outfile = probablyemptyfn.name

    # test non existing directory
    ex['image_directory'] = example_tif + 'notexistingdir'

    with pytest.raises(ValidationError):
        mod1 = generate_EM_tilespecs_from_TIFStack.GenerateTifStackTileSpecs(input_data=ex)

    # test directory not containing tifs
    ex['image_directory'] = example_sbem

    mod = generate_EM_tilespecs_from_TIFStack.GenerateTifStackTileSpecs(input_data=ex)

    with pytest.raises(FileNotFoundError):
        mod.run()

    # test wrong resolutions
    ex["pxs"] = [1, 2, 3, 4]

    with pytest.raises(ValidationError):
        mod1 = generate_EM_tilespecs_from_TIFStack.GenerateTifStackTileSpecs(input_data=ex)


    ex = copy.deepcopy(generate_EM_tilespecs_from_TIFStack.example_input)
    ex['render'] = render.make_kwargs()

    # test import
    ex['image_directory'] = example_tif

    mod3 = generate_EM_tilespecs_from_TIFStack.GenerateTifStackTileSpecs(input_data=ex)
    mod3.run()

    expected_tileIds = set(tif_template['tileids'])
    delivered_tileIds = set(renderapi.stack.get_stack_tileIds(ex['stack'], render=render))

    # test if all tiles are imported
    assert len(expected_tileIds.symmetric_difference(delivered_tileIds)) == 0

    md = renderapi.stack.get_stack_metadata(render=render, stack=ex['stack'])

    expected_resolution = tif_template['resolution']
    delivered_resolution = [md.stackResolutionX, md.stackResolutionY, md.stackResolutionZ]

    # test if resolution of stack is correct
    assert (np.array(expected_resolution) - np.array(delivered_resolution) == [0, 0, 0]).all()

    # cleanup
    os.system('rm -rf ' + example_tif)
    renderapi.stack.delete_stack(ex['stack'], render=render)
