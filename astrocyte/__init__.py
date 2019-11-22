import os, sys, json
from shutil import copy2 as copy_file
from .exceptions import AstroError, StructureError, UploadError, \
    InvalidDistributionError, InvalidMetaError

__version__ = "0.0.1a6"

def execute_command(cmnd):
    import subprocess
    process = subprocess.Popen(cmnd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out_str, std_err_str = '', ''
    for c in iter(lambda: process.stdout.read(1), b''):
        s = c.decode('UTF-8')
        sys.stdout.write(s)
        std_out_str += s
    for c in iter(lambda: process.stderr.read(1), b''):
        s = c.decode('UTF-8')
        std_err_str += s
    return process, std_out_str, std_err_str

class Package:
    def __init__(self, path, pkg_data):
        self.data = pkg_data
        self.package_name = pkg_data["pkg_name"]
        self.name = pkg_data["name"]
        self.astro_version = pkg_data["astro_version"]
        self.glia_version = pkg_data["glia_version"]
        self.set_path(path)

    def __str__(self):
        return self.package_name + " v" + self.version

    def add_mod_file(self, file):
        if not os.path.exists(file):
            raise AstroError("Mod file not found.")
        extension = os.path.splitext(file)[1]
        if extension != ".mod":
            raise AstroError("This is not a mod file.")
        mod_name = os.path.splitext(os.path.basename(file))[0]
        og_name = mod_name
        if not mod_name.startswith('_glia__'+self.name+'__'):
            mod_name = '_glia__' + self.name + '__' + mod_name
        if len(mod_name.split("__")) == 3:
            mod_name = mod_name + '__0'
        if len(mod_name.split("__")) != 4:
            raise AstroError("Glia mod names cannot contain double underscores unless the filename follows the Glia naming convention.")
        if og_name != mod_name:
            print("Mod filename changed from '{}' to '{}'".format(og_name, mod_name))
        copy_file(file, os.path.join(self.path, self.name, "mod", mod_name + ".mod"))
        mod = Mod(self, mod_name)
        print("__init__.py updated.")

    def set_path(self, path):
        self.path = path
        sys.path.insert(0, self.path)
        self.version = __import__(self.name).__version__
        sys.path.remove(self.path)

    def get_source_path(self, *args):
        return os.path.join(self.path, self.name, *args)

    def build(self):
        import subprocess
        print("Building glia package", self)
        rcode = subprocess.call([sys.executable, "setup.py", "bdist_wheel"])
        self._built = rcode == 0
        if self._built:
            print("Glia package built.")

    def built(self):
        return hasattr(self, "_built") and self._built

    def upload(self):
        import subprocess
        print("Uploading glia package", self)
        cmnd = ["twine", "upload", os.path.join("dist", "*{}*".format(self.version))]
        process, out, err = execute_command(cmnd)
        self._uploaded = process.returncode == 0
        if not self._uploaded:
            if err.find("InvalidDistributionError") != -1:
                raise InvalidDistributionError("No build files for " + str(self)
                    + ". Use `astro build`.")
            elif err.find("Error: Use a valid email address") != -1:
                raise InvalidMetaError("The package author email metadata is invalid.")
            else:
                sys.stderr.write(err)
        else:
            print("Uploaded glia package", self)

def get_package(path=None):
    path = path or os.getcwd()
    try:
        pkg_data = json.load(open(os.path.join(path, ".astro", "pkg")))
    except FileNotFoundError as _:
        raise AstroError("This directory is not a glia package.")
        exit(1)
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
        self.writer = Writer(self)
        self.writer.update()

    def get_full_name(self):
        return "{}__{}__{}".format(self.namespace, self.asset_name, self.variant)

    def get_writername(self):
        return "mod" + self.get_full_name()

def get_glia_version():
    # TODO: Use pip to find the installed glia version.
    return "0.0.1"

def get_minimum_glia_version():
    # TODO: Use pip to find the installed glia version and determine major version
    return get_glia_version()

class Writer:
    exclude = ['pkg', 'writer']

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

    def in_it(self):
        tagline = self.get_tagline()
        return any(map(lambda l: l.strip() == tagline, self.read))

    def get_tagline(self):
        return "#-" + self.obj.get_writername()

    def insert(self):
        i, indent = self.find_line("return pkg", return_indent=True)
        self.read[i:i] = self.footer(indent)
        self.read[i:i] = self.content(indent)
        self.read[i:i] = self.header(indent)
        self.write()

    def header(self, indent=0):
        return [
            self.line("#-Generated by Astrocyte v{}".format(__version__), indent),
            self.line(self.get_tagline(), indent)
        ]

    def content(self, indent=0):
        lines = [self.line(self.obj.get_writername() + " = " + self.obj.__class__.__name__ + "()", indent)]
        for k, v in self.obj.__dict__.items():
            if not k in self.__class__.exclude:
                lines.append(self.property_line(k, v, indent))
        return lines

    def footer(self, indent=0):
        return [
            self.line("pkg.mods.append({})".format(self.obj.get_writername()), indent),
            self.line("#-##", indent)
        ]

    def line(self, msg, indent=0):
        return (" " * indent) + msg + "\n"

    def property_line(self, k, v, indent):
        if isinstance(v, str):
            return self.line(self.obj.get_writername() + ".{} = '{}'".format(k, v), indent)
        raise Exception("Unknown property type {} for {}".format(type(v).__name__, k))

    def find_line(self, line, return_indent=False):
        for i, l in enumerate(self.read):
            if l.strip() == line:
                if return_indent:
                    return i, len(l) - len(l.lstrip(' '))
                else:
                    return i
        raise StructureError("__init__.py structure compromised.")

    def write(self):
        init_file = open(self.get_init_path(), "w")
        init_file.writelines(self.read)
        init_file.close()
