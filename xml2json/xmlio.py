from collections.abc import Callable
from typing import Dict

from io import StringIO

import re
import lxml.etree
from lxml import etree
from lxml.etree import XMLParser, parse
from xmljson import XMLData
from collections import Counter, OrderedDict

# noinspection PyProtectedMember
# from .convert import convert

import sys
# Python 3: define unicode() as str()
if sys.version_info[0] == 3:
    unicode = str
    basestring = str

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
        super(MongoFish, self).__init__(
            dict_type=OrderedDict, xml_fromstring=False, text_content=True, simple_text=True)

    def data(self, root):
        '''Convert etree.Element into a dictionary'''
        value = self.dict()
        children = [node for node in root if isinstance(node.tag, basestring)]
        
        root_d = self.dict()
        for attr, attrval in root.attrib.items():
            root_d[root.tag + '@' + attr] = self._fromstring(attrval)
        if root.text and self.text_content is not None:
            text = root.text.strip()
            if text:
                if self.simple_text and len(children) == 0:
                    value = self._fromstring(text)
                else:
                    value[self.text_content] = self._fromstring(text)
        count = Counter(child.tag for child in children)
        for child in children:
            if count[child.tag] == 1:
                value.update(self.data(child))
            else:
                result = value.setdefault(child.tag, self.list())
                result += self.data(child).values()
                
        # if simple_text, elements with no children nor attrs become empty dict not {}
        if isinstance(value, dict) and not value and self.simple_text:
            return self.dict() #  value = ''

        root_d[root.tag] = value
        root_d.move_to_end(root.tag, last=False)
        return root_d #  self.dict([(root.tag, value)])

class JsonTranslator(Callable):
    def __init__(self):
        self._fish = MongoFish()

    def __call__(self, xml_str: str):
        xml = _get_cleaned_root(xml_str)
        fish_json = self._fish.data(xml)

        return fish_json #  convert(fish_json)
