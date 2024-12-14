import logging
import time
from importlib import import_module
from packaging import version

import solcx

from .solidity.nodes import SourceBuilder
from .solidity.utils import from_standard_output

logger = logging.getLogger(__name__)


# Check solc version when we load obfuscator
REQUIRED_SOLC_VER = "0.8.28"

try:
    solc_ver = solcx.get_solc_version()
except Exception as e:
    logger.error("solc is not found on your system.")

required_ver = version.parse(REQUIRED_SOLC_VER)

if solc_ver < required_ver:
    logger.warning(
        f"Your solc version {str(solc_ver)} is smaller than "
        f"{str(REQUIRED_SOLC_VER)}, the output could be wrong!"
    )


class Obfuscator:

    def __init__(self, verbose=False, plugins: list = []):
        self.verbose = verbose
        self.plugins = set()

        for name in plugins:
            if name not in dir():
                plugin = import_module(name=".plugins." + name, package=__package__)
                self.plugins.add(plugin)
            else:
                self.plugins.add(dir()[name])

            logger.debug(f"Loaded plugin {name}.")

    def run(self, url: str, output: str):
        solc_options = {
            "language": "Solidity",
            "sources": {"temp.sol": {"urls": [url]}},
            "settings": {"outputSelection": {"*": {"": ["ast"]}}},
        }

        logger.debug(f"Using solc standard json input {solc_options}.")

        try:
            output_json = solcx.compile_standard(solc_options)
        except Exception as e:
            logger.error(f"Compilation error, check your input file path.\n{e}")
            return

        # TODO: obfuscate all sources under a directory
        nodes = from_standard_output(output_json)
        logger.debug(f"Get {nodes} from source.")
        node = nodes[0]

        start_time = time.time()
        logger.debug(
            f"Obfuscation starts at {time.asctime(time.localtime(start_time))}."
        )

        root = node

        # We are calling plugins.plugin_name.run()
        for plugin in self.plugins:
            root = plugin.run(root)

        # Convert and compress to source code
        builder = SourceBuilder(verbose=self.verbose, indent=4)
        logger.debug("Converting syntax tree to source")
        src = builder.build(root)

        with open(output, "w") as fp:
            fp.write(src)

        elapsed = time.time() - start_time
        logger.debug(f"Obfuscation done! Time elapsed: {elapsed:.8f}s.")
