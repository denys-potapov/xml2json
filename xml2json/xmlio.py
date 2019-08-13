from collections.abc import Callable
from typing import Dict

from io import StringIO

import re
import lxml.etree
from lxml import etree
from lxml.etree import XMLParser, parse
from xmljson import XMLData
from collections import OrderedDict

# noinspection PyProtectedMember
from xml2json.convert import convert

Element = lxml.etree._Element

def _strip_namespace(raw: str) -> str:
    no_ns = re.sub('(xmlns|xsi)(:.*?)?=\".*?\"', "", raw)
    return no_ns

def _strip_encoding(raw: str) -> str:
    no_encoding = re.sub("\<\?xml.+\?\>", "", raw)
    return no_encoding

def _clean_xml(raw: str) -> str:
    """
    Remove interstitial whitespace (whitespace between XML tags) and
    namespaces. The former makes it difficult to detect text-free nodes,
    and the latter makes Xpaths far uglier and more unwieldy.

    :param raw: string containing XML to be cleaned.

    :return: string containing XML with namespaces and interstitial
    whitespace removed.
    """
    a = raw.encode("ascii", "ignore").decode("ascii")
    no_encoding = _strip_encoding(a)
    no_ns = _strip_namespace(no_encoding)
    return no_ns

def _strip_prefix(almost_clean):
    almost_clean = re.sub("<xsd:", "<", almost_clean)
    almost_clean = re.sub("</xsd:", "</", almost_clean)
    almost_clean = re.sub("<irs:", "<", almost_clean)
    almost_clean = re.sub("</irs:", "</", almost_clean)
    return almost_clean


def _clean_xsd(raw: str) -> str:
    almost_clean = _clean_xml(raw)
    clean = _strip_prefix(almost_clean)
    return clean

# https://lxml.de/parsing.html
# https://stackoverflow.com/questions/11850345/using-python-lxml-etree-for-huge-xml-files
def _get_cleaned_root(raw_xml: str) -> Element:
    cleaned = _clean_xsd(raw_xml)
    p = XMLParser(huge_tree=True)
    tree = parse(StringIO(cleaned), parser=p)
    root = tree.getroot()
    # This line used to stand for the three currently above it. If they fail for some reason, try this one again
    # root = etree.fromstring(cleaned, huge_tree=True)
    return root

class MongoFish(XMLData):
    """Same as BadgerFish convention, except changes "$" to "_" for Mongo."""
    def __init__(self, **kwargs):
        super(MongoFish, self).__init__(attr_prefix='@', text_content='_', **kwargs)


class JsonTranslator(Callable):
    def __init__(self):
        self._fish = MongoFish(dict_type=OrderedDict, xml_fromstring=False)

    def __call__(self, xml_str: str):
        xml = _get_cleaned_root(xml_str)
        fish_json = self._fish.data(xml)
        return convert(fish_json)
