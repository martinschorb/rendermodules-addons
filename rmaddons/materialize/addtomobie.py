import os.path
import argschema

from rmaddons.materialize.schemas import AddtoMoBIEParameters, AddtoMoBIEOutput
import mobie

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

    def addtomobieproject(self, xmlpath, outpath):
        """
        Add a BDV xml dataset to a MoBIE project folder. Will create all MoBIER project structure if not yet existing.

        :param str xmlpath: path to the BDV XML
        :param str outpath: path to the output MoBIE project directory

        """

        base = os.path.basename(os.path.splitext(xmlpath)[0])
        xmlpath = os.path.abspath(os.path.relpath(xmlpath))

        # resolution = self.args.get("resolution")
        #
        # # get resolution from XML
        # if resolution == [-1, -1, -1]:
        #     resolution = get_resolution(xmlpath, 0)
        #
        # unit = self.args.get("unit")
        #
        # # get unit from XML
        # if unit == '':
        #     unit = get_unit(xmlpath, 0)

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

        ds = mobie.metadata.read_dataset_metadata(os.path.join(outpath, dataset_name))

        if 'timepoints' in ds.keys():
            # add new data to last existing timepoint

            views = ds['views']

            if dataset_name not in views.keys():
                raise ValueError('MoBie project inconsistent, view not found!')

            defview = dict(views['default'])
            __ = defview.pop('uiSelectionGroup')
            defview['sourceDisplays'][0]['imageDisplay'].pop('name')

            newview = dict(views[dataset_name])
            __ = newview.pop('uiSelectionGroup')
            newview['sourceDisplays'][0]['imageDisplay'].pop('name')





            if defview == newview:
                views['default']['sourceDisplays'] = views[dataset_name]['sourceDisplays']



    def __init__(self, schema_type=None, *args, **kwargs):
        super(AddtoMoBIE, self).__init__(
            schema_type=schema_type, *args, **kwargs)

    def run(self):
        self.addtomobieproject(self.args['xmlpath'], self.args['outpath'])
        print('Done adding ' + self.args['xmlpath'] + ' to MoBIE project ' + self.args['outpath'] + '.')


if __name__ == "__main__": # pragma: no cover
    mod = AddtoMoBIE(input_data=example)
    mod.run()
