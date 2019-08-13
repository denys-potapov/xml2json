"""Used to generate JSON fixtures."""
import time
from pathlib import Path
import json
import logging
import os
from typing import Dict
from xml2json.xmlio import JsonTranslator

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

BASEPATH: str = os.path.dirname(os.path.abspath(__file__))

xml_dir: str = os.path.join(BASEPATH, "..", "fixtures", "xml")
json_dir: str = "/tmp/xml2json"
os.makedirs(json_dir)

translate: JsonTranslator = JsonTranslator()

chunk_time: float = 0.0

# SO 2186525
for i, xml_fn in enumerate(Path(xml_dir).glob("**/*.xml")):
    xml_fn = str(xml_fn)
    json_relpath: str = "/".join(xml_fn.split("/")[-2:]).split(".")[0] + ".json"
    json_fn: str = os.path.join(json_dir, json_relpath)
    start = time.time()
    json_dirpath: str = "/".join(json_fn.split("/")[:-1])
    os.makedirs(json_dirpath, exist_ok=True)
    with open(xml_fn) as xml_fh:
        raw_xml = xml_fh.read()
        if raw_xml.strip() == "":
            logging.error("%s is empty. Skipping." % xml_fn)
            continue
    with open(json_fn, "w") as json_fh:
        as_json: Dict = translate(raw_xml)
        json.dump(as_json, json_fh)
    elapsed = (time.time() - start) * 1000
    chunk_time += elapsed
    if i > 0 and i % 10 == 0:
        avg_time: float = chunk_time / 10
        print("Completed {:,} conversions. Average for last 10: {:0.3}ms per record.".format(i, avg_time))
        chunk_time = 0.0