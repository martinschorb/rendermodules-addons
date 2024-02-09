#!/usr/bin/env python
'''
'''
import os
import copy
import random
import string
import shutil
import numpy as np

import pytest
import xml.etree.ElementTree as ET

from marshmallow.exceptions import ValidationError
import renderapi
from renderapi.errors import RenderError
from asap.module.render_module import RenderModuleException

from skimage.io import imread

import json
from rmaddons.materialize import make_xml, addtomobie, render_export_sections
from rmaddons.dataimport import generate_EM_tilespecs_from_SBEMImage

from test_data import (render_params,
                       example_dir,
                       example_n5,
                       makexml_template,
                       mobie_template,
                       sliceexport_template
                       )

baddir = os.path.join(example_dir, 'fakedir')
defaultscale = 0.1

@pytest.fixture(scope='module')
def render():
    return renderapi.connect(**render_params)


@pytest.mark.dependency()
def test_make_xml():
    # test if n5 sample exists
    assert os.path.exists(example_n5)

    # test n5 scale extraction
    rel_scales = make_xml.get_n5scales(example_n5)
    assert rel_scales == makexml_template['rel_scales']

    # test directory check

    os.makedirs(baddir, exist_ok=True)
    os.system('chmod -r ' + baddir)

    input_params = {'path': baddir}
    with pytest.raises(ValidationError):
        mod1 = make_xml.MakeXML(input_data=input_params)

    input_params['path'] = example_n5
    input_params['unit'] = 'lightyears'

    # test resolution format
    input_params['resolution'] = [1, 2, 3, 4]
    with pytest.raises(ValidationError):
        mod2 = make_xml.MakeXML(input_data=input_params)

    input_params['resolution'] = makexml_template['resolution']

    ip2 = dict()
    ip2.update(input_params)
    # test scale factors

    # integers?
    ip2['scale_factors'] = [[1, 1.5, 12]]
    with pytest.raises(ValidationError):
        mod3 = make_xml.MakeXML(input_data=ip2)

    # length
    ip2['scale_factors'] = [[1, 1, 1], [2, 2, 2, 2]]
    with pytest.raises(ValidationError):
        mod4 = make_xml.MakeXML(input_data=ip2)

    # consistency
    ip2['scale_factors'] = [[1, 1, 1], [2, 2, 2], [5, 5, 5]]
    with pytest.raises(ValidationError):
        mod5 = make_xml.MakeXML(input_data=ip2)

    xml_path = example_n5.replace('.n5', '.xml')

    mod = make_xml.MakeXML(input_data=input_params)

    mod.run()

    # test N5 attrib update
    for attdir in ['setup0', 'setup0/timepoint0']:
        with open(os.path.join(example_n5, attdir, 'attributes.json')) as f:
            att_template = json.load(f)

        assert makexml_template['n5_attribs'][attdir] == att_template

    # test XML file generation
    assert os.path.exists(xml_path)

    # test XML source link
    tree = ET.parse(xml_path)
    assert type(tree) is ET.ElementTree

    root = tree.getroot()
    assert type(root) is ET.Element

    # load the sequence description
    seqdesc = root.find('SequenceDescription')
    assert seqdesc is not None

    # load the ImageLoader
    imload = seqdesc.find('ImageLoader')
    assert imload is not None

    # test correct path to source
    n5path = imload.find('n5')
    assert n5path is not None
    assert n5path.text == os.path.basename(example_n5)

    # load the view descriptions
    viewsets = seqdesc.find('ViewSetups')
    assert viewsets is not None

    vset = viewsets.find('ViewSetup')
    assert vset is not None

    xmlsize = vset.find('size')
    assert xmlsize is not None

    # test if data size fits
    assert xmlsize.text == ' '.join(map(str, makexml_template['size']))

    # test if units and resolution fit
    voxs = vset.find('voxelSize')
    assert voxs is not None

    unit = voxs.find('unit')
    assert unit.text == 'lightyears'

    pxs = voxs.find('size')
    assert pxs is not None
    res = copy.deepcopy(makexml_template['resolution'])
    res.reverse()
    res = map(float, res)
    assert pxs.text == ' '.join(map(str, res))

    input_params['path'] = os.path.join(example_dir, 'materialize_makexml.json')

    # test file type check
    with pytest.raises(TypeError):
        mod = make_xml.MakeXML(input_data=input_params)
        mod.make_render_xml(path=input_params['path'])


