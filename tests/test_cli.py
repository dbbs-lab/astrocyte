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

    def test_0_basics(self):
        self.assertRaises(argparse.ArgumentError, run_cli_command, "doesntexist")

    def test_1_create(self):
        run_cli_command(
            "create package my-test --name=my_test --author=dude --email=bruv@eyo.com"
        )
        os.chdir("my-test")

    def test_2_add_mod(self):
        # Add mechanism
        run_cli_command("add mod ../tests/mod/Kca1_1.mod")
        # Add point process
        run_cli_command("add mod ../tests/mod/NMDA.mod")

    def test_3_build(self):
        run_cli_command("build")

    def test_4_install(self):
        run_cli_command("install")

    @unittest.skipIf(
        not os.getenv("API_PASSWORD") or not os.getenv("API_USERNAME"),
        "No credentials found in environment",
    )
    def test_5_upload(self):
        run_cli_command(
            "upload --user="
            + os.getenv("API_USERNAME")
            + " --password="
            + os.getenv("API_PASSWORD")
        )
