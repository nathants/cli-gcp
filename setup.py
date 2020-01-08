import setuptools
import sys
import os

setuptools.setup(
    version="0.0.1",
    license='mit',
    name='cli-gcp',
    author='nathan todd-stone',
    author_email='me@nathants.com',
    url='http://github.com/nathants/cli-gcp',
    py_modules=['cli_gcp'],
    python_requires='>=3.6',
    install_requires=['requests >2, <3',
                      'argh >0.26, <0.27',
                      'google-api-python-client >1, <2',
                      'google-auth >1, <2',
                      'PyYAML >3, <6',
                      'google-cloud-logging >1, <2',
                      'google-cloud-storage >1, <2'],
    description='composable, succinct gcp scripts',
)

parent = os.path.dirname(os.path.abspath(__file__))
scripts = [os.path.abspath(os.path.join(service, script))
           for service in os.listdir(parent)
           if service.startswith('gcp')
           and os.path.isdir(service)
           for script in os.listdir(os.path.join(parent, service))
           for path in [os.path.join(service, script)]
           if os.path.isfile(path)]

dst_path = os.path.dirname(os.path.abspath(sys.executable))
for src in scripts:
    name = os.path.basename(src)
    dst = os.path.join(dst_path, name)
    try:
        os.remove(dst)
    except FileNotFoundError:
        pass
    os.symlink(src, dst)
    os.chmod(dst, 0o775)
    print('link:', dst, '=>', src, file=sys.stderr)
