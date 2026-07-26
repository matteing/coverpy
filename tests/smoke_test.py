"""Minimal installed-package smoke test used by distribution workflows."""

from coverpy import CoverPy, Result, __version__


def main() -> None:
    result = Result.from_api(
        {
            "wrapperType": "collection",
            "collectionType": "Album",
            "artistName": "Radiohead",
            "collectionName": "OK Computer",
            "artworkUrl100": "https://example.test/100x100bb.jpg",
        }
    )
    assert result.name == "OK Computer"
    assert result.artwork(600).endswith("600x600bb.jpg")
    assert __version__ != "0+unknown"
    CoverPy().close()


if __name__ == "__main__":
    main()
