import setuptools
import os

parent = os.path.dirname(os.path.abspath(__file__))

setuptools.setup(
    version="0.0.1",
    license='mit',
    name='cli-gcp',
    author='nathan todd-stone',
    author_email='me@nathants.com',
    url='http://github.com/nathants/cli-gcp',
    py_modules=['cli_gcp'],
    python_requires='>=3.7',
    install_requires=['requests >2, <3',
                      'argh >0.26, <0.27'],
    scripts = [os.path.join(service, script)
               for service in os.listdir(parent)
               if service.startswith('gcp')
               and os.path.isdir(service)
               for script in os.listdir(os.path.join(parent, service))
               for path in [os.path.join(service, script)]
               if os.path.isfile(path)],
    description='composable, succinct gcp scripts',
)
