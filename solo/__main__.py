import argparse
import logging
import os

from .obfuscator import Obfuscator

plugins = {
    "rename": {"name": "identifierRenaming", "enabled": True},
    "const": {"name": "opaqueConstants", "enabled": True},
    "bogus": {"name": "opaquePredicates", "enabled": True},
    "dfo": {"name": "dataFlowObfuscation", "enabled": True},
    "cff": {"name": "controlFlowFlatten", "enabled": True},
}

parser = argparse.ArgumentParser()

parser.add_argument("filepath", help="the path of the file to obfuscate")
parser.add_argument(
    "--version", "-v", help="display version of this obfuscator", action="store_true"
)
parser.add_argument(
    "--verbose", "-V", help="print debug information", action="store_true"
)
parser.add_argument(
    "--output", "-o", help="the path of the obfuscated file", metavar="out.sol"
)
parser.add_argument(
    "--jobs",
    "-j",
    default=[],
    choices=plugins.keys(),
    help="set the plugins to execute",
    nargs="*",
    action="extend",
)

args = parser.parse_args()

if args.verbose == True:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    file_name = os.path.basename(args.filepath)
    file_dir = os.path.dirname(args.filepath)

    if args.output is not None:
        output_path = args.output
    else:
        file_base, _ = os.path.splitext(file_name)
        output_path = file_dir + os.path.sep + file_base + ".out.sol"

    logger.debug(f"Using {output_path} as output.")

    active_plugins = []
    for j in args.jobs:
        if plugins[j]["enabled"] is True:
            active_plugins.append(plugins[j]["name"])

    obfuscator = Obfuscator(verbose=args.verbose, plugins=active_plugins)
    obfuscator.run(url=args.filepath, output=output_path)


if __name__ == "__main__":
    main()
