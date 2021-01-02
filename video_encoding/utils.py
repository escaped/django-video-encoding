import contextlib
import os
import tempfile
from typing import Generator

from django.core.files import File


@contextlib.contextmanager
def get_local_path(fieldfile: File) -> Generator[str, None, None]:
    """
    Get a local file to work with from a file retrieved from a FileField.
    """
    if not hasattr(fieldfile, 'storage'):
        # Its a local file with no storage abstraction
        try:
            yield os.path.abspath(fieldfile.path)
        except AttributeError:
            yield os.path.abspath(fieldfile.name)
    else:
        storage = fieldfile.storage
        try:
            # Try to access with path
            yield storage.path(fieldfile.path)
        except (NotImplementedError, AttributeError):
            # Storage doesnt support absolute paths,
            # download file to a temp local dir
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
                storage_file = storage.open(fieldfile.name, 'rb')

                temp_file.write(storage_file.read())
                temp_file.flush()
                yield temp_file.name
