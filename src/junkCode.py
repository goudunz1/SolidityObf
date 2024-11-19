import logging

logger = logging.getLogger(__name__)

def obfuscate(node):
    logger.debug("Applying junk code obfuscation on {node}") 
    return node
