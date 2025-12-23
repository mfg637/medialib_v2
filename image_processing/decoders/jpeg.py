def is_JPEG(file_path):
    file = open(file_path, "rb")
    header = file.read(2)
    file.close()
    return header == b"\xff\xd8"
