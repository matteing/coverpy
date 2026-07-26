from __future__ import annotations

import json
from typing import Any

import responses

from coverpy import MotionArtwork
from coverpy.cli import main

SEARCH_URL = "https://itunes.apple.com/search"


@responses.activate
def test_cli_prints_json(album_item: dict[str, Any], capsys: Any) -> None:
    responses.get(SEARCH_URL, json={"resultCount": 1, "results": [album_item]})

    exit_code = main(["OK Computer", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload[0]["name"] == "OK Computer"
    assert captured.err == ""


@responses.activate
def test_cli_prints_human_output(album_item: dict[str, Any], capsys: Any) -> None:
    responses.get(SEARCH_URL, json={"resultCount": 1, "results": [album_item]})

    exit_code = main(["OK Computer", "--size", "600"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "OK Computer — Radiohead" in output
    assert "600x600bb.jpg" in output
    assert "Released: 2016-04-01" in output


@responses.activate
def test_cli_handles_no_results(capsys: Any) -> None:
    responses.get(SEARCH_URL, json={"resultCount": 0, "results": []})

    exit_code = main(["Nothing"])

    assert exit_code == 1
    assert "No results" in capsys.readouterr().err


def test_cli_handles_validation_errors(capsys: Any) -> None:
    exit_code = main(["OK Computer", "--limit", "0"])

    assert exit_code == 2
    assert "limit" in capsys.readouterr().err


@responses.activate
def test_cli_prints_motion_artwork(
    album_item: dict[str, Any], capsys: Any, monkeypatch: Any
) -> None:
    responses.get(SEARCH_URL, json={"resultCount": 1, "results": [album_item]})
    motion = MotionArtwork(
        album_id=1097861387,
        hls_url="https://video.example/master.m3u8",
        video_url="https://video.example/cover.mp4",
        hq_video_url="https://video.example/cover-hq.mp4",
    )
    monkeypatch.setattr("coverpy.cli.CoverPy.get_motion_artwork", lambda *_: motion)

    exit_code = main(["OK Computer", "--motion", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload[0]["motion_artwork"]["video_url"] == "https://video.example/cover.mp4"
    assert captured.err == ""


@responses.activate
def test_cli_prints_human_motion_artwork(
    album_item: dict[str, Any], capsys: Any, monkeypatch: Any
) -> None:
    responses.get(SEARCH_URL, json={"resultCount": 1, "results": [album_item]})
    motion = MotionArtwork(
        album_id=1097861387,
        hls_url="https://video.example/master.m3u8",
        video_url="https://video.example/cover.mp4",
        hq_video_url="https://video.example/cover-hq.mp4",
    )
    monkeypatch.setattr("coverpy.cli.CoverPy.get_motion_artwork", lambda *_: motion)

    exit_code = main(["OK Computer", "--motion"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Motion: https://video.example/cover.mp4" in output
    assert "Motion HQ: https://video.example/cover-hq.mp4" in output
