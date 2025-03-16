try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys
import shutil
exec(open('imbot/version.py').read())
shutil.copyfile('imbot/imbot_init.py','scripts/imbot_init')
shutil.copyfile('imbot/imbot_scan.py','scripts/imbot_scan')
shutil.copyfile('imbot/imbot_analysis.py','scripts/imbot_analysis')
shutil.copyfile('imbot/imbot_convert.py','scripts/imbot_convert')

install_requires=[
            "geomagpy > 1.1.9",
            "numpy >= 1.21.0",
            "scipy >= 1.7.3",
            "setuptools"
          ]

setup(
    name='imbot',
    version=__version__,
    author='R. Leonhardt',
    author_email='roman.leonhardt@geosphere.at',
    packages=['imbot', 'imbot.analysis', 'imbot.core', 'imbot.documentation', 'imbot.bash', 'imbot.config', 'imbot.templates'],
    scripts=['scripts/imbot_scan','scripts/imbot_analysis', 'scripts/imbot_init', 'scripts/imbot_convert'],
    url='',
    license='LICENSE.txt',
    description='INTERMAGNET automatic data checker',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    package_data={'imbot': ['documentation/*.pdf', 'bash/*.sh', 'bash/*.bash', 'config/*.cfg', 'templates/*']  },
    install_requires=install_requires,
)
