import schema
import yaml
import logging
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
from util.retry import retry
from util.colors import red, green, cyan # noqa

ssh_args = ' -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '

def ip(instance):
    assert len(instance['networkInterfaces']) == 1, yaml.dump(instance)
    assert len(instance['networkInterfaces'][0]['accessConfigs']) == 1, yaml.dump(instance)
    return instance['networkInterfaces'][0]['accessConfigs'][0]['natIP']


def ip_private(instance):
    assert len(instance['networkInterfaces']) == 1, yaml.dump(instance)
    return instance['networkInterfaces'][0]['networkIP']

@cached.func
def compute():
    return googleapiclient.discovery.build('compute', 'v1')

def url(obj):
    return obj.get('targetLink') or obj['selfLink'] # target if insert(), self if get()

def format_header():
    return ' '.join([
        'name',
        'type',
        'status',
        'id',
        'kind',
        'labels',
        'tags',
        'zone',
    ])

def format(compute_instance):
    tags = ','.join(compute_instance.get('tags', {}).get('items', []))
    if tags:
        tags = f'tags={tags}'
    return ' '.join([
        (green if compute_instance['status'].lower() == 'running' else
         cyan if compute_instance['status'].lower() in ['provisioning', 'staging'] else
         red)(compute_instance['labels'].get('name', f'missing name label: {compute_instance["name"]}')),
        compute_instance['machineType'].split('/')[-1],
        compute_instance['status'].lower(),
        compute_instance['id'],
        ('preemptible' if compute_instance['scheduling']['preemptible'] else 'ondemand'),
        ','.join(f'{k}={v}' for k, v in sorted(compute_instance.get('labels', {}).items(), key=lambda x: x[0]) if k not in {'name', 'local-user'}) or '-',
        tags or '-',
        compute_instance['zone'].split('/')[-1],
    ])

@schema.check(yields=dict)
def ls(project: str, zone: str, selectors: [str], state: str):
    assert state in ['all', 'running', 'provisioning', 'staging', 'repairing' 'stopping', 'terminated', None], f'bad state: {state}'
    filter = []
    if state != 'all':
        filter += [f'(status = {state.upper()})']
    tags = []
    ip_privs = []
    ips = []
    if selectors:
        if selectors[0].isdigit(): # instance id
            fs = []
            for s in selectors:
                fs += [f'(id = {s})']
            fs = '(' + ' OR '.join(fs) + ')'
            filter += [fs]
        elif selectors[0].startswith('10.'): # ip priv
            for s in selectors:
                ip_privs.append(s)
        elif selectors[0].count('.') == 3: # ip
            for s in selectors:
                ips.append(s)
        elif ':' not in selectors[0] and '=' not in selectors[0]: # instance name
            fs = []
            for s in selectors:
                fs += [f'(labels.name = {s})']
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
            if ((not tags or all(tag in instance_tags for tag in tags))
                or (not ip_privs or item['networkInterfaces'][0]['networkIP'] in ip_privs)
                or (not ips or item['networkInterfaces'][0]['accessConfigs'][0]['natIP'] in ips)):
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

def _ensure(name, get, insert, config, schemafy=lambda x: x, resafy=lambda x: x):
    try:
        res = get()
    except googleapiclient.errors.HttpError as e:
        if e.resp.status != 404:
            raise
        res = insert()
        logging.info(f'{name} created: {config["name"]}')
    else:
        logging.info(f'{name} exists: {config["name"]}')
        config = schemafy(config)
        _res = resafy(res)
        for k, v in config.items():
            schema.validate({(name, k): v}, {(name, k): _res.get(k)})
            logging.info(f'{name} is valid for: {k}={v}')
    logging.info(yaml.dump(res))
    return res

