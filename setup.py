# -*- coding: utf-8 -*-
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup (
    name='kvm',
    version='0.1',
    author='François Ménabé',
    author_email='francois.menabe@gmail.com',
    py_modules=['kvm'],
    data_files=[('', ['kvm.json'])],
    license='MIT License',
    description='An API for managing KVM host.',
    long_description=open('README.rst').read(),
    install_requires=[
        'unix',
        'lxml'
    ],
)
