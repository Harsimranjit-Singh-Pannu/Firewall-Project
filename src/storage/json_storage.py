
import json
import os

from pathlib import Path
from tempfile import NamedTemporaryFile


class JsonStorage:

    def __init__(
        self,
        folder="storage/versions"
    ):
        self.folder = Path(folder)

        self.folder.mkdir(
            parents=True,
            exist_ok=True
        )

    def save(
        self,
        name,
        data
    ):
        file_path = self.folder / f"{name}.json"
        temp_path = None

        try:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.folder,
                prefix=f".{name}.",
                suffix=".tmp",
                delete=False
            ) as file:
                temp_path = Path(file.name)

                json.dump(
                    data,
                    file,
                    indent=4
                )

                file.flush()
                os.fsync(file.fileno())

            # Replace the destination only after the
            # complete JSON document has been written.
            os.replace(
                temp_path,
                file_path
            )

            return file_path

        finally:
            # Remove incomplete temporary files without
            # touching the previously saved version.
            if (
                temp_path is not None
                and temp_path.exists()
            ):
                temp_path.unlink()

    def load(
        self,
        name
    ):
        file_path = self.folder / f"{name}.json"

        if not file_path.exists():
            raise ValueError(
                "JSON file not found"
            )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            return json.load(file)

    def list(
        self
    ):
        return sorted(
            self.folder.glob("version_*.json"),
            key=lambda path: int(
                path.stem.split("_")[1]
            )
        )

    def delete(
        self,
        name
    ):
        file_path = self.folder / f"{name}.json"

        if file_path.exists():
            file_path.unlink()