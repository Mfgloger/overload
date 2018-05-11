# parses help files of OpsUtils and passes them to


def open_help(help_fh):
    # think how to refactor so the lines don't break mid-word
    # in display
    help_fh = r'./help/' + help_fh
    help_lines = []

    with open(help_fh, 'r') as file:
        for line in file:
            help_lines.append(line)
    return help_lines
