import pathlib
from medialib_v2 import settings
from os import cpu_count

samples_root_dir = pathlib.Path("image_processing/core/tests/decoding/samples")

MAX_FILE_LENGTH = 512
TASK_SAVE_DIRECTORY = settings.MEDIALIB_QUEUE_DIRECTORY

encoding_threads = cpu_count()
if encoding_threads is None:
    encoding_threads = 8
else:
    encoding_threads = min(encoding_threads, 16)

proxy_at_tmp = True
