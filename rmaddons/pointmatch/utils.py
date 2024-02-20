import json
import os
import shutil
import numpy as np

def split_tp(infile, maxsplit=100):
    """
    Splits a tilepair JSON file according to the maximum number of entries.

    :param str infile: The original JSON TilePair file
    :param int maxsplit: the maximum number of entries, default: 100
    """

    with open(infile) as f:
        tp_in = json.load(f)

    outdir = os.path.splitext(infile)[0] + '_split'

    if os.path.exists(outdir):
        shutil.rmtree(outdir)

    os.makedirs(outdir)

    pairlist = tp_in["neighborPairs"]
    numpairs = len(pairlist)

    for outidx in range(int(np.ceil(numpairs / maxsplit))):
        outjson = dict()
        for key in tp_in.keys():
            if key != "neighborPairs":
                outjson[key] = tp_in[key]

        outjson["neighborPairs"] = pairlist[outidx * maxsplit: min(((outidx+1) * maxsplit, numpairs))]

        with open(os.path.join(outdir, 'split_' + str(outidx) +'.json'), 'w') as f:
            json.dump(outjson, f, indent=2)


