try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys
exec(open('imbot/version.py').read())

install_requires=[
            "geomagpy >= 2.0.0",
            "numpy >= 1.21.0",
            "scipy >= 1.7.3",
            "setuptools"
          ]

setup(
    name='imbot',
    version=__version__,
    author='R. Leonhardt',
    author_email='roman.leonhardt@geosphere.at',
    packages=['imbot', 'imbot.analysis', 'imbot.core', 'imbot.lib', 'bash', 'magpy.core'],
    scripts=['imbot/imbot_scan','imbot/imbot_analysis'],
    url='',
    license='LICENSE.txt',
    description='INTERMAGNET automatic data checker',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    package_data={'imbot': ['lib/*.txt'], 'documentation': ['*.pdf'], 'config': ['*.cfg']},
    install_requires=install_requires,
)
