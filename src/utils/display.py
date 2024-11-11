HEADER_LENGTH = 40

def print_header(title):
    num_dashes = (HEADER_LENGTH - len(title)) / 2
    print(f"\n{'-' * int(num_dashes)} {title} {'-' * int(num_dashes)}")
