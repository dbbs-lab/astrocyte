import os, sys, json, glob, re, fnmatch
from shutil import copy2 as copy_file
from appdirs import AppDirs
from .exceptions import *

__version__ = "0.1.1"

app_directories = AppDirs("Astrocyte", "Alexandria")


def execute_command(cmnd):
    import subprocess

    process = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out_str, std_err_str = "", ""
    for c in iter(lambda: process.stdout.read(1), b""):
        s = c.decode("UTF-8", "ignore")
        sys.stdout.write(s)
        std_out_str += s
    for c in iter(lambda: process.stderr.read(1), b""):
        s = c.decode("UTF-8", "ignore")
        std_err_str += s
    return process, std_out_str, std_err_str


def execute_python(script):
    return execute_command([sys.executable, "-c" + script])


class Package:
    def __init__(self, path, pkg_data):
        from git import Repo, Actor

        self.repo = Repo(path)
        self.data = pkg_data
        self.package_name = pkg_data["pkg_name"]
        self.name = pkg_data["name"]
        self.astro_version = pkg_data["astro_version"]
        self.glia_version = pkg_data["glia_version"]
        self.author = Actor(pkg_data["author"], pkg_data["email"])
        self.set_path(path)

    def __str__(self):
        return self.package_name + " v" + self.version

    def add_mod_file(self, file, name=None, variant="0"):
        if not os.path.exists(file):
            raise AstroError("Mod file not found.")
        extension = os.path.splitext(file)[1]
        if extension != ".mod":
            raise AstroError("This is not a mod file.")
        if name is not None:
            mod_name = "glia__" + self.name + "__" + name + "__" + variant
        else:
            mod_name = get_path_mod_name(file)
            og_name = mod_name
            if mod_name.startswith("glia__"):
                if len(mod_name.split("__")) != 4:
                    raise AstroError(
                        "Mod files cannot contain double underscores unless the filename follows the Glia naming convention."
                    )
                pkg_name, asset, variant = parse_asset_name(mod_name)
                mod_name = "glia__{}__{}__{}".format(self.name, asset, variant)
            else:
                mod_name = "glia__" + self.name + "__" + mod_name + "__" + variant
            if og_name != mod_name:
                print("Mod filename changed from '{}' to '{}'".format(og_name, mod_name))
        self.import_mod_file(
            file, os.path.join(self.path, self.name, "mod", mod_name + ".mod"), mod_name
        )
        self.commit("Added " + mod_name)

    def import_mod_file(self, origin, destination, name):
        from shutil import copy2

        copy2(origin, destination)
        mod = Mod(self, name)
        mod.sanitize_mod_file()
        return mod

    def edit_asset(self, mod_part, name=None, variant=None):
        candidates = list(
            map(
                lambda x: get_path_mod_name(x),
                find_files(self.get_mod_path("*" + mod_part + "*")),
            )
        )
        if len(candidates) == 0:
            raise AstroError("No assets found matching '{}'".format(mod_part))
        elif len(candidates) > 1:
            raise AstroError(
                "Multiple matches found for '{}'".format(mod_part)
                + "\n"
                + "\n".join(candidates)
            )
        mod = Mod(self, candidates[0])
        mod.set_names(name=name, variant=variant)

    def set_path(self, path):
        self.path = path
        sys.path.insert(0, self.path)
        self.version = __import__(self.name).__version__
        sys.path.remove(self.path)

    def get_source_path(self, *args):
        return os.path.join(self.path, self.name, *args)

    def get_mod_path(self, *args):
        return self.get_source_path("mod", *args)

    def build(self):
        import subprocess
        from time import sleep

        cwd = os.getcwd()
        os.chdir(self.path)
        self.increment_version()
        sleep(0.5)
        print("Building glia package", self)
        self.commit("New build, incremented version")
        rcode = subprocess.call([sys.executable, "setup.py", "bdist_wheel"])
        os.chdir(cwd)
        self._built = rcode == 0
        if self._built:
            print("Glia package built.")

    def built(self):
        return hasattr(self, "_built") and self._built

    def upload(self):
        from . import api
        import subprocess

        cdw = os.getcwd()
        os.chdir(self.path)
        print("Uploading glia package", self)
        api.upload_meta(self)
        cmnd = [
            "twine",
            "upload",
            "--username=_",
            "--password=" + api.get_valid_token(),
            "--disable-progress-bar",
            "--repository-url=" + api.__repo_url__,
            os.path.join("dist", "*{}*".format(self.version)),
        ]
        process, out, err = execute_command(cmnd)
        process.communicate()
        os.chdir(cwd)
        self._uploaded = process.returncode == 0
        if not self._uploaded:
            if err.find("InvalidDistributionError") != -1:
                raise InvalidDistributionError(
                    "No build files for " + str(self) + ". Use `astro build`."
                )
            elif err.find("Error: Use a valid email address") != -1:
                raise InvalidMetaError("The package author email metadata is invalid.")
            else:
                sys.stderr.write(err)
        else:
            print("Uploaded glia package", self)

    def link(self):
        import subprocess, site

        cwd = os.getcwd()
        os.chdir(self.path)

        cmnd = [sys.executable, "-m", "pip", "install", "-e", "."]
        process, out, err = execute_command(cmnd)
        process.communicate()
        self._linked = process.returncode == 0

        os.chdir(cwd)
        if not self._linked:
            raise BuildError("Could not create egg link:" + err)
        else:
            print(self, "egg linked.")

    def install(self):
        import subprocess, site

        site_packages = list(
            filter(lambda s: s.find("site-packages") != -1, site.getsitepackages())
        )
        distfile = self.get_distribution()
        old_dir = os.getcwd()
        if len(site_packages) > 0:
            os.chdir(site_packages[0])
        print("Installing glia package", self)
        cmnd = [sys.executable, "-m", "pip", "install", distfile]
        process, out, err = execute_command(cmnd)
        # Extra call to communicate required or subprocess freezes.
        process.communicate()
        os.chdir(old_dir)
        self._installed = process.returncode == 0
        if not self._installed:
            raise BuildError("Could not install build:" + err)
        else:
            print("Installed glia package", self)
            import glia

    def uninstall(self):
        import subprocess, site

        site_packages = list(
            filter(lambda s: s.find("site-packages") != -1, site.getsitepackages())
        )
        distfile = self.get_distribution()
        old_dir = os.getcwd()
        if len(site_packages) > 0:
            os.chdir(site_packages[0])
        print("Uninstalling glia package", self)
        cmnd = [sys.executable, "-m", "pip", "uninstall", "-y", distfile]
        process, out, err = execute_command(cmnd)
        # Extra call to communicate required or subprocess freezes.
        process.communicate()
        os.chdir(old_dir)
        self._installed = process.returncode != 0
        if self._installed:
            raise BuildError("Could not uninstall:" + err)
        else:
            print("Uninstalled glia package", self)
            import glia

    def increment_version(self):
        splits = self.version.split(".")
        new_version = ".".join(splits[0:-1]) + "." + str(int(splits[-1]) + 1)
        v = lambda v: '__version__ = "{}"'.format(v)
        with open(self.get_source_path("__init__.py"), "r") as file:
            content = file.read().replace(v(self.version), v(new_version))
        with open(self.get_source_path("__init__.py"), "w") as file:
            file.write(content)
            self.version = new_version

    def commit(self, message):
        # Add modified files to commit
        self.repo.git.add(update=True)
        index = self.repo.index
        # Add new files to commit
        index.add(self.repo.untracked_files)
        # Make commit
        index.commit(message, author=self.author, committer=self.author)

    def get_distribution(self):
        try:
            return os.path.abspath(
                glob.glob(os.path.join(self.path, "dist", "*{}*".format(self.version)))[0]
            )
        except IndexError as _:
            raise InvalidDistributionError(
                "No build files for " + str(self) + ". Use `astro build`."
            )