@pytest.mark.dependency(depends=["test_make_xml"])
def test_mobie():
    xml_path = example_n5.replace('.n5', '.xml')
    assert os.path.exists(xml_path)

    input_params0 = addtomobie.example.copy()

    input_params0['xmlpath'] = os.path.join(example_dir, 'materialize_makexml.json')

    # test check for input file type
    with pytest.raises(ValidationError):
        mod = addtomobie.AddtoMoBIE(input_data=input_params0)

    input_params1 = addtomobie.example.copy()
    input_params1['xmlpath'] = xml_path

    # check if test dir exists already:
    while os.path.exists(input_params1['outpath']):
        input_params1['outpath'] = os.path.join(input_params1['outpath'],
                                                ''.join(random.choices(string.ascii_uppercase, k=8)))

    mod = addtomobie.AddtoMoBIE(input_data=input_params1)

    # addresses stupid mount issue in CI
    os.chdir(os.getcwd())

    mod.run()

    # test output directory
    assert os.path.exists(input_params1['outpath'])

    project_jsonf = os.path.join(input_params1['outpath'], 'project.json')

    # test project.json
    assert os.path.exists(project_jsonf)

    expected_project = set(mobie_template['project.json'])
    with open(project_jsonf) as pj:
        delivered_project = set(json.load(pj))

    assert len(expected_project.symmetric_difference(delivered_project)) == 0

    # test dataset
    expected_dsdir = os.path.join(input_params1['outpath'], mobie_template['project.json']["datasets"][0])

    assert os.path.exists(expected_dsdir)
    assert os.path.exists(os.path.join(expected_dsdir, 'images'))

    expected_dataset = set(mobie_template['dataset.json'])
    with open(os.path.join(expected_dsdir, 'dataset.json')) as pj:
        delivered_dataset = set(json.load(pj))

    assert len(expected_dataset.symmetric_difference(delivered_dataset)) == 0

    imtype = list(mobie_template["dataset.json"]["sources"]
                  [mobie_template['project.json']["datasets"][0]]
                  ["image"]["imageData"].keys())[0]

    imagedir = os.path.join(expected_dsdir, 'images', imtype.replace('.', '-'))

    assert os.path.exists(imagedir)

    xml_path = os.path.join(expected_dsdir,
                            mobie_template["dataset.json"]
                            ["sources"][mobie_template['project.json']["datasets"][0]]["image"]["imageData"]
                            [imtype]["relativePath"])

    assert os.path.exists(xml_path)
    assert os.path.exists(os.path.splitext(xml_path)[0] + '.' + imtype.replace('bdv.', ''))

    # cleanup
    os.system('rm -rf ' + input_params1['outpath'])


@pytest.mark.dependency(depends=["tests/test_dataimport.py::test_generate_SBEM"], scope='session')
def test_render_export_sections(render):
    assert isinstance(render, renderapi.render.Render)

    ex = copy.deepcopy(render_export_sections.example)
    render0 = render
    ex['render'] = render0.make_kwargs()
    ex['input_stack'] = generate_EM_tilespecs_from_SBEMImage.example_input['output_stack']
    ex['project'] = generate_EM_tilespecs_from_SBEMImage.example_input['render']['project']
    ex['output_json'] = './slices_out.json'

    # check if test dir exists already:
    while os.path.exists(ex['image_directory']):
        ex['image_directory'] = os.path.join(example_dir, ex['image_directory'],
                                             ''.join(random.choices(string.ascii_uppercase, k=8)))

    stacktest = copy.deepcopy(ex)

    stacktest['input_stack'] = "thisstackclearlydoesnotexist"

    mod0 = render_export_sections.RenderSectionAtScale_extended(input_data=stacktest)

    # test check for non-existing stack
    with pytest.raises(RenderError):
        mod0.run()

    slicetest = copy.deepcopy(ex)
    slicetest['minZ'] = 5e12

    mod1 = render_export_sections.RenderSectionAtScale_extended(input_data=slicetest)

    # test check for non-existing slice
    with pytest.raises(RenderModuleException):
        mod1.run()

    dirtest = copy.deepcopy(ex)
    dirtest['customPath'] = False

    # test default directories
    mod2 = render_export_sections.RenderSectionAtScale_extended(input_data=dirtest)

    mod2.run()

    outdir = os.path.join(ex['image_directory'], ex['render']['project'], ex['input_stack'],
                          sliceexport_template['fullpath'])
    assert os.path.exists(outdir)

    flist = sliceexport_template['images'].copy()

    for outfile in os.listdir(outdir):
        flist.remove(outfile.split('.' + ex['imgformat'])[0])

    assert flist == []

    # test one file
    imfile = '3.0.jpg'
    im = imread(os.path.join(outdir, imfile))

    assert (im.shape == np.floor(np.array(sliceexport_template["imsize"]))).all()

    assert str(im) == sliceexport_template[imfile]

    # remove generated subdirectories
    shutil.rmtree(os.path.join(ex['image_directory'], ex['render']['project']))

    # test output formats and custom path
    flist = []

    for outformat in ['tiff', 'png', 'jpg']:
        formattest = copy.deepcopy(ex)
        formattest['imgformat'] = outformat
        formattest['customPath'] = True

        flist.extend([im + os.extsep + outformat for im in sliceexport_template['images']])

        mod = render_export_sections.RenderSectionAtScale_extended(input_data=formattest)
        mod.run()

        imfile = '3.0.' + outformat
        im = imread(os.path.join(ex['image_directory'], imfile))

        assert (im.shape == np.floor(np.array(sliceexport_template["imsize"]))).all()

        assert str(im) == sliceexport_template[imfile]

    for outfile in os.listdir(ex['image_directory']):
        flist.remove(outfile)

    assert flist == []

    # test scale and intensity
    downscale = 2

    scaletest = copy.deepcopy(ex)
    scaletest['scale'] = defaultscale / downscale
    scaletest['minInt'] = 123
    scaletest['maxInt'] = 125
    scaletest['customPath'] = True
    scaletest['image_directory'] += '/scale'

    mod3 = render_export_sections.RenderSectionAtScale_extended(input_data=scaletest)
    mod3.run()

    # test one file
    imfile = 'scale/4.0.jpg'

    im1 = imread(os.path.join(scaletest['image_directory'], imfile))

    # test scaled size
    assert (im1.shape == np.floor(np.array(sliceexport_template["imsize"]) / downscale)).all()

    # test scaled image
    assert str(im1) == sliceexport_template[imfile]

    # cleanup
    os.system('rm -rf ' + ex['image_directory'])


@pytest.mark.dependency(depends=["test_make_xml", "test_mobie","test_render_export_sections"])
def test_cleanup(render):
    # clean up
    os.system('rm -rf ' + os.path.join(example_dir, '*_testdata'))
    os.system('rm -rf ' + 'slicedata')
    os.system('rm ./slices_out.json')
    renderapi.stack.delete_stack(generate_EM_tilespecs_from_SBEMImage.example_input['output_stack'], render=render)
