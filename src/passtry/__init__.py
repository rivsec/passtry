import argparse
import sys

from passtry import (
    jobs,
    services,
)


def param_split(param):
    return param.split('+')


def parse_args(args):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.print_usage = parser.print_help
    parser.add_argument('-s', '--services', type=param_split, help='Services (separated with `+`) or a file')
    parser.add_argument('-U', '--usernames', type=param_split, help='Usernames (separated with `+`) or a file')
    parser.add_argument('-P', '--passwords', type=param_split, help='Passwords (separated with `+`) or a file')
    parser.add_argument('-t', '--targets', type=param_split, help='Targets (separated with `+`) or a file')
    parser.add_argument('-p', '--ports', type=param_split, help='Ports (separated with `+`) or a file')
    parser.add_argument('-u', '--uri', nargs='?', help='URI connection string (takes precedence over other arguments)')
    parser.add_argument('--list-services', action='store_true', help='Show available services')
    parsed = parser.parse_args(args)
    if parsed.list_services:
        print('Services: ' + ', '.join((services.Service.registry.keys())))
    else:
        job = jobs.Job()
        final_args = job.normalize(parsed.services, parsed.usernames, parsed.passwords, parsed.targets, parsed.ports)
        if parsed.uri:
            normal_uri = job.normalize(*job.split(parsed.uri))
            job.merge(normal_uri, final_args)
        job.consume(final_args)
        job.start()
        output = '\n'.join(
            [job.prettify(result) for result in job.results if result]
        )
        print(output)


def main():
    parse_args(sys.argv[1:])


if __name__ == '__main__':
    sys.exit(main())
