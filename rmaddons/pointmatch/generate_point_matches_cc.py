import glob

from rmaddons.pointmatch.schemas import CCParameters
from asap.pointmatch.schemas import PointMatchClientOutputSchema
from asap.module.render_module import RenderModule

from renderapi.render import format_baseurl
from renderapi.client import call_run_ws_client

from rmaddons.utilities import arg2params

example = {
    "render": {
        "host": "render.embl.de",
        "port": 8080,
        "owner": "000tests",
        "project": "test_project",
        "client_scripts": ("/g/emcf/software/render/render-ws-java-client/src/main/scripts/")
    },
    "tile_pair_dir": "/g/emcf/schorb/code/rendermodules-addons/tests/test_files/tilepairs",
    "renderScale": 0.5,
    "matchModelType": "TRANSLATION",
    "owner": "TestCollectionOwner",
    "collection": "TestCollection",
    "ccFullScaleSampleSize": 200,
    "ccFullScaleStepSize": 200,
    "ccMinResultThreshold": 0.6
}


class PointMatchCC(RenderModule):
    default_schema = CCParameters
    default_output_schema = PointMatchClientOutputSchema

    def call_cc_client(self, tp_jsonfile):
        """
        Calls the CrossCorrelation PointMatch client to calculate matches.

        :param str tp_jsonfile: path to the JSON file listing the tile pairs.
        """
        baseDataUrl = format_baseurl(self.args['render']['host'],
                                     self.args['render']['port'])

        if not baseDataUrl.startswith('http'):
            baseDataUrl = 'http://' + baseDataUrl

        className = 'org.janelia.render.client.CrossCorrelationPointMatchClient'

        argvs = []
        argvs += ['--baseDataUrl', baseDataUrl]

        for key, val in self.args.items():
            if key not in ["render", "log_level", "tile_pair_dir"]:
                argvs += arg2params(self.args, key)

        argvs += ["--pairJson", tp_jsonfile]

        call_run_ws_client(className, add_args=argvs, renderclient=self.render)

    def run(self):

        tp_json = glob.glob(self.args['tile_pair_dir'] + '/*.json')

        for tp_jsonfile in tp_json:
            self.call_cc_client(tp_jsonfile)


if __name__ == "__main__":
    mod = PointMatchCC(input_data=example)
    mod.run()
