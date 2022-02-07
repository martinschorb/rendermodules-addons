import os
import json
import tempfile

from jinja2 import Environment, FileSystemLoader
import marshmallow

pool_size = os.environ.get('TEST_POOL_SIZE', 5)

render_host = os.environ.get(
    'RENDER_HOST', 'localhost')
render_port = os.environ.get(
    'RENDER_PORT', 8080)
render_test_owner = os.environ.get(
    'RENDER_TEST_OWNER', 'test'
)
render_dir = os.environ.get('RENDER_DIR',('../render'))

client_script_location = os.environ.get(
    'RENDER_CLIENT_SCRIPTS',
    (render_dir+'/render-ws-java-client/'
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

example_dir = os.path.join(os.path.dirname(__file__), 'test_files')
example_env = Environment(loader=FileSystemLoader(example_dir))

example_n5z =  os.path.join(example_dir,'testn5.tgz')
example_n5 = os.path.join(example_dir,'rmaddons_test.n5')

if not os.path.exists(example_n5):
    try:
        os.system('tar xvfz ' + example_n5z + ' -C ' + example_dir)
    except OSError as e:
        pass


def render_json_template(env, template_file, **kwargs):
    template = env.get_template(template_file)
    d = json.loads(template.render(**kwargs))
    return d


makexml_template = render_json_template(
        example_env,
        'materialize_makexml.json')

