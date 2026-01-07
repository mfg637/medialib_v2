def is_avif(file):
    file = open(file, "rb")
    file.seek(4)
    header = file.read(8)
    file.close()
    return header in (b"ftypavif", b"ftypavis")
