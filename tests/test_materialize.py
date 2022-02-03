#!/usr/bin/env python
'''
'''
import os
import copy

import pytest
import xml.etree.ElementTree as ET
from marshmallow.exceptions import ValidationError

import json
from rmaddons.materialize import make_xml
from test_data import (
                       example_dir,
                       example_n5,
                       makexml_template
                       )

def test_make_xml():
    # test if n5 sample exists
    assert os.path.exists(example_n5)

    # test n5 scale extraction
    rel_scales = make_xml.get_n5scales(example_n5)
    assert rel_scales == makexml_template['rel_scales']

    # test directory check
    baddir = example_dir+'/fakedir'

    os.makedirs(baddir,exist_ok=True)
    os.system('chmod -r '+baddir)
    os.system('ls -l '+example_dir)
    input_params = {'path':baddir}
    with pytest.raises(ValidationError):
        mod1 = make_xml.MakeXML(input_data=input_params)

    input_params['path'] = example_n5
    input_params['unit'] = 'lightyears'

    # test resolution format
    input_params ['resolution'] = [1,2,3,4]
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
    ip2['scale_factors'] = [[1, 1, 1],[2,2,2,2]]
    with pytest.raises(ValidationError):
        mod4 = make_xml.MakeXML(input_data=ip2)

    # consistency
    ip2['scale_factors'] = [[1, 1, 1], [2, 2, 2],[5,5,5]]
    with pytest.raises(ValidationError):
        mod5 = make_xml.MakeXML(input_data=ip2)

    xml_path = example_n5.replace('.n5', '.xml')

    mod = make_xml.MakeXML(input_data=input_params)

    mod.run()

    # test N5 attrib update
    for attdir in ['setup0','setup0/timepoint0']:
        with open(os.path.join(example_n5,attdir,'attributes.json')) as f:
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
    assert xmlsize.text == ' '.join(map(str,makexml_template['size']))

    # test if units and resolution fit
    voxs = vset.find('voxelSize')
    assert voxs is not None

    unit = voxs.find('unit')
    assert unit.text=='lightyears'

    pxs = voxs.find('size')
    assert pxs is not None
    res = copy.deepcopy(makexml_template['resolution'])
    res.reverse()
    res = map(float,res)
    assert pxs.text == ' '.join(map(str,res))


    input_params ['path'] = os.path.join(example_dir,'materialize_makexml.json')

    # test file type check
    with pytest.raises(TypeError):
        mod = make_xml.MakeXML(input_data=input_params)
        mod.make_render_xml(path=input_params['path'])

    # clean up
    os.system('rm -rf ' + example_n5)
    os.system('rm -rf ' + baddir)

    os.system('rm ' + xml_path)
