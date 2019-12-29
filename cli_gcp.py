import schema
import warnings
import shell
import datetime
import contextlib
import traceback
import logging
import sys
import util.iter
import util.log
import googleapiclient.discovery
from util import cached
from util.colors import red, green, cyan # noqa

ssh_args = ' -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '

@cached.func
def compute():
    return googleapiclient.discovery.build('compute', 'v1')

def format(compute_instance):
    tags = ','.join(compute_instance.get('tags', {}).get('items', []))
    if tags:
        tags = f'tags={tags}'
    return ' '.join([
        (green if compute_instance['status'].lower() == 'running' else
         cyan if compute_instance['status'].lower() in ['provisioning', 'staging'] else
         red)(compute_instance['name']),
        compute_instance['zone'].split('/')[-1],
        compute_instance['machineType'].split('/')[-1],
        compute_instance['status'].lower(),
        compute_instance['id'],
        ('preemptible' if compute_instance['scheduling']['preemptible'] else 'ondemand'),
        ','.join(f'{k}={v}' for k, v in sorted(compute_instance.get('labels', {}).items(), key=lambda x: x[0])) or '-',
        tags or '-',
    ])

@schema.check(yields=dict)
def ls(project: str, zone: str, selectors: [str], state: str):
    assert state in ['all', 'running', 'provisioning', 'staging', 'repairing' 'stopping', 'terminated', None], f'bad state: {state}'
    filter = []
    if state != 'all':
        filter += [f'(status = {state.upper()})']
    tags = []
    if selectors:
        if selectors[0].isdigit(): # instance id
            fs = []
            for s in selectors:
                fs += [f'(id = {s})']
            fs = '(' + ' OR '.join(fs) + ')'
            filter += [fs]
        elif ':' not in selectors[0] and '=' not in selectors[0]: # instance name
            fs = []
            for s in selectors:
                fs += [f'(name = {s})']
            fs = '(' + ' OR '.join(fs) + ')'
            filter += [fs]
        elif '=' in selectors[0]: # label
            fs = []
            for s in selectors:
                k, v = s.split('=')
                fs += [f'(labels.{k} = {v})']
            fs = ' AND '.join(fs)
            filter += [fs]
        elif ':' in selectors[0]: # tag
            fs = []
            for s in selectors:
                k, v = s.split(':')
                tags += [v]
        else:
            logging.info(f'unkown selector type: {selectors[0]}')
            sys.exit(1)
    filter = ' AND '.join(filter)
    req = compute().instances().list(project=project, zone=zone, filter=filter)
    while req:
        resp = req.execute()
        for item in resp.get('items', []):
            instance_tags = item.get('tags', {}).get('items', [])
            if not tags or all(tag in instance_tags for tag in tags):
                yield item
        req = compute().instances().list_next(req, resp)

def now():
    return str(datetime.datetime.utcnow().isoformat()) + 'Z'

@contextlib.contextmanager
def setup():
    warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
    util.log.setup(format='%(message)s')
    with shell.set_echo():
        if util.hacks.override('--stream'):
            shell.set_stream().__enter__()
        try:
            yield
        except AssertionError as e:
            logging.info(red('error: %s' % (e.args[0] if e.args else traceback.format_exc().splitlines()[-2].strip())))
            sys.exit(1)
        except:
            raise
