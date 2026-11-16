"""Bounded public-source acquisition for local review, never training approval.

Stores immutable raw files and source metadata. Commons search topics are retrieval
hints, not category/severity labels. No archives are extracted or code executed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlparse

import httpx
from PIL import Image

HOSTS = {"zenodo.org", "commons.wikimedia.org", "upload.wikimedia.org", "data.mendeley.com",
         "prod-dcd-datasets-public-files-eu-west-1.s3.eu-west-1.amazonaws.com"}
DWSD_SHA256 = "fb9229c330ed253f4fb7c18bd46dddebe4df6f8d3f602747f505ff7601a11737"
TOPICS = {
    "garbage_waste": ["Kolkata garbage", "India garbage dump"],
    "drainage_sewerage": ["Kolkata sewage", "India open drain"],
    "waterlogging": ["Kolkata waterlogging", "Chennai flooded street"],
    "water_supply": ["India leaking water pipe", "Kolkata public water tap", "India water pipeline", "Kolkata water supply"],
    "streetlight": ["India broken streetlight", "Kolkata street light"],
    "footpath_access": ["India broken sidewalk", "Kolkata footpath obstruction", "India footpath"],
    "public_sanitation": ["India public toilet"],
    "trees_storm_damage": ["Kolkata Amphan damage", "Howrah fallen tree"],
    "construction_debris": ["India construction debris"],
    "pollution": ["Kolkata burning garbage", "India polluted canal"],
    "public_asset_damage": ["India damaged public park", "Kolkata playground", "India damaged building"],
    "animals_public_space": ["India stray dogs", "Kolkata cattle street"],
    "electrical_hazards": ["Kolkata electric wires", "India fallen electric pole"],
}
INDIA_PATTERN = re.compile(
    r"\b(india|kolkata|calcutta|howrah|west bengal|chennai|mumbai|bengaluru|bangalore)\b", re.I
)


def check_url(url):
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.username
            or parsed.password or parsed.port not in {None, 443}):
        raise ValueError("Unexpected download host/scheme")


def safe_name(value):
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    if (not value or value[-1:] in {".", " "} or any(c in value for c in '/\\:<>"|?*')
            or any(ord(c) < 32 for c in value) or Path(value).name != value
            or value.split(".")[0].upper() in reserved):
        raise ValueError("Unsafe source filename")
    return value


def save_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)


def download(client, url, path, limit, *, expected_size=None, expected_md5=None, expected_sha256=None):
    check_url(url)
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    # Exclusive creation preserves an existing/partial snapshot for diagnosis.
    with path.open("xb") as target:
        for redirect in range(4):
            check_url(url)
            with client.stream("GET", url, follow_redirects=False) as response:
                if response.is_redirect:
                    if redirect == 3:
                        raise ValueError("Too many redirects")
                    url = str(response.url.join(response.headers["location"]))
                    continue
                response.raise_for_status()
                for chunk in response.iter_bytes(1024 * 1024):
                    size += len(chunk)
                    if size > limit:
                        raise ValueError("Download exceeds configured limit")
                    target.write(chunk)
                    sha.update(chunk)
                    md5.update(chunk)
                break
    if expected_size is not None and size != expected_size:
        raise ValueError("Downloaded size mismatch")
    if expected_md5 is not None and md5.hexdigest() != expected_md5:
        raise ValueError("Publisher checksum mismatch")
    if expected_sha256 is not None and sha.hexdigest() != expected_sha256:
        raise ValueError("Publisher checksum mismatch")
    return {"file": path.name, "bytes": size, "sha256": sha.hexdigest(), "md5": md5.hexdigest()}


def metadata(client, url, output):
    download(client, url, output, 10 * 1024 * 1024)
    return json.loads(output.read_text(encoding="utf-8"))


def begin(output):
    output.mkdir(parents=True, exist_ok=False)
    (output / "INCOMPLETE").write_text("Acquisition is incomplete; do not train.\n", encoding="utf-8")


def finish(output, report):
    report.update(retrieved_at=datetime.now(timezone.utc).isoformat(), training_approved=False)
    save_json(output / "acquisition.json", report)
    (output / "COMPLETE").write_text("Acquisition only; no training approval.\n", encoding="utf-8")
    (output / "INCOMPLETE").unlink()
    print(json.dumps(report, ensure_ascii=True), flush=True)


def footpath(client, output, include_archive=False):
    begin(output)
    record = metadata(client, "https://zenodo.org/api/records/17154852", output / "source_metadata.json")
    if record["metadata"]["license"]["id"] != "cc-by-4.0":
        raise ValueError("Source license changed; review before download")
    files = [f for f in record["files"] if include_archive or not f["key"].endswith(".zip")]
    total = sum(f["size"] for f in files)
    if total > 5_000_000_000 or shutil.disk_usage(output).free < total + 5_000_000_000:
        raise ValueError("Acquisition budget or free-space reserve exceeded")
    results = []
    for f in files:
        print("Downloading footpath source file: " + f["key"], flush=True)
        if not f["checksum"].startswith("md5:"):
            raise ValueError("Unexpected publisher checksum format")
        results.append(download(client, f["links"]["self"], output / safe_name(f["key"]),
                                f["size"], expected_size=f["size"], expected_md5=f["checksum"][4:]))
    finish(output, {"source": "zenodo-footpath-17154852", "license": "CC BY 4.0",
                    "country_basis": "publisher describes Pune, India collection",
                    "archive_downloaded": include_archive, "files": results})


def plain(value):
    return html.unescape(re.sub(r"<[^>]+>", " ", value))


def dwsd(client, output):
    begin(output)
    base = "https://data.mendeley.com/public-api/datasets/gr99ny6b8p"
    source = metadata(client, base + "/snapshot/1", output / "source_metadata.json")
    if source["licence"]["short_name"] != "CC BY 4.0" or source["version"] != 1:
        raise ValueError("DWSD source/license changed; review before download")
    files = metadata(client, base + "/files?folder_id=root&version=1&$start=0&$limit=1000",
                     output / "source_files.json")
    if len(files) != 1 or files[0]["filename"] != "DSWD.zip":
        raise ValueError("DWSD archive listing changed")
    file = files[0]
    detail = file["content_details"]
    if detail["sha256_hash"] != DWSD_SHA256 or detail["size"] != 252719363:
        raise ValueError("DWSD pinned archive changed")
    if shutil.disk_usage(output).free < detail["size"] + 5_000_000_000:
        raise ValueError("Free-space reserve exceeded")
    print("Downloading West Bengal DWSD archive", flush=True)
    result = download(client, detail["download_url"], output / safe_name(file["filename"]),
                      detail["size"], expected_size=detail["size"], expected_sha256=DWSD_SHA256)
    finish(output, {"source": "mendeley-dwsd-gr99ny6b8p-v1", "license": "CC BY 4.0",
                    "country_basis": "publisher and paper describe West Bengal collection",
                    "files": [result], "severity_labels_available": False,
                    "augmentation_parent_review_required": True})


def eligible(page):
    info = page.get("imageinfo", [{}])[0]
    ext = info.get("extmetadata", {})
    license_name = ext.get("LicenseShortName", {}).get("value", "")
    # Explicitly support common freely reusable photo licenses, not all Commons media.
    license_ok = bool(re.fullmatch(r"CC BY(?:-SA)? (?:2\.0|2\.5|3\.0|4\.0)|CC0|Public domain", license_name))
    basis = plain(page.get("title", "") + " " + ext.get("ImageDescription", {}).get("value", ""))
    if not license_ok or not INDIA_PATTERN.search(basis):
        return False
    return info.get("mime") in {"image/jpeg", "image/png"} and 0 < info.get("size", 0) <= 20 * 1024 * 1024


def commons(client, output, per_query=5, topics=None):
    if not 1 <= per_query <= 10:
        raise ValueError("per-query must be 1..10")
    if topics is not None and (not topics or any(t not in TOPICS for t in topics)):
        raise ValueError("Unknown/empty retrieval topics")
    begin(output)
    images = output / "images"
    images.mkdir()
    records, rejected, seen, hashes = [], [], set(), set()
    counts, total = Counter(), 0
    for topic, queries in TOPICS.items():
        if topics is not None and topic not in topics:
            continue
        for query in queries:
            params = {"action": "query", "format": "json", "generator": "search", "gsrsearch": query,
                      "gsrnamespace": 6, "gsrlimit": per_query, "prop": "imageinfo",
                      "iiprop": "url|extmetadata|size|mime|sha1"}
            url = str(httpx.URL("https://commons.wikimedia.org/w/api.php", params=params))
            number = len(list(output.glob("search-*.json"))) + 1
            data = metadata(client, url, output / f"search-{number:02}.json")
            if "error" in data:
                raise ValueError("Commons API returned an error")
            for page in sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p["pageid"]):
                identity = page["pageid"]
                if identity in seen:
                    continue
                seen.add(identity)
                if not eligible(page):
                    rejected.append({"pageid": identity, "reason": "license/geography/type/size gate"})
                    continue
                info = page["imageinfo"][0]
                if info.get("sha1") in hashes:
                    rejected.append({"pageid": identity, "reason": "duplicate publisher content hash"})
                    continue
                if total + info["size"] > 300 * 1024 * 1024:
                    rejected.append({"pageid": identity, "reason": "300 MiB acquisition budget"})
                    continue
                extension = ".jpg" if info["mime"] == "image/jpeg" else ".png"
                target = images / f"commons-{identity}{extension}"
                item = download(client, info["url"], target, 20 * 1024 * 1024, expected_size=info["size"])
                with Image.open(target) as im:
                    width, height = im.size
                    im.verify()
                item.update(file=target.relative_to(output).as_posix(), pageid=identity,
                            source_page=info["descriptionurl"], source_title=page["title"],
                            source_metadata=info["extmetadata"], publisher_sha1=info.get("sha1"),
                            retrieval_topic=topic, query=query, width=width, height=height,
                            country_basis="source title/description; not independently location-verified",
                            category_label=None, severity_label=None, annotation_status="pending",
                            split="unassigned", privacy_review="pending")
                records.append(item)
                # Checkpoint each raw acquisition; a later network failure cannot hide completed files.
                save_json(output / f"record-{identity}.json", item)
                hashes.add(info.get("sha1"))
                counts[topic] += 1
                total += item["bytes"]
            print(f"Retrieved {len(records)} candidate photos; topic {topic}", flush=True)
    save_json(output / "candidates.json", records)
    save_json(output / "rejections.json", rejected)
    finish(output, {"source": "wikimedia-commons-indian-civic-review-pool", "images": len(records),
                    "bytes": total, "retrieval_topic_counts_not_labels": dict(counts),
                    "rejected": len(rejected), "no_paired_complaint_text": True})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=["footpath", "commons", "dwsd"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-archive", action="store_true")
    parser.add_argument("--per-query", type=int, default=5)
    parser.add_argument("--topics", nargs="+", choices=list(TOPICS), help="Commons retrieval topics only")
    args = parser.parse_args()
    with httpx.Client(timeout=httpx.Timeout(60, connect=20), follow_redirects=False,
                      headers={"User-Agent": "CivicAI-Research/0.1 (https://github.com/Soumodeep-Das/civic-ai)"}) as client:
        if args.source == "footpath":
            footpath(client, args.output, args.include_archive)
        elif args.source == "dwsd":
            dwsd(client, args.output)
        else:
            commons(client, args.output, args.per_query, args.topics)


if __name__ == "__main__":
    main()
