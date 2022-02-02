#!/usr/bin/env python
'''
'''
import os
import copy

import pytest


import renderapi
from asap.utilities.pillow_utils import Image
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
            mod.make_render_xml()

