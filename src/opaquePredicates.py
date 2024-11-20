import json
import logging
import os

import solcast
from packaging import version
import solcx

from collections import deque

logger = logging.getLogger(__name__)

SOLC_VERSION = "0.8.28"

def obfuscate(node):
    logger.debug("Inserting opaque predicates obfuscation on {node}")

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

    file_name = 'opaque_predicates.sol'

    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    file_path = os.path.join(current_directory, file_name)

    # generate solc options to compile ast
    solc_options = {
        "language": "Solidity",
        "sources": {
            file_name: {
                "urls": [
                    file_path,
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

    # generate ast some predicates nodes
    try:
        output_json = solcx.compile_standard(
            solc_options
        )
    except Exception as e:
        logger.error(f"Compilation error, check your input file path")
        return

    nodes = solcast.from_standard_output(output_json)
    logger.debug(f"Get {nodes} from source")


    pNode = nodes[0]

    # create opaque predicates
    predicate_variable_declaration1 = nodes[0].nodes[1].nodes[0].nodes[0]
    predicate1 = nodes[0].nodes[1].nodes[0].nodes[1]

    predicate_variable_declaration2 = nodes[0].nodes[1].nodes[0].nodes[2]
    predicate2 = nodes[0].nodes[1].nodes[0].nodes[3]

    predicate_variable_declaration3 = nodes[0].nodes[1].nodes[0].nodes[4]
    predicate_variable_declaration4 = nodes[0].nodes[1].nodes[0].nodes[5]
    predicate3 = nodes[0].nodes[1].nodes[0].nodes[6]


    # traverse the ast to insert opaque predicates

    queue = deque([(node, 0)])  # BFS deque
    count = 0
    max_depth = 2
    while queue:
        x, depth = queue.popleft()
        print(x)
        if depth > max_depth:
            break
        if hasattr(x, 'nodes') and depth <= max_depth:
            for child in x.nodes:
                queue.append((child, depth + 1))
        if x.nodeType == 'FunctionDefinition' and hasattr(x, 'nodes'):
            original_nodes = x.nodes
            predicate_reference = None
            if count % 3 == 0:
                predicate_reference = predicate1
                x.nodes = [predicate_variable_declaration1, predicate_reference]
            elif count % 3 == 1:
                predicate_reference = predicate2
                x.nodes = [predicate_variable_declaration2, predicate_reference]
            elif count % 3 == 2:
                predicate_reference = predicate3
                x.nodes = [predicate_variable_declaration3, predicate_variable_declaration4, predicate_reference]
            count += 1
            predicate_reference.trueBody = original_nodes

    print(node.nodes[2].nodes[13].__dict__)

    logger.debug("Opaque predicates insertion done")

    return node