class ensure:
    def firewall_allow(project, rule_name, source_ranges, network_tags, port=None, proto='tcp', direction='ingress', priority=1000):
        assert direction in {'ingress', 'egress'}
        config = {"direction": direction.upper(),
                  'priority': priority,
                  "sourceRanges": source_ranges,
                  "allowed": [{"IPProtocol": proto,
                               "ports": [str(port)] if port else []}],
                  "targetTags": network_tags,
                  "name": rule_name}
        get = compute().firewalls().get(project=project, firewall=config['name']).execute
        insert = compute().firewalls().insert(project=project, body=config).execute
        def schemafy(config):
            config['sourceRanges'] = tuple(config['sourceRanges'])
            config['allowed'] = tuple(config['allowed'])
            config['targetTags'] = config['targetTags'] or None
            config['allowed'][0]['ports'] = config['allowed'][0].get('ports') or (':optional', list, [])
            return config
        return _ensure('firewall allow', get, insert, config, schemafy)

    def firewall_deny(project, rule_name, source_ranges, network_tags, port=None, proto='tcp', direction='ingress', priority=1000):
        assert direction in {'ingress', 'egress'}
        config = {"direction": direction.upper(),
                  'priority': priority,
                  "sourceRanges": source_ranges,
                  "denied": [{"IPProtocol": proto,
                              "ports": [str(port)] if port else []}],
                  "targetTags": network_tags,
                  "name": rule_name}
        get = compute().firewalls().get(project=project, firewall=config['name']).execute
        insert = compute().firewalls().insert(project=project, body=config).execute
        def schemafy(config):
            config['sourceRanges'] = tuple(config['sourceRanges'])
            config['denied'] = tuple(config['denied'])
            return config
        return _ensure('firewall denied', get, insert, config, schemafy)

    def ssl_cert(project, ssl_cert_name, ip_address):
        get = compute().sslCertificates().get(project=project, sslCertificate=ssl_cert_name).execute
        schemafy = lambda _: {}
        with shell.tempdir():
            shell.run(f'openssl req -x509 -nodes -newkey rsa:2048 -keyout ssl.key -out ssl.crt -days 9999 -subj "/CN={ip_address}/O=Fake Name/C=US"')
            with open('ssl.crt') as f:
                crt = f.read()
            with open('ssl.key') as f:
                key = f.read()
            config = {'name': ssl_cert_name,
                      'certificate': crt,
                      'privateKey': key}
            insert = compute().sslCertificates().insert(project=project, body=config).execute
            return _ensure('ssl cert', get, insert, config, schemafy)

    def global_forwarding_rules(project, forwarding_rules_name, proxy_name, ip_address_url, port):
        config = {'name': forwarding_rules_name,
                  'loadBalancingScheme': 'EXTERNAL',
                  'portRange': port,
                  'target': proxy_name,
                  'IPProtocol': 'TCP',
                  'IPAddress': ip_address_url}
        get = compute().globalForwardingRules().get(project=project, forwardingRule=config['name']).execute
        insert = compute().globalForwardingRules().insert(project=project, body=config).execute
        insert = retry(insert, exponent=1.2, allowed_exception_fn=lambda e: e.resp.status == 404)
        return _ensure('global forwarding rules', get, insert, config)

    def global_ip_address(project, ip_address_name):
        config = {'name': ip_address_name,
                  'ipVersion': 'IPV4'}
        get = compute().globalAddresses().get(project=project, address=config['name']).execute
        def insert():
            compute().globalAddresses().insert(project=project, body=config).execute()
            def fetch():
                res = compute().globalAddresses().get(project=project, address=config['name']).execute()
                assert 'address' in res
                return res
            return retry(fetch, times=20, exponent=1.5)()
        return _ensure('global ip address', get, insert, config)

    def https_proxy(project, https_proxy_name, url_map_url, ssl_cert_url):
        config = {'name': https_proxy_name,
                  'sslCertificates': [ssl_cert_url],
                  'urlMap': url_map_url}
        get = compute().targetHttpsProxies().get(project=project, targetHttpsProxy=config['name']).execute
        insert = compute().targetHttpsProxies().insert(project=project, body=config).execute
        insert = retry(insert, exponent=1.2, allowed_exception_fn=lambda e: e.resp.status == 404) # can't be updated before upstream components actually exists
        return _ensure('https proxy', get, insert, config)

    def http_proxy(project, http_proxy_name, url_map_url):
        config = {'name': http_proxy_name,
                  'urlMap': url_map_url}
        get = compute().targetHttpProxies().get(project=project, targetHttpProxy=config['name']).execute
        insert = compute().targetHttpProxies().insert(project=project, body=config).execute
        return _ensure('http proxy', get, insert, config)

    def url_map(project, url_map_name, backend_service_name):
        config = {'name': url_map_name,
                  'defaultService': backend_service_name}
        get = compute().urlMaps().get(project=project, urlMap=config['name']).execute
        insert = compute().urlMaps().insert(project=project, body=config).execute
        insert = retry(insert, exponent=1.2, allowed_exception_fn=lambda e: e.resp.status == 404) # can't be updated before upstream components actually exists
        return _ensure('url map', get, insert, config)

    def backend_has_instance_group(project, zone, backend_service_name, instance_group_manager_name, balancing_mode, health_check_url):
        instance_group_manager = compute().instanceGroupManagers().get(project=project, zone=zone, instanceGroupManager=instance_group_manager_name).execute()
        instance_group_url = instance_group_manager['instanceGroup']
        backend_service = compute().backendServices().get(project=project, backendService=backend_service_name).execute()
        backend_config = {"group": instance_group_url,
                          "balancingMode": balancing_mode}
        backends = backend_service.get('backends', [])
        for backend in backends:
            if backend['group'] == instance_group_url:
                for k, v in backend_config.items():
                    schema.validate({k: v}, {k: backend.get(k)})
                    logging.info(f'backend config is valid for: {k}={v}')
                return backend_service
        else:
            backend_service['backends'] = backend_service.get('backends', []) + [backend_config]
            logging.info(yaml.dump({'backendService': backend_service}))
            update = compute().backendServices().update(project=project, backendService=backend_service_name, body=backend_service).execute
            res = retry(update, exponent=1.2, allowed_exception_fn=lambda e: e.resp.status == 404)() # can't be updated before upstream components actually exists
            logging.info(yaml.dump({'backendService': res}))
            return update

    def instance_template(project, instance_template_name, instance_config):
        config = {'name': instance_template_name,
                  "properties": instance_config}
        get = compute().instanceTemplates().get(project=project, instanceTemplate=config['name']).execute
        insert = compute().instanceTemplates().insert(project=project, body=config).execute
        def schemafy(config):
            config = config['properties']
            config['machineType'] = config['machineType'].split('/')[-1]
            config['tags']['fingerprint'] = (':optional', str, '')
            config['tags']['items'] = config['tags']['items'] or (':optional', list, [])
            config['disks'] = tuple(config['disks'])
            del config['name']
            for net in config['networkInterfaces']:
                val = net['network']
                def f(x):
                    return x.endswith(val)
                net['network'] = f
            return config
        def resafy(res):
            res = res['properties']
            return res
        return _ensure('instance template', get, insert, config, schemafy, resafy)

    def health_check(project, health_check_name, health_check_http_path, port):
        config = {"name": health_check_name,
                  'type': 'HTTP',
                  "httpHealthCheck": {"requestPath": health_check_http_path,
                                      'port': port}}
        get = compute().healthChecks().get(project=project, healthCheck=config['name']).execute
        insert = compute().healthChecks().insert(project=project, body=config).execute
        return _ensure('health check', get, insert, config)

    def backend_service(project, timeout, health_check_url, port_name, backend_service_name):
        config = {"connectionDraining": {"drainingTimeoutSec": timeout},
                  "protocol": "HTTP",
                  "loadBalancingScheme": "EXTERNAL",
                  "healthChecks": [health_check_url],
                  "portName": port_name,
                  "name": backend_service_name,
                  "timeoutSec": timeout}
        get = compute().backendServices().get(project=project, backendService=config['name']).execute
        insert = compute().backendServices().insert(project=project, body=config).execute
        return _ensure('backend service', get, insert, config)

    def managed_instance_group(project, zone, instance_name, health_check_url, target_size, target_size_max, instance_template_url, port_name, port, instance_group_manager_name):
        config = {"autoHealingPolicies": [{"healthCheck": health_check_url,
                                           "initialDelaySec": 60}],
                  "targetSize": target_size,
                  "baseInstanceName": instance_name,
                  "updatePolicy": {"type": "PROACTIVE",
                                   "maxSurge": {"fixed": target_size_max},
                                   "minimalAction": "REPLACE",
                                   "maxUnavailable": {"percent": 50}},
                  "instanceTemplate": instance_template_url,
                  "namedPorts": [{"name": port_name, "port": port}],
                  "name": instance_group_manager_name}
        get = compute().instanceGroupManagers().get(project=project, zone=zone, instanceGroupManager=config['name']).execute
        insert = compute().instanceGroupManagers().insert(project=project, zone=zone, body=config).execute
        return _ensure('managed instance group', get, insert, config)

    def autoscaler(project, zone, autoscaler_name, instance_group_manager_url, target_size, target_size_max):
        config = {"autoscalingPolicy": {"maxNumReplicas": target_size_max,
                                        "coolDownPeriodSec": 30,
                                        "cpuUtilization": {"utilizationTarget": 0.5},
                                        "minNumReplicas": target_size},
                  "target": instance_group_manager_url,
                  "name": autoscaler_name}
        get = compute().autoscalers().get(project=project, zone=zone, autoscaler=config['name']).execute
        insert = compute().autoscalers().insert(project=project, zone=zone, body=config).execute
        return _ensure('autoscaler', get, insert, config)
