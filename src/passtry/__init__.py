import argparse
import sys
import logging


logs = logging.getLogger('passtry')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--foo', nargs='?', help='foo help')
    parser.add_argument('bar', nargs='+', help='bar help')


if __name__ == '__main__':
    sys.exit(main())