def get_package(path=None):
    path = path or os.getcwd()
    print("PATH?", path, os.getcwd())
    try:
        print("LISTDIR:", os.listdir(os.path.join(path, ".astro")))
        pkg_data = json.load(open(os.path.join(path, ".astro", "pkg")))
    except FileNotFoundError as _:
        raise AstroError("This directory is not a glia package.")
    pkg = Package(path, pkg_data)
    return pkg


class Mod:
    def __init__(self, pkg, namespaced_name):
        self.pkg = pkg
        self.pkg_name = pkg.name
        splits = namespaced_name.split("__")
        self.asset_name = "__".join(splits[2:-1])
        self.variant = splits[-1]
        self.namespace = "__".join(splits[:2])
        self._is_point_process = self.is_point_process()
        self.writer = Writer(self)
        self.writer.update()

    def get_full_name(self):
        return get_asset_name(self.namespace, self.asset_name, self.variant)

    def get_writername(self):
        return "mod_" + self.get_full_name()

    def set_names(self, name=None, variant=None):
        """
            Change this Mod's names. Updates the mod file and __init__.py
        """
        old_asset_name = self.asset_name
        old_variant = self.variant
        new_asset_name = name or self.asset_name
        new_variant = variant or self.variant
        old_name = self.get_full_name()
        new_name = get_asset_name(self.namespace, new_asset_name, new_variant)
        os.rename(
            self.pkg.get_mod_path(old_name) + ".mod",
            self.pkg.get_mod_path(new_name) + ".mod",
        )
        self.writer.replace(old_name, new_name)
        self.asset_name = new_asset_name
        self.variant = new_variant
        self.writer.update()
        self.sanitize_mod_file()
        self.pkg.commit(
            "Renamed {} to {}".format(
                old_asset_name + "." + old_variant, new_asset_name + "." + new_variant
            )
        )

    def get_mod_file(self):
        """
            Return the full filename of the mod file.
        """
        return self.pkg.get_mod_path(self.get_full_name()) + ".mod"

    def sanitize_mod_file(self):
        # Read the mod file.
        with open(self.get_mod_file(), "r") as f:
            lines = f.readlines()
        inserts = []
        # Define the statement that needs to be replaced with the new name
        # For a mechanism that's "SUFFIX <name>"
        # For a point_process it's "POINT_PROCESS <name>"
        if not self._is_point_process:
            name_statement = "SUFFIX"
        else:
            name_statement = "POINT_PROCESS"
        # Iterate over all lines to find name statements and the correct position
        # to insert our new name statement (as the first line of the NEURON block)
        for i, l in enumerate(lines):
            # Remove all previous name statements
            if l.lower().strip().startswith(name_statement.lower()):
                lines.remove(l)
            if l.replace("{", "").lower().strip() == "neuron":
                # Add the name statement to be inserted.
                inserts.append(
                    (i + 1, name_statement + " " + self.get_full_name() + "\n")
                )
        # Inser the new statements
        for i, l in enumerate(inserts):
            lines.insert(i + l[0], l[1])
        # Write the new mod file.
        with open(self.get_mod_file(), "w") as f:
            f.writelines(lines)

    def is_point_process(self):
        with open(self.get_mod_file(), "r") as f:
            lines = f.readlines()
        for line in lines:
            if line.strip().lower().startswith("point_process"):
                return True
        return False


