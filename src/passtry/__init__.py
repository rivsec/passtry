import argparse
import sys

from passtry import (
    exceptions,
    jobs,
    services,
)


class ArgSplitAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string):
        setattr(namespace, self.dest, set(values.split('+')))


def read_file(parsed, file_attr):
    fil = getattr(parsed, file_attr, tuple())
    return {line.strip() for line in fil}


def read_combo(parsed, file_attr, delimiter=None):
    fil = getattr(parsed, file_attr, tuple())
    result = list()
    try:
        for line in fil:
            username, password = line.strip().split(delimiter)
            result.append([None, username, password, None, None])
    except ValueError:
        raise exceptions.DataError('Error occured while processing combo file')
    return result


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.print_usage = parser.print_help
    parser.add_argument('-s', '--services', action=ArgSplitAction, default=set(), help='Services (`+` separated)')
    parser.add_argument('-sf', '--services-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Services file')
    parser.add_argument('-U', '--usernames', action=ArgSplitAction, default=set(), help='Usernames (`+` separated)')
    parser.add_argument('-Uf', '--usernames-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Usernames file')
    parser.add_argument('-P', '--passwords', action=ArgSplitAction, default=set(), help='Passwords (`+` separated)')
    parser.add_argument('-Pf', '--passwords-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Passwords file')
    parser.add_argument('-Cf', '--combo-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Combo file')
    parser.add_argument('-Cd', '--combo-delimiter', default=':', help='Combo file delimiter')
    parser.add_argument('-t', '--targets', action=ArgSplitAction, default=set(), help='Targets (`+` separated)')
    parser.add_argument('-tf', '--targets-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Targets file')
    parser.add_argument('-p', '--ports', action=ArgSplitAction, default=set(), help='Ports (`+` separated)')
    parser.add_argument('-pf', '--ports-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Ports file')
    parser.add_argument('-tN', '--threads-number', type=int, default=jobs.THREADS_NUMBER, help='Number of worker threads')
    parser.add_argument('-fN', '--failed-number', type=int, default=jobs.FAILED_NUMBER, help='Maximum number of failed connections')
    parser.add_argument('-cT', '--connections-timeout', type=int, default=jobs.CONNECTIONS_TIMEOUT, help='Connections timeout')
    parser.add_argument('-tW', '--time-wait', type=float, default=jobs.TIME_WAIT, help='Time to wait between connections')
    parser.add_argument('-tR', '--time-randomize', type=int, default=jobs.TIME_RANDOMIZE, help='Randomized time in seconds to add to wait time (`--time-wait`)')
    parser.add_argument('-u', '--uri', help='URI connection string (takes precedence over other arguments)')
    parser.add_argument('--list-services', action='store_true', help='Show available services')
    parser.add_argument('-eF', '--enable-first', default=False, action='store_true', help='Abort processing on first match')
    parser.add_argument('-dF', '--disable-failures', default=True, action='store_false', help='Disable counter for failed connections')
    parsed = parser.parse_args(args)
    if parsed.list_services:
        return ['Services: ' + ', '.join((services.Service.registry.keys()))]
    job = jobs.Job(
        threads_number=parsed.threads_number,
        failed_number=parsed.failed_number,
        connections_timeout=parsed.connections_timeout,
        time_wait=parsed.time_wait,
        time_randomize=parsed.time_randomize,
        abort_match=parsed.enable_first,
        watch_failures=parsed.disable_failures
    )
    services_set = read_file(parsed, 'services_file').union(parsed.services)
    usernames_set = read_file(parsed, 'usernames_file').union(parsed.usernames)
    passwords_set = read_file(parsed, 'passwords_file').union(parsed.passwords)
    targets_set = read_file(parsed, 'targets_file').union(parsed.targets)
    ports_set = read_file(parsed, 'ports_file').union(parsed.ports)
    final_args = job.combine(services_set, usernames_set, passwords_set, targets_set, ports_set)
    combo_args = read_combo(parsed, 'combo_file', parsed.combo_delimiter)
    final_args.extend(combo_args)
    if parsed.uri:
        normal_uri = job.combine(*job.split(parsed.uri))
        # NOTE: If URI was defined and ports is None use the URI schema value for given class
        uri_ports = normal_uri[0][jobs.TASK_STRUCT_BY_NAME['ports']]
        uri_services = normal_uri[0][jobs.TASK_STRUCT_BY_NAME['services']]
        if uri_ports is None:
            normal_uri[0][jobs.TASK_STRUCT_BY_NAME['ports']] = services.Service.registry[uri_services].port
        final_args = job.merge(normal_uri, final_args)
    first_row = final_args[0]
    for idx, val in enumerate(first_row):
        if val is None:
            missing = jobs.TASK_STRUCT[idx]
            # NOTE: Now repeat the operation of replacing ports for each task, if URI was not defined this should be still None
            if missing == 'ports':
                service = first_row[jobs.TASK_STRUCT_BY_NAME['services']]
                final_args = job.merge(
                    [[None, None, None, None, services.Service.registry[service].port]],
                    final_args
                )
                continue
            return [f'Missing argument `{jobs.TASK_STRUCT[idx]}`!']
    job.start(final_args)
    return job.output()


def main():
    try:
        results = parse_args(sys.argv[1:])
    except (exceptions.ConfigurationError, exceptions.DataError) as exc:
        results = [exc.args[0]]
    print('\n'.join(results))


if __name__ == '__main__':
    sys.exit(main())
