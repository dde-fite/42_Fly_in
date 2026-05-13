from __future__ import annotations
from typing import TYPE_CHECKING
from io import BytesIO
from fastapi import UploadFile

if TYPE_CHECKING:
    from _typeshed import FileDescriptorOrPath


def file_to_uploadfile(file: FileDescriptorOrPath) -> UploadFile:
    with open(file, "rb") as f:
        content = f.read()
    return UploadFile(
        filename="map.txt",
        file=BytesIO(content)
    )
