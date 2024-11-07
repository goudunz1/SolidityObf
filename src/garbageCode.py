import solcast
import logging

from astUtils import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def obfuscate(node: dict) -> dict:
	return node
