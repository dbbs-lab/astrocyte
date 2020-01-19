import unittest, os, sys, argparse

unittest.TestLoader.sortTestMethodsUsing = None
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import astrocyte.cli

astrocyte.cli._exit_on_fail = False

# Duck punch the argument parser so it doesn't sys.exit
def on_argparse_error(self, message):
    raise argparse.ArgumentError(None, message)


argparse.ArgumentParser.error = on_argparse_error


def run_cli_command(command):
    argv = sys.argv
    sys.argv = command.split(" ")
    sys.argv.insert(0, "test_cli_command")
    result = astrocyte.cli.astrocyte_cli()
    sys.argv = argv
    return result


class TestCLI(unittest.TestCase):
    """
        Check if packages can be discovered.
    """

    def test_basics(self):
        self.assertRaises(argparse.ArgumentError, run_cli_command, "doesntexist")

    def test_create(self):
        run_cli_command(
            "create package my-test --name=my_test --author=dude --email=bruv@eyo.com"
        )

    def test_add_mod(self):
        os.chdir("my-test")

        # Add mechanism
        run_cli_command("add mod ../tests/mod/Kca1_1.mod")
        # Add point process
        run_cli_command("add mod ../tests/mod/NMDA.mod")

    def test_build(self):
        run_cli_command("build")

    def test_install(self):
        run_cli_command("install")

    def test_upload(self):
        print("API_USERNAME" in os.environ)
        print(os.getenv("API_USERNAME"))
