import argparse
import sys

from passtry import (
    jobs,
    services,
)


def parse_args(args):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.print_usage = parser.print_help
    parser.add_argument('-s', '--services', nargs='+', default=argparse.SUPPRESS, help='Comma separated services or a file')
    parser.add_argument('-U', '--usernames', nargs='+', default=argparse.SUPPRESS, help='Comma separated usernames or a file')
    parser.add_argument('-P', '--passwords', nargs='+', default=argparse.SUPPRESS, help='Comma separated passwords or a file')
    parser.add_argument('-t', '--targets', nargs='+', default=argparse.SUPPRESS, help='Comma separated targets or a file')
    parser.add_argument('-p', '--ports', nargs='+', default=argparse.SUPPRESS, help='Comma separated ports or a file')
    parser.add_argument('--list-services', action='store_true', help='Show available services')
    parser.add_argument('URI', nargs='?', default=argparse.SUPPRESS, help='URI connection string (takes precedence over other arguments)')
    parsed = parser.parse_args(args)
    if parsed.list_services:
        print('Services: ' + ', '.join((services.Service.registry.keys())))
    else:
        job = jobs.Job()
        tasks = job.normalize(parsed.services, parsed.usernames, parsed.passwords, parsed.targets, parsed.ports)
        job.consume(tasks)
        job.start()
        output = '\n'.join(
            [job.prettify(result) for result in job.results if result]
        )
        print(output)


def main():
    parse_args(sys.argv[1:])


if __name__ == '__main__':
    sys.exit(main())
