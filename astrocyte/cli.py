import os, sys, argparse, json
try:
    from .templates import create_template
except ModuleNotFoundError as _:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from astrocyte.templates import create_template

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

    cl_args = parser.parse_args()
    if hasattr(cl_args, 'func'):
        cl_args.func(cl_args)

def create_package(args):
    folder = os.path.abspath(args.folder)
    try:
        os.mkdir(folder)
    except FileExistsError as _:
        print("Target location already exists.")
        exit(1)
    # Ask package information
    pkg_data = {
        "pkg_name": args.folder,
        "name": input("Package name [{}]: ".format(args.folder)) or args.folder
    }
    pkg_data["author"] = input_required("Author: ")
    pkg_data["email"] = input_required("Email: ")
    pkg_folder = os.path.join(folder, pkg_data["name"])
    astro_folder = os.path.join(folder, ".astro")

    # Create package files
    create_template("setup.py", folder, locals=pkg_data)            # setup.py
    create_template("README.md", folder, locals=pkg_data)           # setup.py
    os.mkdir(pkg_folder)                                            # package folder
    make(os.path.join(pkg_folder, "__init__.py"), "")               # __init__.py
    os.mkdir(astro_folder)                                          # astro folder
    make(os.path.join(astro_folder, "pkg"), json.dumps(pkg_data))   # pkg json

    # Finish
    print("Package skeleton created.")

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
    print("Running astrocyte-cli script.")
    astrocyte_cli()
