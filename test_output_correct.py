import json
import os
import random
import shutil
import string
from pathlib import Path
from typing import List, Dict

import pytest

from xml2json.xmlio import JsonTranslator

BASEPATH: str = os.path.dirname(os.path.abspath(__file__))

xml_dir: str = os.path.join(BASEPATH, "fixtures", "xml")
json_dir: str = os.path.join(BASEPATH, "fixtures", "json")

translate: JsonTranslator = JsonTranslator()

to_check: List[str] = [str(xml_fn) for xml_fn in Path(xml_dir).glob("**/*.xml")]

@pytest.mark.parametrize("xml_fn", to_check)
def test_output_correct(xml_fn):
    json_relpath: str = "/".join(xml_fn.split("/")[-3:]).split(".")[0] + ".json"
    json_fn: str = os.path.join(json_dir, json_relpath)
    with open(xml_fn) as xml_fh:
        raw_xml = xml_fh.read()
        if raw_xml.strip() == "":
            return
    actual: Dict = translate(raw_xml)
    with open(json_fn) as json_fh:
        expected = json.load(json_fh)
    assert actual == expected

