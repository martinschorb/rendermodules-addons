import os
import json
# import renderapi
# import pytest

from jinja2 import Environment, FileSystemLoader

pool_size = os.environ.get('TEST_POOL_SIZE', 5)

render_host = os.environ.get(
    'RENDER_HOST', 'localhost')
render_port = os.environ.get(
    'RENDER_PORT', 8080)
render_test_owner = os.environ.get(
    'RENDER_TEST_OWNER', '000tests'
)
render_dir = os.environ.get('RENDER_DIR', os.path.abspath('../../render'))

client_script_location = os.environ.get(
    'RENDER_CLIENT_SCRIPTS',
    (render_dir + '/render-ws-java-client/'
                  'src/main/scripts/'))

# asap test compares with integer
try:
    render_port = int(render_port)
except ValueError:
    pass

render_params = {
    "host": render_host,
    "port": render_port,
    "owner": render_test_owner,
    "project": "test_project",
    "client_scripts": client_script_location
}

log_dir = os.environ.get(
    'LOG_DIR',
    (os.path.join(os.path.dirname(__file__), '../test_logs')))

try:
    os.makedirs(log_dir)
except OSError as e:
    pass

# example data setup

example_dir = os.path.join(os.path.dirname(__file__), 'test_files')
example_env = Environment(loader=FileSystemLoader(example_dir))

tempdir = example_dir
# example N5 output data

example_n5z = os.path.join(example_dir, 'testn5.tgz')
example_n5 = os.path.abspath(os.path.join(tempdir, 'rmaddons_test.n5'))

if not os.path.exists(example_n5):
    try:
        os.system('tar xvfz ' + example_n5z + ' -C ' + tempdir)
    except OSError as e:
        pass

# example SBEMImage input data

example_sbemz = os.path.join(example_dir, 'testsbemimage.tgz')
example_sbem = os.path.abspath(os.path.join(tempdir, 'sbemimage_testdata'))

if not os.path.exists(example_sbem):
    try:
        os.system('tar xvfz ' + example_sbemz + ' -C ' + example_dir)
    except OSError as e:
        pass

# example SerialEMmontage input data

example_serialemz = os.path.join(example_dir, 'testidoc.tgz')
example_serialem = os.path.abspath(os.path.join(tempdir, 'idoc_supermont_testdata'))

if not os.path.exists(example_serialem):
    try:
        os.system('tar xvfz ' + example_serialemz + ' -C ' + example_dir)
    except OSError as e:
        pass

# example TIFF Stack input data

example_tifz = os.path.join(example_dir, 'testtiff.tgz')
example_tif = os.path.abspath(os.path.join(tempdir, 'tif_testdata'))

if not os.path.exists(example_tif):
    try:
        os.system('tar xvfz ' + example_tifz + ' -C ' + example_dir)
    except OSError as e:
        pass


# load template json files

def render_json_template(env, template_file, **kwargs):
    template = env.get_template(template_file)
    d = json.loads(template.render(**kwargs))
    return d


# define test templates

makexml_template = render_json_template(
    example_env,
    'materialize_makexml.json')

sbemimage_template = render_json_template(
    example_env,
    'dataimport_generate_EM_tilespecs_from_SBEMImage.json')

serialem_template = render_json_template(
    example_env,
    'dataimport_generate_EM_tilespecs_from_SerialEMmontage.json')

mobie_template = render_json_template(
    example_env,
    'materialize_addtomobie.json')

sliceexport_template = render_json_template(
    example_env,
    'materialize_render_export_sections.json')

tif_template = render_json_template(
    example_env,
    'dataimport_generate_EM_tilespecs_from_TIFStack.json')

cc_template = render_json_template(
    example_env,
    'pointmatch_generate_point_matches_cc.json')
