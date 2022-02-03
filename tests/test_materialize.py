#!/usr/bin/env python
'''
'''
import os
import copy

import pytest
import xml.etree.ElementTree as ET

import renderapi
from rmaddons.materialize import make_xml
from test_data import (render_params,
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

    input_params = {'path':os.path.join(example_dir,'materialize_makexml.json')}
    mod = make_xml.MakeXML(input_data=input_params)

    # test file type check
    with pytest.raises(TypeError):
        mod.make_render_xml(path=input_params['path'])

    input_params['path'] = example_n5
    input_params['unit'] = 'lightyears'
    input_params['resolution']  = makexml_template['resolution']

    xml_path = example_n5.replace('.n5', '.xml')

    mod = make_xml.MakeXML(input_data=input_params)

    mod.run()

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


    # clean up
    os.system('rm -rf ' + example_n5)
    os.system('rm ' + xml_path)
