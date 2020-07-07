import setuptools

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f:
    long_description = f.read()

setuptools.setup(
    name='pysicktim',
    version='0.2.0',
    description='TIM5xx Python Library, TCP version',
    license='GNU General Public License v3.0',
    packages=setuptools.find_packages(),
    install_requires=[],
    author='Dennis van Peer',
    author_email='den.vanpeer+pypi@gmail.com',
    keywords=['tim561','tcp','sick','lidar','sicktim','tim5xx','sicktim5xx','sicktim561'],
    url='https://github.com/Denpeer/pysicktim',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
