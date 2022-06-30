import argparse
import sys

from passtry import (
    jobs,
    services,
)


class ArgSplitAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string):
        setattr(namespace, self.dest, values.split('+'))


def read_args_or_file(parsed, name):
    result = None
    if hasattr(parsed, name):
        result = getattr(parsed, name)
    elif hasattr(parsed, name + '_file'):
        with getattr(parsed, name + '_file') as fil:
            result = [line.strip() for line in fil]
    return result


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.print_usage = parser.print_help
    group_services = parser.add_mutually_exclusive_group()
    group_usernames = parser.add_mutually_exclusive_group()
    group_passwords = parser.add_mutually_exclusive_group()
    group_targets = parser.add_mutually_exclusive_group()
    group_ports = parser.add_mutually_exclusive_group()
    group_services.add_argument('-s', '--services', action=ArgSplitAction, default=argparse.SUPPRESS, help='Services (`+` separated)')
    group_services.add_argument('-sf', '--services-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Services file')
    group_usernames.add_argument('-U', '--usernames', action=ArgSplitAction, default=argparse.SUPPRESS, help='Usernames (`+` separated)')
    group_usernames.add_argument('-Uf', '--usernames-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Usernames file')
    group_passwords.add_argument('-P', '--passwords', action=ArgSplitAction, default=argparse.SUPPRESS, help='Passwords (`+` separated)')
    group_passwords.add_argument('-Pf', '--passwords-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Passwords file')
    group_targets.add_argument('-t', '--targets', action=ArgSplitAction, default=argparse.SUPPRESS, help='Targets (`+` separated)')
    group_targets.add_argument('-tf', '--targets-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Targets file')
    group_ports.add_argument('-p', '--ports', action=ArgSplitAction, default=argparse.SUPPRESS, help='Ports (`+` separated)')
    group_ports.add_argument('-pf', '--ports-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Ports file')
    parser.add_argument('-jW', '--jobs-workers', default=jobs.DEFAULT_WORKERS_NO, help='Number of worker threads')
    parser.add_argument('-jF', '--jobs-failed', default=jobs.DEFAULT_MAX_FAILED, help='Maximum number of failed connections')
    parser.add_argument('-u', '--uri', help='URI connection string (takes precedence over other arguments)')
    parser.add_argument('--list-services', action='store_true', help='Show available services')
    parsed = parser.parse_args(args)
    if parsed.list_services:
        return ['Services: ' + ', '.join((services.Service.registry.keys()))]
    job = jobs.Job(workers_no=parsed.jobs_workers, max_failed=parsed.jobs_failed)
    services_args = read_args_or_file(parsed, 'services')
    usernames_args = read_args_or_file(parsed, 'usernames')
    passwords_args = read_args_or_file(parsed, 'passwords')
    targets_args = read_args_or_file(parsed, 'targets')
    ports_args = read_args_or_file(parsed, 'ports')
    final_args = job.normalize(services_args, usernames_args, passwords_args, targets_args, ports_args)
    if parsed.uri:
        normal_uri = job.normalize(*job.split(parsed.uri))
        job.merge(normal_uri, final_args)

    first_row = final_args[0]
    for idx, val in enumerate(first_row):
        if val is None:
            missing = jobs.TASK_STRUCT[idx]
            if missing == 'ports':
                service = first_row[jobs.TASK_STRUCT_BY_NAME['services']]
                job.merge(
                    [[None, None, None, None, services.Service.registry[service].port]],
                    final_args
                )
                continue
            return [f'Missing argument `{jobs.TASK_STRUCT[idx]}`!']
    job.start(final_args)
    return job.output()


def main():
    results = parse_args(sys.argv[1:])
    print('\n'.join(results))


if __name__ == '__main__':
    sys.exit(main())
