from django.core.files import File
from base.shared_knowledge.file_format import GENERIC_BINARY_FILE_MIME


class LocalFile(File):
    def __init__(self, file, name=None, content_type=None):
        super().__init__(file, name=name)
        self.content_type = content_type or GENERIC_BINARY_FILE_MIME
