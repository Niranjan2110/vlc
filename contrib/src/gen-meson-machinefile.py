#!/usr/bin/env python3
import os
import argparse
import shlex

class BinaryAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, value, option_string=None):
        split = value.split(':')
        if (len(split) < 2 or split[0] == '' or split[1] == ''):
            raise ValueError("Syntax: --binary foo:/usr/bin/foo")
        name = split[0]
        if (getattr(namespace, 'binary') is None):
            setattr(namespace, 'binary', {})
        namespace.binary[name] = ':'.join(split[1:])

# Argument parsing
parser = argparse.ArgumentParser(
    description="Generate a meson crossfile based on environment variables")
parser.add_argument('--type',
    choices=['internal', 'external-cross', 'external-native'],
    default='internal',
    help="""
internal:   Internal crossfile used when contribs are cross-compiled.
            Not meant for use outside the contribs build.
external-*: External machine file (either cross or native).
            This is meant to be used by VLCs meson build system to easily
            use the given contribs, similar to --with-contrib=DIR for ./configure
""")
parser.add_argument('--binary', action=BinaryAction, nargs='*')
parser.add_argument('file', type=argparse.FileType('w', encoding='UTF-8'),
    help="output file")
args = parser.parse_args()

# Helper to add env variable value to crossfile
def _add_environ_val(meson_key, env_key):
    env_value = os.environ.get(env_key)
    if env_value != None:
        args.file.write("{} = '{}'\n".format(meson_key, env_value))

# Helper to single-quote array items
def _quote_arr(arr):
    return ["'" + item + "'" for item in arr]

# Helper to add an array to crossfile
def _add_arr(meson_key, arr, literal=False):
    if not literal:
        arr = _quote_arr(arr)
    arr_string = (', '.join(arr))
    args.file.write("{} = [{}]\n".format(meson_key, arr_string))

# Helper to add env variable array to crossfile
def _add_environ_arr(meson_key, env_key):
    env_array = os.environ.get(env_key)
    if env_array != None:
        env_values = shlex.split(env_array)
        _add_arr(meson_key, env_values)

# Generate meson crossfile
args.file.write("# Automatically generated by contrib makefile\n")

if args.type == 'internal':
    # Binaries section
    args.file.write("\n[binaries]\n")
    _add_environ_val('c', 'CC')
    _add_environ_val('cpp', 'CXX')
    if os.environ.get('HOST_SYSTEM') == 'darwin':
        _add_environ_val('objc', 'OBJC')
        _add_environ_val('objcpp', 'OBJCXX')
    _add_environ_val('ar', 'AR')
    _add_environ_val('ranlib', 'RANLIB')
    _add_environ_val('strip', 'STRIP')
    _add_environ_val('pkg-config', 'PKG_CONFIG')
    _add_environ_val('windres', 'WINDRES')

    # Properties section
    args.file.write("\n[properties]\n")
    args.file.write("needs_exe_wrapper = true\n")
    _add_environ_val('pkg_config_libdir', 'PKG_CONFIG_LIBDIR')

    # Host machine section
    args.file.write("\n[host_machine]\n")
    _add_environ_val('system', 'HOST_SYSTEM')
    _add_environ_val('cpu_family', 'HOST_ARCH')
    args.file.write("endian = 'little'\n")

    # Get first part of triplet
    cpu = os.environ.get('HOST', '').split('-')[0]
    args.file.write("cpu = '{}'\n".format(cpu))

    # CMake section
    args.file.write("\n[cmake]\n")
    _add_environ_val('CMAKE_C_COMPILER', 'CC')
    _add_environ_val('CMAKE_CXX_COMPILER', 'CXX')
    _add_environ_val('CMAKE_SYSTEM_NAME', 'CMAKE_SYSTEM_NAME')
    _add_environ_val('CMAKE_SYSTEM_PROCESSOR', 'ARCH')

elif args.type.startswith('external'):
    # Constants section
    if args.binary is not None:
        args.file.write("\n[binaries]\n")
        for program_name, program_path in args.binary.items():
            args.file.write(f"{program_name} = '{program_path}'\n")
    args.file.write("\n[constants]\n")
    args.file.write("contrib_dir = '{}'\n".format(os.environ['PREFIX']))
    args.file.write("contrib_libdir = contrib_dir / 'lib'\n")
    args.file.write("contrib_incdir = contrib_dir / 'include'\n")
    args.file.write("contrib_pkgconfdir = contrib_libdir / 'pkgconfig'\n")

    # Properties section
    args.file.write("\n[properties]\n")
    args.file.write("contrib_dir = contrib_dir\n")
    args.file.write("contrib_libdir = contrib_libdir\n")
    args.file.write("contrib_incdir = contrib_incdir\n")

    pkgconfdir_arr = ['contrib_pkgconfdir']
    if args.type == 'external-cross':
        if os.environ.get('PKG_CONFIG', 'pkg-config') == 'pkg-config':
            # If we have no host-specific pkg-config, set the libdir
            # so we do not pick up incompatible deps.
            _add_arr('pkg_config_libdir', pkgconfdir_arr, literal=True)
    else:
        pkgconfpath = os.environ.get('PKG_CONFIG_PATH')
        if pkgconfpath is not None:
            args.file.write("\n[built-in options]\n")
            _add_arr('pkg_config_path', filter(None, pkgconfpath.split(':')))

else:
    assert False, 'Unhandled type!'

