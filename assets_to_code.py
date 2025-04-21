from argparse import ArgumentParser, Namespace
from base64 import b64encode
from enum import StrEnum
from io import BytesIO
from os import listdir
from pathlib import Path
from typing import cast


class FileAccess(StrEnum):
    Read = "r"
    Binary = "b"
    Write = "w"


class Encoding(StrEnum):
    UTF_8 = "utf-8"


class FileType(StrEnum):
    PNG = ".png"
    JPEG = ".jpeg"
    JPG = ".jpg"


def convert_png(path: Path) -> str:
    with open(path, FileAccess.Read + FileAccess.Binary) as png_file:
        return b64encode(cast(BytesIO, png_file).read()).decode(Encoding.UTF_8)


def convert_file(path: Path) -> str:
    output: str | None = None

    match path.suffix.lower():
        # Example on how to add a custom encoder for png files or whatever:
        case FileType.PNG:
            output = convert_png(path)
        case _:
            with open(path, FileAccess.Read + FileAccess.Binary) as file:
                output = b64encode(cast(BytesIO, file).read()).decode(Encoding.UTF_8)

    return output


def convert_dir_contents(source_dir: Path) -> dict[Path, str]:
    output: dict[Path, str] = {}

    for node in listdir(source_dir):
        node_path: Path = source_dir / node
        if node_path.is_dir():
            output = output | convert_dir_contents(node_path)
        else:
            output[node_path] = convert_file(node_path)

    return output


def convert_assets(assets_dir: Path, output_file: Path) -> None:
    encoded_assets: dict[Path, str] = convert_dir_contents(assets_dir)
    with open(output_file, FileAccess.Write, encoding=Encoding.UTF_8) as out_file_io:
        out_file_io.writelines([
            "from pathlib import Path\n",
            "from typing import Final\n",
            "\n",
            "\n",
            "ASSETS: Final[dict[Path, str]] = {\n",
            *[f"    Path(r\"{str(k.relative_to(assets_dir))}\"): r\"{v}\",\n" for k, v in encoded_assets.items()],
            "}\n"
        ])


if __name__ == "__main__":
    parser: ArgumentParser = ArgumentParser(
        description="Convert assets to python code. Useful for avoiding asset dir issues."
    )
    parser.add_argument("--assets_dir", "-a", required=True, help="Path to the assets directory.")
    parser.add_argument("--output_file", "-o", required=False, help="Output file containing the encoded assets.")

    arguments: Namespace = parser.parse_args()
    convert_assets(
        Path(arguments.assets_dir),
        Path(arguments.output_file) if arguments.output_file else Path(__file__).parent.resolve() / "encoded_assets.py"
    )
