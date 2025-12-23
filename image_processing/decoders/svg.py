import re


svg_tag = re.compile(r"<svg[^>]*>")


def is_svg(file_path):
    file = open(file_path, "r")
    try:
        data = file.read()
    except UnicodeDecodeError:
        file.close()
        return False
    file.close()
    return svg_tag.search(data) is not None
