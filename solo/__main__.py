import argparse
import logging
import os

from .obfuscator import Obfuscator

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
    choices=("cff", "oconst", "opredic"),
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

    obfuscator = Obfuscator(verbose=args.verbose, plugins=args.jobs)
    obfuscator.run(url=args.filepath, output=output_path)


if __name__ == "__main__":
    main()
