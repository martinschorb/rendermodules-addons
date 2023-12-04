import argschema

from rmaddons.pointmatch.schemas import AMSTParameters, AMSTOutputSchema


example = {
    "render": {
        "host": "localhost",
        "port": 8080,
        "owner": "000tests",
        "project": "tests",
        "client_scripts": (
            "/render/render-ws-java-client/src/main/scripts/")},
    "input_stack": "test_amst",
    "tile_pair_dir": "filepath",
    "z_range": [0, 16]
}


class PointMatchAMST(argschema.ArgSchemaParser):
    default_schema = AMSTParameters
    default_output_schema = AMSTOutputSchema

    def amst_align(self, input_stack, tile_pair_dir, z_range):
        pass

    def run(self):
        self.amst_align(self.args['input_stack'], self.args['tile_pair_dir'], self.args['z_range'])


if __name__ == "__main__":
    mod = PointMatchAMST(input_data=example)
    mod.run()
