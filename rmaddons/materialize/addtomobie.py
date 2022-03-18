import os.path
import argschema
import xml.etree.ElementTree as ET

from rmaddons.materialize.schemas import AddtoMoBIEParameters, AddtoMoBIEOutput
import mobie

import mobie.metadata as mom
from pybdv.metadata import get_resolution, get_unit

example = {
    "xmlpath": "tests/test_files/rmaddons_test.xml",
    "outpath": "tests/test_files/mobie",
    "resolution": [-1, -1, -1],
    "unit": ''
}


class AddtoMoBIE(argschema.ArgSchemaParser):
    default_schema = AddtoMoBIEParameters
    default_output_schema = AddtoMoBIEOutput

    def addtomobieproject(self,xmlpath,outpath):
        """
        Add a BDV xml dataset to a MoBIE project folder. Will create all MoBIER project structure if not yet existing.

        :param str xmlpath: path to the BDV XML
        :param str outpath: path to the output MoBIE project directory

        """
        os.system('sleep 23')

        base = os.path.basename(os.path.splitext(xmlpath)[0])

        resolution = self.args.get("resolution")

        # get resolution from XML
        if resolution == [-1,-1,-1]:
            resolution = get_resolution(xmlpath,0)

        unit = self.args.get("unit")

        # get unit from XML
        if unit == '':
            unit = get_unit(xmlpath, 0)

        dataset_name = self.args.get("dataset_name")

        if dataset_name == '':
            dataset_name = base

        image_name = self.args.get("image_name")

        if image_name == '':
            image_name = base

        menu_name = self.args.get("menu_name")

        if menu_name == '':
            menu_name = None


        mobie.add_bdv_image(xmlpath,
                            outpath,
                            dataset_name=dataset_name,
                            image_name=image_name,
                            menu_name=menu_name,
                            move_data=True)

    def __init__(self, schema_type=None, *args, **kwargs):
        super(AddtoMoBIE, self).__init__(
            schema_type=schema_type, *args, **kwargs)

    def run(self):

        self.addtomobieproject(self.args['xmlpath'],self.args['outpath'])
        
        
        
if __name__ == "__main__":
    mod = AddtoMoBIE(input_data=example)
    mod.run()
 