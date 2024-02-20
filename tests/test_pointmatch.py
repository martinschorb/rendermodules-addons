#!/usr/bin/env python
"""
"""
import pytest
import shutil
import os
import json
import copy

import renderapi
from marshmallow.exceptions import ValidationError

from rmaddons.pointmatch.utils import split_tp
from rmaddons.pointmatch import generate_point_matches_cc
from rmaddons.dataimport import generate_EM_tilespecs_from_TIFStack

from test_data import (render_params,
                       example_dir,
                       example_tif,
                       cc_template
                       )


@pytest.fixture(scope='module')
def render():
    return renderapi.connect(**render_params)


@pytest.mark.dependency()
def test_split_tp():
    infile = os.path.join(example_dir, "tile_pairs.json")
    outdir = os.path.splitext(infile)[0] + "_split"

    maxsplit = 2
    split_tp(infile, maxsplit)

    splitfiles = ['split_1.json', 'split_0.json', 'split_2.json']

    assert os.path.exists(outdir)
    assert sorted(os.listdir(outdir)) == sorted(splitfiles)

    for splitfile in splitfiles:
        with open(os.path.join(outdir, splitfile)) as f:
            tp_test = json.load(f)

        assert len(tp_test["neighborPairs"]) <= maxsplit

    # higher maxsplit
    maxsplit = 3
    split_tp(infile, maxsplit)

    splitfiles = ['split_1.json', 'split_0.json']

    assert os.path.exists(outdir)
    assert sorted(os.listdir(outdir)) == sorted(splitfiles)

    for splitfile in splitfiles:
        with open(os.path.join(outdir, splitfile)) as f:
            tp_test = json.load(f)

        assert len(tp_test["neighborPairs"]) <= maxsplit

    # cleanup
    shutil.rmtree(outdir)


@pytest.mark.dependency()  # depends=["tests/test_dataimport.py::test_generate_TIF"], scope='session')
def test_generate_PM_CC(render):
    assert isinstance(render, renderapi.render.Render)

    ex = copy.deepcopy(generate_point_matches_cc.example)
    ex['render'] = render.make_kwargs()

    # create test stack
    tifimport = copy.deepcopy(generate_EM_tilespecs_from_TIFStack.example_input)
    tifimport['render'] = render.make_kwargs()
    tifimport['image_directory'] = example_tif

    tifimp = generate_EM_tilespecs_from_TIFStack.GenerateTifStackTileSpecs(input_data=tifimport)
    tifimp.run()

    ex0 = copy.deepcopy(ex)

    ex['renderScale'] = 'd'
    with pytest.raises(ValidationError):
        mod1 = generate_point_matches_cc.PointMatchCC(input_data=ex)

    ex = copy.deepcopy(ex0)

    # somehow this does not work...
    #
    #
    # ex["matchModelType"] = "This type clearly does not exist!"
    # with pytest.raises(ValidationError):
    #     mod1 =  generate_point_matches_cc.PointMatchCC(input_data=ex)
    #
    # ex = copy.deepcopy(ex0)
    #
    # ex["ccFullScaleSampleSize"] = 1.04923549
    # with pytest.raises(ValidationError):
    #     mod1 =  generate_point_matches_cc.PointMatchCC(input_data=ex)
    #
    # ex = copy.deepcopy(ex0)
    # ...

    tpdir = os.path.join(example_dir, 'tilepairs')
    os.makedirs(tpdir)
    shutil.copy(os.path.join(example_dir, "tile_pairs.json"), tpdir)

    ex0['tile_pair_dir'] = tpdir
    ex0['ccFullScaleSampleSize'] = 20
    ex0['ccFullScaleStepSize'] = 20

    mod = generate_point_matches_cc.PointMatchCC(input_data=ex0)
    mod.run()

    # check if MatchCollection exists

    assert ex0["owner"] in renderapi.pointmatch.get_matchcollection_owners(render=render)

    mc = renderapi.pointmatch.get_matchcollections(ex0["owner"], render=render)

    assert len(mc) == 1
    assert mc[0]['collectionId']['name'] == ex0['collection']

    expected_ids = cc_template['groupIds']

    assert expected_ids == renderapi.pointmatch.get_match_groupIds(ex0['collection'], ex0["owner"], render=render)

    assert cc_template['in_match'] == renderapi.pointmatch.get_matches_within_group(ex0['collection'],
                                                                                    expected_ids[2],
                                                                                    owner=ex0["owner"],
                                                                                    render=render)

    out_match = cc_template['out_match']
    o_m = renderapi.pointmatch.get_matches_outside_group(ex0['collection'],
                                                         expected_ids[2],
                                                         owner=ex0["owner"],
                                                         render=render)

    assert len(o_m) == out_match['len']

    for match in o_m:
        match['matches'] = {}
        match.pop('matchCount')

    assert out_match['match'] in o_m

    # cleanup
    os.system('rm -rf ' + example_tif)
    shutil.rmtree(tpdir)
    renderapi.pointmatch.delete_collection(ex0['collection'], ex0["owner"], render=render)
    renderapi.stack.delete_stack(tifimport['output_stack'], render=render)
