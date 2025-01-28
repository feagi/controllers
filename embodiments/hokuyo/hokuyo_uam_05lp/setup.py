from setuptools import setup, find_packages
from glob import glob
import os

package_name = 'hokuyo_uam_05lp'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), [
            'src/networking.json',
            'src/capabilities.json',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='bwuk',
    maintainer_email='kevin.a.araujo@gmail.com',
    description='Hokuyo controller package for ROS2',
    license='BSD',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'robot = hokuyo_uam_05lp.robot:main',
        ],
    },
)