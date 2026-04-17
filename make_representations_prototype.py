import os
import django
import pathlib
import argparse

# Django set up must be exactly there
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "medialib_v2.settings")
django.setup()

from image_processing.services import analysis, media_passport  # noqa: E402
from image_processing.services.representations import (  # noqa: E402
    make_representations,
    get_image_signatures,
)

argument_parser = argparse.ArgumentParser()
argument_parser.add_argument("input_file", type=pathlib.Path)


if __name__ == "__main__":
    args = argument_parser.parse_args()
    input_file: pathlib.Path = args.input_file
    passport: media_passport.BaseMediaPassport
    compatibility_level: int
    passport, compatibility_level = analysis.analyze_file(input_file)
    representations = make_representations(passport, compatibility_level)
    print(representations)
    if isinstance(passport, media_passport.StaticImagePassport):
        print(get_image_signatures(passport))
