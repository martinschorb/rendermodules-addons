import os.path
import argschema
import json
from rendermodules_addons.materialize.schemas import MakeXMLParameters, MakeXMLOutput
from pybdv.metadata import write_xml_metadata, write_h5_metadata, write_n5_metadata, validate_attributes
from pybdv.util import absolute_to_relative_scale_factors
# import sys



example = {
    "path": "-",
    "scale_factors": [[1,1,1]],
    "resolution": [0.05, 0.015, 0.015],
    "unit": 'micrometer'
}



def get_n5scales(path):
    with open(os.path.join(path,'setup0','timepoint0','attributes.json')) as f:
        t0_attribs = json.load(f)

    # first need to reverse the axis order of the scale factors due to XYZ convention in java vs. ZYX convention in python
    scale_factors = [sf[::-1] for sf in t0_attribs["scales"]]
    # then need to translate from absolute to relative scale factors, which are expected by pybdv
    rel_scales = absolute_to_relative_scale_factors(scale_factors)

    return rel_scales


class MakeXML(argschema.ArgSchemaParser):
    default_schema = MakeXMLParameters
    default_output_schema = MakeXMLOutput


    @classmethod
    def make_render_xml(self,path, scale_factors , resolution, unit):
        
        if path.endswith('n5'):
            xml_path = path.replace('.n5', '.xml')
            is_h5=False
        elif path.endswith('h5'):
            xml_path = path.replace('.h5', '.xml')
            is_h5=True
        else:
            raise TypeError('Only h5 and n5 are currently supported.')
    
        attrs = {'channel': {'id': None}}
        attrs = validate_attributes(xml_path, attrs, setup_id=0,
                                    enforce_consistency=False)
        if scale_factors == [[1,1,1]]:
            scale_factors = get_n5scales(path)
        
        write_xml_metadata(xml_path, path, unit, resolution,
                           is_h5=is_h5,
                           setup_id=0, timepoint=0,
                           setup_name=None,
                           affine=None,
                           attributes=attrs,
                           overwrite=False,
                           overwrite_data=False,
                           enforce_consistency=False)
        
        if is_h5:
            write_h5_metadata(path, scale_factors, resolution, setup_id=0, timepoint=0, overwrite=True)
        else:
            write_n5_metadata(path, scale_factors, resolution, setup_id=0, timepoint=0, overwrite=True)
            
            
            

    def run(self):        
        self.make_render_xml(self.args['path'], self.args['scale_factors'] , self.args['resolution'], self.args['unit'])
        
        
        
if __name__ == "__main__":
    mod = MakeXML(input_data=example)
    mod.run()
 