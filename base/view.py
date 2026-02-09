def format_file_size(file_size: int) -> str:
    if file_size >= 2**10:
        if file_size >= 2**20:
            if file_size >= 2**30:
                return f"{file_size / (2 ** 30) :.2f} GiB"
            return f"{file_size / (2 ** 20):.2f} MiB"
        return f"{file_size / (2 ** 10):.2f} KiB"
    return f"{file_size} bytes"
