import os, sys, argparse, json
from shutil import copy2 as copy_file

try:
    from .templates import create_template
    from . import Package, get_package, load_local_pkg, get_glia_version, __version__
    from .exceptions import AstroError
except ModuleNotFoundError as _:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from astrocyte import (
        Package,
        load_local_pkg,
        get_package,
        get_glia_version,
        __version__,
    )
    from astrocyte.templates import create_template
    from astrocyte.exceptions import AstroError

_exit_on_fail = True


class AliasedSubParsersAction(argparse._SubParsersAction):
    old_init = staticmethod(argparse._ActionsContainer.__init__)

    @staticmethod
    def _containerInit(
        self, description, prefix_chars, argument_default, conflict_handler
    ):
        AliasedSubParsersAction.old_init(
            self, description, prefix_chars, argument_default, conflict_handler
        )
        self.register("action", "parsers", AliasedSubParsersAction)

    class _AliasedPseudoAction(argparse.Action):
        def __init__(self, name, aliases, help):
            dest = name
            if aliases:
                dest += " (%s)" % ",".join(aliases)
            sup = super(AliasedSubParsersAction._AliasedPseudoAction, self)
            sup.__init__(option_strings=[], dest=dest, help=help)

    def add_parser(self, name, **kwargs):
        aliases = kwargs.pop("aliases", [])
        parser = super(AliasedSubParsersAction, self).add_parser(name, **kwargs)

        # Make the aliases work.
        for alias in aliases:
            self._name_parser_map[alias] = parser
        # Make the help text reflect them, first removing old help entry.
        if "help" in kwargs:
            help = kwargs.pop("help")
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
    create_parser = subparsers.add_parser(
        "create", aliases=("c"), description="Create packages or components."
    )
    create_subparsers = create_parser.add_subparsers()
    create_package_parser = create_subparsers.add_parser(
        "package", aliases=("pkg", "p"), description="Create an empty package."
    )
    create_package_parser.add_argument(
        "folder", action="store", help="Location of the package folder."
    )
    create_package_parser.add_argument(
        "--name", action="store", help="Name of the package."
    )
    create_package_parser.add_argument(
        "--author", action="store", help="Author of the package."
    )
    create_package_parser.add_argument(
        "--email", action="store", help="Email of the author."
    )
    create_package_parser.set_defaults(func=create_package)

    # Add mod file
    add_parser = subparsers.add_parser(
        "add", aliases=("a"), description="Create packages or components."
    )
    add_subparsers = add_parser.add_subparsers()
    add_mod_parser = add_subparsers.add_parser(
        "mod", aliases=("m"), description="Add a mod file to your package."
    )
    add_mod_parser.add_argument("file", action="store", help="Path of the mod file.")
    add_mod_parser.add_argument(
        "-n", "--name", action="store", help="Asset name of the mod file."
    )
    add_mod_parser.add_argument(
        "-v", "--variant", action="store", help="Variant name of the asset.", default="0"
    )
    add_mod_parser.add_argument(
        "-l", "--local", action="store_true", help="Add the mod file for local use."
    )
    add_mod_parser.set_defaults(func=add_mod_file)

    # Edit asset
    edit_parser = subparsers.add_parser(
        "edit", aliases=("a"), description="Edit packages or components."
    )
    edit_parser.add_argument(
        "asset", action="store", help="Unique part of the asset name."
    )
    edit_parser.add_argument("-n", "--name", action="store", help="New asset name.")
    edit_parser.add_argument("-v", "--variant", action="store", help="New variant name.")
    edit_parser.add_argument(
        "-l", "--local", action="store_true", help="Edit a local asset."
    )
    edit_parser.set_defaults(func=edit_mod_file)

    # Remove mod file
    remove_parser = subparsers.add_parser(
        "remove", aliases=["rm"], description="Remove components from the package."
    )
    remove_subparsers = remove_parser.add_subparsers()
    remove_mod_parser = remove_subparsers.add_parser(
        "mod", aliases=("m"), description="Remove a mod file to your package."
    )
    remove_mod_parser.add_argument("name", action="store", help="Name of the asset.")
    remove_mod_parser.add_argument(
        "-v", "--variant", action="store", help="Variant name of the asset."
    )
    remove_mod_parser.add_argument(
        "-f", "--force", action="store_true", help="Don't prompt for confirmation."
    )
    remove_mod_parser.add_argument(
        "-l", "--local", action="store_true", help="Remove the mod file for local use."
    )
    remove_mod_parser.set_defaults(func=remove_mod_file)

    # Build wheel
    wheel_parser = subparsers.add_parser(
        "build", description="Build the package into a wheel."
    )
    wheel_parser.add_argument(
        "--upload", action="store_true", help="Upload the wheel after a succesfull build."
    )
    wheel_parser.add_argument(
        "--install",
        action="store_true",
        help="Install the wheel after a succesfull build.",
    )
    wheel_parser.set_defaults(func=build_package)

    # Upload wheel
    upload_parser = subparsers.add_parser(
        "upload", description="Upload current wheel to PyPI."
    )
    upload_parser.set_defaults(func=upload_package)

    # Install wheel
    install_parser = subparsers.add_parser(
        "install", description="Install current wheel."
    )
    install_parser.set_defaults(func=install_package)

    # Uninstall wheel
    uninstall_parser = subparsers.add_parser(
        "uninstall", description="Uninstall current wheel."
    )
    uninstall_parser.set_defaults(func=uninstall_package)

    cl_args = parser.parse_args()
    if hasattr(cl_args, "func"):
        try:
            cl_args.func(cl_args)
        except AstroError as e:
            print("ERROR", str(e))
            if _exit_on_fail:
                exit(1)
            else:
                raise