def get_glia_version():
    # TODO: Use pip to find the installed glia version.
    return "0.1.1"


def get_minimum_glia_version():
    # TODO: Use pip to find the installed glia version and determine major version
    return get_glia_version()


class Writer:
    exclude = ["pkg", "writer"]
    repr_types = [int, bool, str]

    def __init__(self, obj):
        self.obj = obj

    def get_init_path(self):
        return self.obj.pkg.get_source_path("__init__.py")

    def update(self):
        init_file = open(self.get_init_path(), "r")
        self.read = init_file.readlines()
        init_file.close()
        if not self.in_it():
            self.insert()
        else:
            content, roi = self.read_block()
            fresh = {}
            for k, v in self.obj.__dict__.items():
                if not k in self.__class__.exclude:
                    line = self.property_line(k, v, self.indent)
                    if k in content:
                        # Replace existing content line, mark it as used
                        self.read[content[k][0]] = line
                        fresh[k] = True
                    else:
                        # Add a new content line before the end
                        self.read[(roi[1] - 2) : (roi[1] - 2)] = [line]
                        roi = tuple([roi[0], roi[1] + 1])
            for key, line in sorted(content.items(), key=lambda x: x[1][0], reverse=True):
                if not key in fresh:
                    del self.read[line[0]]
            self.write()

    def in_it(self):
        return self.find_tagline() > -1

    def find_tagline(self, find_end=False):
        tagline = self.get_tagline()
        endline = self.get_endline()
        start = -1
        for i, l in enumerate(self.read):
            if l.strip() == tagline:
                self.indent = len(l) - len(l.lstrip(" "))
                if not find_end:
                    return i
                else:
                    start = i
            if start != -1 and l.strip() == endline:
                return start, i
        return -1

    def read_block(self):
        start_i, end_i = self.find_tagline(find_end=True)
        roi = range(start_i, end_i)
        values = {}
        for i in roi:
            line = self.read[i].strip()
            if (
                line.startswith("#")
                or line.startswith("pkg")
                or line.endswith("= Mod()")
                or line.endswith("= pkg")
            ):
                continue
            assignee, evaluee = tuple(line.split("="))
            evaluee = eval(evaluee)
            assignee = ".".join(assignee.split(".")[1:]).strip()
            values[assignee] = (i, evaluee)
        return values, (start_i, end_i)

    def get_tagline(self):
        return "#-" + self.obj.get_writername()

    def get_endline(self):
        return "#-##"

    def insert(self):
        i, indent = self.find_line("return pkg", return_indent=True)
        self.indent = indent
        self.read[i:i] = self.footer(indent)
        self.read[i:i] = self.content(indent)
        self.read[i:i] = self.header(indent)
        self.write()

    def header(self, indent=0):
        return [
            self.line("#-Generated by Astrocyte v{}".format(__version__), indent),
            self.line(self.get_tagline(), indent),
        ]

    def content(self, indent=0):
        lines = [
            self.line(
                self.obj.get_writername() + " = " + self.obj.__class__.__name__ + "()",
                indent,
            )
        ]
        for k, v in self.obj.__dict__.items():
            if not k in self.__class__.exclude:
                lines.append(self.property_line(k, v, indent))
        lines.append(self.line(self.obj.get_writername() + ".pkg = pkg", indent))
        return lines

    def footer(self, indent=0):
        return [
            self.line("pkg.mods.append({})".format(self.obj.get_writername()), indent),
            self.line("#-##", indent),
        ]

    def line(self, msg, indent=0):
        return (" " * indent) + msg + "\n"

    def property_line(self, k, v, indent):
        if type(v) in self.__class__.repr_types:
            return self.line(
                self.obj.get_writername() + ".{} = {}".format(k, repr(v)), indent
            )
        raise Exception("Unknown property type {} for {}".format(type(v).__name__, k))

    def find_line(self, line, return_indent=False):
        for i, l in enumerate(self.read):
            if l.strip() == line:
                if return_indent:
                    return i, len(l) - len(l.lstrip(" "))
                else:
                    return i
        raise StructureError("__init__.py structure compromised.")

    def write(self):
        init_file = open(self.get_init_path(), "w")
        init_file.writelines(self.read)
        init_file.close()

    def replace(self, old, new):
        init_file = open(self.get_init_path(), "r")
        content = init_file.read()
        init_file.close()
        init_file = open(self.get_init_path(), "w")
        init_file.write(content.replace(old, new))
        init_file.close()


def parse_asset_name(name):
    splits = name.split("__")
    if len(splits) != 4:
        raise AstroError("Invalid mod name '{}'".format(name))
    return tuple(splits[1:])


def get_asset_name(namespace, name, variant="0"):
    return "{}__{}__{}".format(namespace, name, variant)


def get_path_mod_name(path):
    return os.path.splitext(os.path.basename(path))[0]


def find_files(path_pattern):
    pths = glob.glob(path_pattern)

    match = re.compile(fnmatch.translate(path_pattern)).match
    valid_pths = [pth for pth in pths if match(pth)]

    return valid_pths


def load_local_pkg():
    local_path = os.path.join(app_directories.user_data_dir, "local")
    if os.path.exists(local_path):
        local = get_package(local_path)
    else:
        from .cli import create_package
        from time import sleep

        args = type("Namespace", (object,), {"folder": local_path})()
        local = create_package(
            args, {"author": "User", "email": "not@applicable.com", "pkg_name": "local"}
        )
        local.link()
    return local
