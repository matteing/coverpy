"""Command-line interface for coverpy."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

import requests

from . import __version__
from .client import CoverPy, Entity
from .exceptions import ArtworkUnavailableError, CoverPyError
from .models import Result
from .motion import MotionArtwork


def build_parser() -> argparse.ArgumentParser:
    """Build the coverpy argument parser."""
    parser = argparse.ArgumentParser(
        prog="coverpy", description="Search the iTunes catalog for music artwork."
    )
    parser.add_argument("term", help="album, song, or artist to search for")
    parser.add_argument("--entity", choices=[item.value for item in Entity], default="album")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--country", default="US", help="two-letter iTunes Store country code")
    parser.add_argument("--size", type=int, default=1200, help="square artwork size in pixels")
    parser.add_argument("--no-explicit", action="store_true", help="exclude explicit content")
    parser.add_argument(
        "--motion", action="store_true", help="resolve experimental Apple Music motion artwork"
    )
    parser.add_argument("--json", action="store_true", help="emit normalized JSON")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _format_result(result: Result, size: int, motion: MotionArtwork | None = None) -> str:
    try:
        artwork = result.artwork(size)
    except ArtworkUnavailableError:
        artwork = "unavailable"

    lines = [f"{result.name} — {result.artist}", f"Type: {result.type}", f"Artwork: {artwork}"]
    if result.store_url:
        lines.append(f"Store: {result.store_url}")
    if result.release_date:
        lines.append(f"Released: {result.release_date.date().isoformat()}")
    if result.primary_genre_name:
        lines.append(f"Genre: {result.primary_genre_name}")
    if motion:
        lines.append(f"Motion: {motion.video_url or motion.hls_url}")
        if motion.hq_video_url and motion.hq_video_url != motion.video_url:
            lines.append(f"Motion HQ: {motion.hq_video_url}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the coverpy command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with CoverPy(country=args.country) as client:
            results = client.search(
                args.term,
                args.limit,
                entity=args.entity,
                explicit=False if args.no_explicit else None,
            )
            motion_artwork = (
                [client.get_motion_artwork(result) for result in results]
                if args.motion
                else [None] * len(results)
            )
        if not results:
            print(f"No results found for {args.term!r}.", file=sys.stderr)
            return 1
        if args.json:
            payload = []
            for result, motion in zip(results, motion_artwork, strict=True):
                item = result.as_dict()
                if args.motion:
                    item["motion_artwork"] = motion.as_dict() if motion else None
                payload.append(item)
            print(json.dumps(payload, indent=2))
        else:
            print(
                "\n\n".join(
                    _format_result(result, args.size, motion)
                    for result, motion in zip(results, motion_artwork, strict=True)
                )
            )
    except (CoverPyError, requests.RequestException, TypeError, ValueError) as error:
        print(f"coverpy: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
