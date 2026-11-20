from setuptools import setup
import os
from glob import glob

package_name = 'goto_point'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Camille-123-z',
    maintainer_email='zhang_hong_yi2025@qq.com',
    description='Simple go-to-point controller using LiDAR SLAM localization (no Nav2)',
    license='MIT',
    entry_points={
        'console_scripts': [
            'goto_point_node = goto_point.goto_point_node:main',
        ],
    },
)
