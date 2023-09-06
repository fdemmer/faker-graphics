import argparse

from faker_graphics.drawing import PlaceholderPNG


def main(output):
    with PlaceholderPNG(output) as drawing:
        drawing.draw()


parser = argparse.ArgumentParser(prog="faker_graphics")
parser.add_argument("-o", "--output", type=argparse.FileType("wb"), required=True)

main(**vars(parser.parse_args()))