def create_package(args, presets=None):
    # Set presets for non-interactive mode.
    if presets is None:
        presets = {}
        if args.author:
            presets["author"] = args.author
        if args.email:
            presets["email"] = args.email
        if args.name:
            presets["pkg_name"] = args.name
    if not "folder" in presets:
        presets["folder"] = None
    if not "pkg_name" in presets:
        presets["pkg_name"] = None
    # Get paths. `folder` is the absolute path and `folder_name` doubles as the package name
    folder = os.path.abspath(args.folder)
    folder_name = args.folder.split(os.sep)[-1]
    # Create root folder
    try:
        os.mkdir(folder)
    except FileExistsError as _:
        raise AstroError("Target location already exists.") from None
    # Initialize git repo.
    from git import Repo, Actor

    repo = Repo.init(folder)
    # Ask package information
    pkg_data = {
        "pkg_name": folder_name,
        # Package naming priority: preset > user input > folder name.
        "name": presets["pkg_name"]
        or input("Package name [{}]: ".format(folder_name))
        or folder_name,
    }
    pkg_data["author"] = input_required("author", presets)
    pkg_data["email"] = input_required("email", presets)
    # Fill in the rest of the package information.
    pkg_data["glia_version"] = get_glia_version()
    pkg_data["astro_version"] = __version__
    pkg_folder = os.path.join(folder, pkg_data["name"])
    mod_folder = os.path.join(pkg_folder, "mod")
    astro_folder = os.path.join(folder, ".astro")

    # Create package files
    create_template("setup.py", folder, locals=pkg_data)  # setup.py
    create_template("README.md", folder, locals=pkg_data)  # README
    create_template(".gitignore", folder)  # .gitignore
    os.mkdir(pkg_folder)  # package folder
    os.mkdir(mod_folder)  # mod folder
    create_template("__init__.py", pkg_folder, locals=pkg_data)  # __init__.py
    os.mkdir(astro_folder)  # astro folder
    make(os.path.join(astro_folder, "pkg"), json.dumps(pkg_data))  # pkg json

    # Hide .astro folder on Windows
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.kernel32.SetFileAttributesW(astro_folder, 2)

    # Make initial commit
    index = repo.index
    index.add(repo.untracked_files)
    author = Actor(pkg_data["author"], pkg_data["email"])
    index.commit(
        "Initial commit generated by Astrocyte.", author=author, committer=author
    )
    # Finish
    print("Package skeleton created.")
    return Package(folder, pkg_data)


def _get_pkg(args):
    if args.local:
        return load_local_pkg()
    else:
        return get_package()


def add_mod_file(args):
    pkg = _get_pkg(args)
    pkg.add_mod_file(args.file, name=args.name, variant=args.variant)
    print("Added mod file.")


def remove_mod_file(args):
    pkg = _get_pkg(args)
    candidates = pkg.get_mod_candidates(args.name)
    if not candidates:
        raise AstroError("No assets found matching '{}'".format(args.name))
    message = (
        str(len(candidates))
        + " mod files found:\n"
        + "\n".join(candidates)
        + "\nAre you sure you want to remove the above mod files [y/n]? "
    )
    if not args.force and input(message) != "y":
        return
    for candidate in candidates:
        pkg.remove_mod_file(candidate)
    pkg.commit("Removed " + ", ".join(candidates))


def edit_mod_file(args):
    pkg = _get_pkg(args)
    pkg.edit_asset(args.asset, name=args.name, variant=args.variant)


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


def uninstall_package(args):
    pkg = get_package()
    pkg.uninstall()


def make(target, content):
    f = open(target, "w")
    f.write(content)
    f.close()


def input_required(key, presets={}):
    # Silly ol' trick for non-interactive mode.
    if key in presets:
        return presets[key]
    response = ""
    while not response:
        response = input(key.capitalize() + ": ")
    return response


if __name__ == "__main__":
    print("Careful! Executing cli.py is unsupported.")
    astrocyte_cli()
