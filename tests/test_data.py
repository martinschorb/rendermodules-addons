import os
import json
import tempfile

from jinja2 import Environment, FileSystemLoader
import marshmallow

pool_size = os.environ.get('ASAP_POOL_SIZE', 5)

render_host = os.environ.get(
    'RENDER_HOST', 'renderservice')
render_port = os.environ.get(
    'RENDER_PORT', 8080)
render_test_owner = os.environ.get(
    'RENDER_TEST_OWNER', 'test'
)
client_script_location = os.environ.get(
    'RENDER_CLIENT_SCRIPTS',
    ('/shared/render/render-ws-java-client/'
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
#
# scratch_dir = os.environ.get(
#     'SCRATCH_DIR', '/var/www/render/scratch/')
# try:
#     os.makedirs(scratch_dir)
# except OSError as e:
#     pass

log_dir = os.environ.get(
    'LOG_DIR',
    os.path.join(TEST_DATA_ROOT, 'logs'))

try:
    os.makedirs(log_dir)
except OSError as e:
    pass

example_dir = os.path.join(os.path.dirname(__file__), 'test_files')
example_env = Environment(loader=FileSystemLoader(example_dir))


def render_json_template(env, template_file, **kwargs):
    template = env.get_template(template_file)
    d = json.loads(template.render(**kwargs))
    return d
