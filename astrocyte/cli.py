import os, sys, argparse, json
from shutil import copy2 as copy_file
try:
    from .templates import create_template
    from . import Package, get_package, get_glia_version, __version__
    from .exceptions import AstroError
except ModuleNotFoundError as _:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from astrocyte import Package, get_package, get_glia_version, __version__
    from astrocyte.templates import create_template
    from astrocyte.exceptions import AstroError

class AliasedSubParsersAction(argparse._SubParsersAction):
    old_init = staticmethod(argparse._ActionsContainer.__init__)

    @staticmethod
    def _containerInit(self, description, prefix_chars, argument_default, conflict_handler):
        AliasedSubParsersAction.old_init(self, description, prefix_chars, argument_default, conflict_handler)
        self.register('action', 'parsers', AliasedSubParsersAction)

    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, help):
            dest = name
            if aliases:
                dest += ' (%s)' % ','.join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=help)

    def add_parser(self, name, **kwargs):
        aliases = kwargs.pop('aliases', [])
        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if 'help' in kwargs:
            help = kwargs.pop('help')
            self._choices_actions.pop()
            pseudo_action = self._AliasedPseudoAction(name, aliases, help)
            self._choices_actions.append(pseudo_action)

        return parser

# override argparse to register new subparser action by default
argparse._ActionsContainer.__init__ = AliasedSubParsersAction._containerInit

def astrocyte_cli():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Create package
    create_parser = subparsers.add_parser("create", aliases=('c'), description="Create packages or components.")
    create_subparsers = create_parser.add_subparsers()
    create_package_parser = create_subparsers.add_parser("package", aliases=('pkg', 'p'), description="Create an empty package.")
    create_package_parser.add_argument('folder', action='store', help='Location of the package folder.')
    create_package_parser.set_defaults(func=create_package)

    # Add mod file
    add_parser = subparsers.add_parser("add", aliases=('a'), description="Create packages or components.")
    add_subparsers = add_parser.add_subparsers()
    add_mod_parser = add_subparsers.add_parser("mod", aliases=('m'), description="Add a mod file to your package.")
    add_mod_parser.add_argument('file', action='store', help='Path of the mod file.')
    add_mod_parser.set_defaults(func=add_mod_file)

    # Build wheel
    wheel_parser = subparsers.add_parser("build", description="Build the package into a wheel.")
    wheel_parser.add_argument("--upload", action="store_true", help="Upload the wheel after a succesfull build.")
    wheel_parser.add_argument("--install", action="store_true", help="Install the wheel after a succesfull build.")
    wheel_parser.set_defaults(func=build_package)

    # Upload wheel
    wheel_parser = subparsers.add_parser("upload", description="Upload current wheel to PyPI.")
    wheel_parser.set_defaults(func=upload_package)

    # Install wheel
    wheel_parser = subparsers.add_parser("install", description="Install current wheel.")
    wheel_parser.set_defaults(func=install_package)

    cl_args = parser.parse_args()
    if hasattr(cl_args, 'func'):
        try:
            cl_args.func(cl_args)
        except AstroError as e:
            print('ERROR',str(e))
            exit(1)

def create_package(args):
    folder = os.path.abspath(args.folder)
    try:
        os.mkdir(folder)
    except FileExistsError as _:
        raise AstroError("Target location already exists.") from None
    # Ask package information
    pkg_data = {
        "pkg_name": args.folder,
        "name": input("Package name [{}]: ".format(args.folder)) or args.folder
    }
    pkg_data["author"] = input_required("Author: ")
    pkg_data["email"] = input_required("Email: ")
    pkg_data["glia_version"] = get_glia_version()
    pkg_data["astro_version"] = __version__
    pkg_folder = os.path.join(folder, pkg_data["name"])
    mod_folder = os.path.join(pkg_folder, "mod")
    astro_folder = os.path.join(folder, ".astro")

    # Create package files
    create_template("setup.py", folder, locals=pkg_data)            # setup.py
    create_template("README.md", folder, locals=pkg_data)           # README
    create_template(".gitignore", folder)                           # .gitignore
    os.mkdir(pkg_folder)                                            # package folder
    os.mkdir(mod_folder)                                            # mod folder
    create_template("__init__.py", pkg_folder, locals=pkg_data)     # __init__.py
    os.mkdir(astro_folder)                                          # astro folder
    make(os.path.join(astro_folder, "pkg"), json.dumps(pkg_data))   # pkg json

    # Finish
    print("Package skeleton created.")

def add_mod_file(args):
    pkg = get_package()
    pkg.add_mod_file(args.file)

def build_package(args):
    pkg = get_package()
    pkg.build()
    if pkg.built() and args.install:
        pkg.install()
    if pkg.built() and args.upload:
        pkg.upload()

def upload_package(args):
    pkg = get_package()
    pkg.upload()

def install_package(args):
    pkg = get_package()
    pkg.install()

def make(target, content):
    f = open(target, "w")
    f.write(content)
    f.close()

def input_required(msg):
    response = ""
    while not response:
        response = input(msg)
    return response

if __name__ == "__main__":
    print("Careful! Executing cli.py is unsupported.")
    astrocyte_cli()
