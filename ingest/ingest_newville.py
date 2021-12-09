#!/usr/bin/env python

import argparse
import pathlib
import json
from collections import defaultdict

from tiled.examples.xdi import read_xdi

from tqdm import tqdm

import pymongo
from pymongo import MongoClient

from util import serialize_parquet
from util import create_collection


def main():
    parser = argparse.ArgumentParser(description="ingest newville data")
    parser.add_argument(
        "--mongo_uri",
        default="mongodb://root:example@localhost:27017/?authSource=admin",
    )
    parser.add_argument("--db", default="aimm")
    parser.add_argument("--collection", default="newville")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("data_path")

    args = parser.parse_args()

    path = pathlib.Path(args.data_path)
    assert path.exists()
    files = list(path.rglob("*.xdi"))
    print(f"found {len(files)} xdi files to ingest")

    client = MongoClient(args.mongo_uri)
    db = client[args.db]

    with open("schema.json") as f:
        schema = json.load(f)

    c = create_collection(db, args.collection, schema, overwrite=args.overwrite)

    counts = defaultdict(int)

    for f in tqdm(files):
        df, metadata = read_xdi(str(f))
        fields = metadata.pop("fields")
        metadata.update(**fields)
        metadata["filename"] = f.name

        symbol = metadata["Element"]["symbol"]
        edge = metadata["Element"]["edge"]

        uid_prefix = f"{symbol}-{edge}"
        uid_suffix = str(counts[uid_prefix])
        uid = f"{uid_prefix}-{uid_suffix}"
        counts[uid_prefix] += 1

        common = {
            "element": {"symbol": symbol, "edge": edge},
            "spec": "newville",
            "uid": uid,
        }
        metadata["common"] = common

        data = {
            "media_type": "application/x-parquet",
            "structure_family": "dataframe",
            "blob": serialize_parquet(df).tobytes(),
        }

        doc = {"data": data, "metadata": metadata}
        c.insert_one(doc)


if __name__ == "__main__":
    main()