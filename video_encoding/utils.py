import os
import tempfile


def get_fieldfile_local_path(fieldfile):
    local_temp_file = None

    if hasattr(fieldfile, 'storage'):
        storage = fieldfile.storage
        try:
            # Try to access with path
            storage_local_path = storage.path(fieldfile.path)
        except (NotImplementedError, AttributeError):
            # Storage doesnt support absolute paths, download
            # file to a temp local dir
            storage_file = storage.open(fieldfile.name, 'rb')

            local_temp_file = tempfile.NamedTemporaryFile(delete=False)
            local_temp_file.write(storage_file.read())
            local_temp_file.close()
            storage_local_path = local_temp_file.name
    else:
        # Its a local file with no storage abstraction
        try:
            path = os.path.abspath(fieldfile.path)
        except AttributeError:
            path = os.path.abspath(fieldfile.name)

        storage_local_path = path

    return storage_local_path, local_temp_file
