#! /usr/bin/env python3

import os
import sys
import platform
import shutil

import paver
from paver.easy import task, options, Bunch, needs, cmdopts
from paver.virtual import virtualenv
from subprocess import Popen


VERSION = ''
exec(open('version.py', 'r').read())

options(
    virtualenv=Bunch(
        script_name='bootstrap.py',
        dest_dir='build_venv',
        packages_to_install=['fludo', 'PyInstaller']
    ),
    setup=Bunch(
        name="Eliq",
        packages=['eliq'],
        version=VERSION,
        author='Zsolt Nagy',
        author_email='nazsolti@outlook.com'
    )
)


@task
@virtualenv('build_venv')
def check_venv():
    for package in options.virtualenv.packages_to_install:
        __import__(package)


@task
@virtualenv('build_venv')
def install_packages_in_venv():
    for package in options.virtualenv.packages_to_install:
        Popen('pip install {}'.format(package)).wait()


@task
def create_venv():
    try:
        check_venv()
    except FileNotFoundError:
        print('Venv not found, creating...')
        paver.virtual.bootstrap()
        Popen(sys.executable + ' ' + options.virtualenv.script_name).wait()
        os.remove(options.virtualenv.script_name)
        check_venv()
    except ModuleNotFoundError:
        print('Some modules not found, installing...')
        install_packages_in_venv()
        check_venv()


@task
@virtualenv('build_venv')
@needs('create_venv')
def build_pyinstaller():
    if platform.system() == 'Windows':
        Popen(('pyinstaller --noconfirm --noconsole --clean --icon "res/icons/application.ico"'
               ' --add-data "res";"res" "eliq.pyw"')).wait()
    else:
        Popen('pyinstaller --noconfirm --clean --add-data "res":"res" "eliq.pyw"').wait()

    # Capitalize the executable
    if platform.system() == 'Windows':
        os.rename(os.path.join('dist', 'eliq', 'eliq.exe'),
            os.path.join('dist', 'eliq', 'Eliq.exe'))
    # TODO: Capitalize executables for other platforms

    os.rename(os.path.join('dist', 'eliq'),
        os.path.join('dist', '{} {}'.format(options.setup.name, options.setup.version)))


@task
@needs('create_venv')
def build():
    if os.path.exists(os.path.join('dist',
            '{} {}'.format(options.setup.name, options.setup.version))):
        print('Existing build directory found in dist. Rebuild? (y/n/c) ')
        answer = input()
        if answer in ['y', 'Y']:
            shutil.rmtree(os.path.join('dist',
                '{} {}'.format(options.setup.name, options.setup.version)))
            build()
        elif answer in ['c', 'C']:
            print('Cancel.')
            return
    else:
        build_pyinstaller()


@task
@cmdopts([
    ('clean', 'c', 'Clean all build directories, leaving only the archive in dist.')
])
def build_archive():
    
    build()

    if platform.system() == 'Windows':
        build_dir = os.path.join('dist',
            '{} {}'.format(options.setup.name, options.setup.version))
        try:
            os.remove(build_dir + '.zip')
        except FileNotFoundError:
            # Did not exist
            pass
        shutil.make_archive(build_dir, 'zip', build_dir)
    # TODO: Create tar.gz for other platforms

    if hasattr(options.build_archive, 'clean'):
        clean()


@task
@cmdopts([
    ('new_version=', 'u', 'Update version number')
])
def version(options):
    if hasattr(options.version, 'new_version'):
        with open('version.py', 'w') as f:
            f.write('VERSION = \'{}\'\n'.format(options.version.new_version))
        print('Version updated to: {}'.format(options.version.new_version))
    else:
        print('Version is: {}'.format(VERSION))


@task
@cmdopts([
    ('all', 'a', 'Also remove \'dist\' directory along with built archives.')
])
def clean():
    try:
        shutil.rmtree('build')
        print('Removed \'build\'')
    except FileNotFoundError:
        print('Skipping \'build\' (not found)')

    try:
        shutil.rmtree('build_venv')
        print('Removed \'build_venv\'')
    except FileNotFoundError:
        print('Skipping \'build_venv\' (not found)')

    dist_dir = os.path.join('dist',
        '{} {}'.format(options.setup.name, options.setup.version))
    try:
        shutil.rmtree(dist_dir)
        print('Removed \'{}\''.format(dist_dir))
    except FileNotFoundError:
        print('Skipping \'{}\' (not found)'.format(dist_dir))

    try:
        os.remove('eliq.spec')
        print('Removed \'eliq.spec\'')
    except FileNotFoundError:
        print('Skipping \'eliq.spec\' (not found)')

    if hasattr(options.clean, 'all'):
        try:
            shutil.rmtree('dist')
            print('Removed \'dist\'')
        except FileNotFoundError:
            print('Skipping \'dist\' (not found)')

# TODO: Create builder for PyPi
