# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES


setup (
    name='kvm',
    version='1.0.4',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    packages=['kvm'],
    package_dir={'kvm': 'kvm'},
    package_data={'kvm': ['kvm.json']},
    license='MIT License',
    description='An API for managing KVM host.',
    long_description=open('README.rst').read(),
    install_requires=[
        'unix',
        'lxml'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Operating System :: Unix',
        'Topic :: System :: Systems Administration']
)
