import sys, os, argparse, json
import solcx, solcast
from copy import deepcopy
from importlib import import_module
from packaging import version
import logging
import time

from astUtils import node2src

SOLC_VERSION = "0.8.28"

#LOG_LEVEL = logging.INFO
LOG_LEVEL = logging.DEBUG

MODULES = [
    # to enable a module, add it here
    # all modules must implement function obfuscate() which takes a SourceUnit
    # node as input and returns a obfuscated SourceUnit node
    #
    # example of adding and enabling cff.py
    # {"name": "cff", "enabled": True},
    {"name": "junkCode", "enabled": True},
    {"name": "opaquePredicates", "enabled": True}
]

parser = argparse.ArgumentParser()

parser.add_argument("filepath", help="the path of the file to obfuscate")
parser.add_argument(
    "--version", "-v", help="display version of this obfuscator", action="store_true"
)
parser.add_argument(
    "--verbose", "-V", help="print debug information", action="store_true"
)
parser.add_argument("--output", "-o", help="the path of the obfuscated file")

args = parser.parse_args()

logging.basicConfig(level=LOG_LEVEL)

logger = logging.getLogger(__name__)


def main():

    # check solc version
    try:
        solc_ver = solcx.get_solc_version()
    except Exception as e:
        logger.error("solc is not found on your system")
        return

    expect_ver = version.parse(SOLC_VERSION)
    if solc_ver < expect_ver:
        logger.warning(
            f"Your solc version {str(solc_ver)} is smaller than "
            f"{str(expect_ver)}, the output could be wrong!"
        )

    # parse input and output file
    file_name = os.path.basename(args.filepath)
    file_dir = os.path.dirname(args.filepath)

    if args.output is not None:
        output_path = args.output
    else:
        file_base, _ = os.path.splitext(file_name)
        output_path = file_dir + os.path.sep + file_base + ".obfuscated.sol"

    logger.debug(f"Using {output_path} as output")

    # generate solc options to compile ast
    solc_options = {
        "language": "Solidity",
        "sources": {
            file_name: {
                "urls": [
                    args.filepath,
                ]
            },
        },
        "settings": {
            # "stopAfter": "parsing",
            "outputSelection": {
                "*": {
                    "": [
                        "ast",
                    ]
                }
            }
        },
    }

    logger.debug(f"Using solc standard json input {solc_options}")

    # get ast node
    try:
        output_json = solcx.compile_standard(
            solc_options, allow_paths=os.path.dirname(output_path)
        )
    except Exception as e:
        logger.error(f"Compilation error, check your input file path")
        return

    # with open("english_auction.json", "w", encoding="utf-8") as json_file:
    #     json.dump(output_json, json_file, ensure_ascii=False, indent=4)

    nodes = solcast.from_standard_output(output_json)
    logger.debug(f"Get {nodes} from source")

    node = nodes[0]  # TODO: obfuscate all sources under a directory
    # print(node['conditionTest']['condition'].nodes[0].__dict__)
    # print(node['conditionTest']['condition'].nodes[0].condition.__dict__)

    start_time = time.time()
    logger.debug(f"Obfuscation starts at {time.asctime(time.localtime(start_time))}")

    # TODO: currently deepcopy of solcast node may encounter problems because of
    # parent <-> child reference
    # gonna integrate its code instead of importing it in the future
    # for now we do not copy it
    # if a copy is really needed, regenerate one with output_json
    #node_obf = deepcopy(node)
    node_obf = node

    for m in MODULES:
        if m["enabled"] is True:

            module_name = m["name"]
            module = import_module(module_name)
            logger.debug(f"Loaded obfuscation module {module_name}")

            # we're calling module.obfuscate() here
            node_obf = module.obfuscate(node_obf)

    # convert and compress to source code
    if LOG_LEVEL == logging.DEBUG:
        source_obf = node2src(node_obf, indent=2)
    else:
        source_obf = node2src(node_obf)

    with open(output_path, "w") as fp:
        fp.write(source_obf)

    elapsed = time.time() - start_time
    logger.debug(f"Done! Time elapsed: {elapsed:.8f}s")


if __name__ == "__main__":
    main()
