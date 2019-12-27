import warnings
import shell
import datetime
import contextlib
import traceback
import logging
import sys
import util.iter
import util.log
from util.colors import red, green, cyan # noqa

ssh_args = ' -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '

def now():
    return str(datetime.datetime.utcnow().isoformat()) + 'Z'

@contextlib.contextmanager
def setup():
    warnings.filterwarnings("ignore", "Your application has authenticated using end user credentials")
    logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
    logging.getLogger('googleapiclient.discovery').setLevel(logging.ERROR)
    util.log.setup(format='%(message)s')
    if util.hacks.override('--stream'):
        shell.set_stream().__enter__()
    try:
        yield
    except AssertionError as e:
        logging.info(red('error: %s' % (e.args[0] if e.args else traceback.format_exc().splitlines()[-2].strip())))
        sys.exit(1)
    except:
        raise
