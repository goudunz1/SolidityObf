import sys, os, argparse, json
import solcx, solcast
from copy import deepcopy
from importlib import import_module
from packaging import version
import logging

from astUtils import node2source

logging.basicConfig(level=logging.DEBUG)

SOLC_VERSION = "0.8.28"

MODULES = [
	{"name": "garbageCode", "enabled": True},
	{"name": "dataFlowObfuscate", "enabled": False},
	{"name": "opaquePredicates", "enabled": False},
	{"name": "controlFlowFlatten", "enabled": False},
	{"name": "layoutObfuscate", "enabled": False},
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

logger = logging.getLogger(__name__)


def main():
	
	# check solc version
	try:
		solc_ver = solcx.get_solc_version()
	except Exception as e:
		logging.error("solc is not found on your system")
		return

	expect_ver = version.parse(SOLC_VERSION)
	if solc_ver < expect_ver:
		logging.warning(f"Your solc version {str(solc_ver)} is smaller than "
				  f"{str(expect_ver)}, the output could be wrong!")

	# parse input and output file
	file_name = os.path.basename(args.filepath)
	file_dir = os.path.dirname(args.filepath)

	if args.output is not None:
		output_path = args.output
	else:
		file_base, _ = os.path.splitext(file_name)
		output_path = file_dir + os.path.sep + file_base + "_obf.sol"
	
	logging.debug(f"Using {output_path} as output")

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
			#"stopAfter": "parsing",
			"outputSelection": {
				"*": {
					"": [
						"ast",
					]
				}
			}
		}
	}

	logging.debug(f"Using solc standard json input {solc_options}")

	# get ast node
	try:
		output_json = solcx.compile_standard(solc_options, allow_paths=os.path.dirname(output_path))
	except Exception as e:
		logging.error(f"Compilation error, check your input file path")
		return

	nodes = solcast.from_standard_output(output_json)
	logging.debug(f"Get {nodes} from source")

	node = nodes[0]  # TODO: obfuscate all sources under a directory

	# do obfuscation
	node_obf = deepcopy(node)
	for m in MODULES:
		if m["enabled"] is True:

			module_name = m["name"]
			module = import_module(module_name)
			logging.debug(f"Loadded obfuscation module {module_name}")

			# calling module.obfuscate.do()
			node_obf = module.obfuscate(node_obf)

	# convert and compress to source code
	source_obf = node2source(node_obf)
	with open(output_path, "w") as fp:
		fp.write(source_obf)

	logging.debug(f"Done!")


if __name__ == "__main__":
	main()
