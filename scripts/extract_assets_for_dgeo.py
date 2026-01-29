#!/usr/bin/env python3
"""Extract STAC asset metadata and conversion outputs for dgeo migration."""

import argparse
import csv
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

from pystac_client import Client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class AssetExtractor:
    """Collect asset metadata plus numbered alternates for CSV export."""

    def __init__(self, catalog_url: str = "https://stac.easierdata.info/api/v1/pgstac"):
        self.catalog_url = catalog_url
        self.client: Client | None = None

    def connect(self) -> None:
        logger.info(f"Connecting to catalog {self.catalog_url}")
        self.client = Client.open(self.catalog_url)
        logger.info("Connection established")

    def extract_assets(self, collection_id: str, max_items: int | None = None) -> List[Dict[str, Any]]:
        if not self.client:
            self.connect()

        logger.info(f"Searching collection {collection_id}")
        search = self.client.search(collections=[collection_id], max_items=max_items)

        records: List[Dict[str, Any]] = []
        item_count = 0

        for item in search.items():
            item_count += 1
            if item_count % 100 == 0:
                logger.info(f"Processed {item_count} items...")

            for asset_key, asset in item.assets.items():
                record: Dict[str, Any] = {
                    "item_id": item.id,
                    "collection_id": item.collection_id,
                    "main_asset_key": asset_key,
                    "main_asset_source_name": asset_key,
                    "main_asset_type": "main",
                    "main_href": asset.href,
                    "main_asset_filename": self._extract_filename_from_href(asset.href),
                    "main_asset_filetype": self._extract_filetype_from_href(asset.href),
                    "main_media_type": asset.media_type or "",
                    "main_title": asset.title or "",
                    "main_roles": ",".join(asset.roles) if asset.roles else "",
                    "main_description": asset.description or "",
                }

                alternates = self._collect_alternates(asset)
                for idx, alt in enumerate(alternates, start=1):
                    prefix = f"alternate_asset_{idx}"
                    record[f"{prefix}_name"] = alt["name"]
                    record[f"{prefix}_normalized_name"] = alt["normalized_name"]
                    record[f"{prefix}_href"] = alt["href"]
                    record[f"{prefix}_type"] = alt["type"]
                    if alt["cid"]:
                        record[f"{prefix}_cid"] = alt["cid"]
                    if alt["piece_cid"]:
                        record[f"{prefix}_piece_cid"] = alt["piece_cid"]

                    if alt["normalized_name"] == "ipfs":
                        record["ipfs_href"] = alt["href"]
                        record["ipfs_cid"] = alt["cid"] or ""
                    elif alt["normalized_name"] == "filecoin":
                        record["filecoin_href"] = alt["href"]
                        record["filecoin_piece_cid"] = alt["piece_cid"] or alt["cid"] or ""

                records.append(record)

        logger.info(f"Extraction complete: {item_count} items, {len(records)} asset records")
        return records

    def _collect_alternates(self, asset) -> List[Dict[str, str]]:
        alternates_list: List[Dict[str, str]] = []
        asset_dict = asset.to_dict()
        raw_alts = asset_dict.get("alternate")

        alternates: Dict[str, Dict[str, Any]] = {}
        if isinstance(raw_alts, dict):
            alternates.update(raw_alts)

        normalized_names = {self._normalize_alternate_key(k) for k in alternates}
        if "http" not in normalized_names:
            alternates["http"] = {"href": asset.href, "type": asset.media_type or ""}

        for key, value in alternates.items():
            if not isinstance(value, dict):
                continue

            normalized = self._normalize_alternate_key(key)
            href = value.get("href", "")
            if normalized == "ipfs":
                href = self._rewrite_ipfs_gateway(href)

            alt_cid = value.get("cid") or self._extract_cid_from_href(href)
            piece_cid = value.get("piece_cid")
            if not piece_cid and normalized == "filecoin":
                piece_cid = self._extract_cid_from_href(href)

            alternates_list.append({
                "name": key,
                "normalized_name": normalized,
                "href": href,
                "type": value.get("type", ""),
                "cid": alt_cid or "",
                "piece_cid": piece_cid or "",
            })

        return alternates_list

    def save_to_csv(self, records: List[Dict[str, Any]], output_path: str) -> None:
        if not records:
            logger.warning("No records to write")
            return

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = set().union(*(rec.keys() for rec in records))
        priority = [
            "item_id", "collection_id",
            "main_asset_key", "main_asset_source_name", "main_asset_type",
            "main_href", "main_asset_filename", "main_asset_filetype", "main_media_type",
            "main_title", "main_roles", "main_description",
            "ipfs_href", "ipfs_cid",
            "filecoin_href", "filecoin_piece_cid",
        ]
        ordered = [field for field in priority if field in fieldnames]
        remaining = sorted(fieldnames - set(ordered))

        logger.info(f"Writing {len(records)} asset rows to {output_path}")
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=ordered + remaining)
            writer.writeheader()
            writer.writerows(records)

        logger.info("CSV export complete")

    @staticmethod
    def _normalize_alternate_key(key: str) -> str:
        if not key:
            return "alternate"
        normalized = re.sub(r"[^0-9a-z]+", "_", key.lower()).strip("_")
        return normalized or "alternate"

    @staticmethod
    def _rewrite_ipfs_gateway(href: str) -> str:
        if href.startswith("https://gateway.easierdata.info"):
            return href.replace("https://gateway.easierdata.info", "https://dweb.link", 1)
        return href

    @staticmethod
    def _extract_cid_from_href(href: str) -> str:
        if not href:
            return ""
        if href.startswith("ipfs://"):
            return href.replace("ipfs://", "").split("/", 1)[0]
        if "/ipfs/" in href:
            return href.split("/ipfs/", 1)[1].split("/", 1)[0]
        if href.startswith("filecoin://"):
            return href.replace("filecoin://", "").split("/", 1)[0]
        return ""

    @staticmethod
    def _extract_filename_from_href(href: str) -> str:
        if not href:
            return ""
        parsed = urlparse(href)
        return Path(parsed.path or href).name

    @staticmethod
    def _extract_filetype_from_href(href: str) -> str:
        filename = AssetExtractor._extract_filename_from_href(href)
        return filename.rsplit(".", 1)[-1] if "." in filename else ""


