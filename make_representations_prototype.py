import argparse
import pathlib
from image_processing.services import analysis, media_passport
from image_processing.services.representations import (
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
