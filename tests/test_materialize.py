#!/usr/bin/env python
'''
'''
import os
import imghdr
import copy

import pytest


import renderapi
from asap.utilities.pillow_utils import Image
from asap.materialize import materialize_sections
from test_data import (render_params,
                       )


@pytest.fixture(scope='module')
def render():
    return renderapi.connect(**render_params)