class CSVConverter:
    """Build JSON payloads keyed by item and grouped by alternates."""

    def convert(self, csv_path: str, output_dir: str | None = None) -> None:
        csv_file = Path(csv_path)
        if not csv_file.exists():
            logger.error(f"CSV not found: {csv_path}")
            sys.exit(1)

        output_dir = Path(output_dir) if output_dir else csv_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Converting {csv_file} to JSON payloads")
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        metadata: Dict[str, Dict[str, Any]] = {}
        asset_cids: Dict[str, Dict[str, Any]] = {}
        full: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            item_id = row["item_id"]
            asset_key = row.get("main_asset_key") or row.get("asset_key")
            if not asset_key:
                logger.warning("Skipping record without asset key")
                continue

            metadata.setdefault(item_id, {
                "id": item_id,
                "collection_id": row.get("collection_id", ""),
                "ipfs_cids": [],
                "filecoin_piece_cids": [],
            })

            full.setdefault(item_id, {
                "item_id": item_id,
                "collection_id": row.get("collection_id", ""),
                "assets": {},
            })
            asset_cids.setdefault(item_id, {"assets": {}})

            ipfs_cid = row.get("ipfs_cid", "").strip()
            if ipfs_cid and ipfs_cid not in metadata[item_id]["ipfs_cids"]:
                metadata[item_id]["ipfs_cids"].append(ipfs_cid)

            piece_cid = row.get("filecoin_piece_cid", "").strip()
            if piece_cid and piece_cid not in metadata[item_id]["filecoin_piece_cids"]:
                metadata[item_id]["filecoin_piece_cids"].append(piece_cid)

            if ipfs_cid:
                asset_cids[item_id]["assets"][asset_key] = {"dgeo:cid": ipfs_cid}

            full[item_id]["assets"][asset_key] = {
                "main": {
                    "asset_key": asset_key,
                    "asset_source_name": row.get("main_asset_source_name", ""),
                    "asset_type": row.get("main_asset_type", ""),
                    "href": row.get("main_href", ""),
                    "filename": row.get("main_asset_filename", ""),
                    "filetype": row.get("main_asset_filetype", ""),
                    "media_type": row.get("main_media_type", ""),
                    "title": row.get("main_title", ""),
                    "roles": row.get("main_roles", ""),
                    "description": row.get("main_description", ""),
                },
                "alternates": self._gather_alternates(row)
            }

        self._write_json(output_dir / f"{csv_file.stem}_metadata.json", metadata)
        self._write_json(output_dir / f"{csv_file.stem}_asset_cids.json", asset_cids)
        self._write_json(output_dir / f"{csv_file.stem}_full.json", full)

        logger.info("Conversion finished")
        logger.info(f"Generated files: {output_dir}/{csv_file.stem}_metadata.json, {output_dir}/{csv_file.stem}_asset_cids.json, {output_dir}/{csv_file.stem}_full.json")

    def _gather_alternates(self, row: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        grouped: Dict[str, Dict[str, str]] = {}
        for key, value in row.items():
            if not key.startswith("alternate_asset_") or not value:
                continue

            suffix = key[len("alternate_asset_"):]
            if "_" not in suffix:
                continue

            idx, prop = suffix.split("_", 1)
            grouped.setdefault(idx, {})[prop] = value

        alternates: Dict[str, Dict[str, str]] = {}
        for values in grouped.values():
            normalized = values.get("normalized_name") or AssetExtractor._normalize_alternate_key(values.get("name", ""))
            data = {
                "name": values.get("name", ""),
                "href": values.get("href", ""),
                "type": values.get("type", ""),
            }
            if "cid" in values:
                data["cid"] = values["cid"]
            if "piece_cid" in values:
                data["piece_cid"] = values["piece_cid"]
            alternates.setdefault(normalized, {}).update(data)

        return alternates

    @staticmethod
    def _write_json(path: Path, data: Any) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract/convert STAC asset metadata for dgeo migration")

    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Extract assets from a STAC collection")
    extract_parser.add_argument("collection_id", help="STAC collection id to fetch")
    extract_parser.add_argument("-o", "--output", required=True, help="CSV output path")
    extract_parser.add_argument("--catalog-url", default="https://stac.easierdata.info/api/v1/pgstac", help="STAC catalog URL")
    extract_parser.add_argument("--max-items", type=int, help="Limit number of items processed")

    convert_parser = subparsers.add_parser("convert", help="Convert an edited CSV into JSON payloads")
    convert_parser.add_argument("csv_file", help="Path to edited CSV file")
    convert_parser.add_argument("-o", "--output-dir", help="Directory for generated JSON files")

    args = parser.parse_args()

    if args.command == "extract":
        extractor = AssetExtractor(catalog_url=args.catalog_url)
        records = extractor.extract_assets(args.collection_id, max_items=args.max_items)
        extractor.save_to_csv(records, args.output)
    elif args.command == "convert":
        CSVConverter().convert(args.csv_file, args.output_dir)


if __name__ == "__main__":
    main()