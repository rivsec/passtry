import argparse
import sys

from passtry import (
    exceptions,
    jobs,
    logs,
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
            username, secret = line.strip().split(delimiter)
            result.append([None, username, secret, None, None])
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
    parser.add_argument('-S', '--secrets', action=ArgSplitAction, default=set(), help='Secrets (`+` separated)')
    parser.add_argument('-Sf', '--secrets-file', type=argparse.FileType('r'), default=argparse.SUPPRESS, help='Secrets file')
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
    parser.add_argument('-eF', '--enable-first-match', default=False, action='store_true', help='Abort processing on first match')
    parser.add_argument('-dF', '--disable-failures', default=True, action='store_false', help='Disable counter for failed connections')
    parser.add_argument('-eS', '--enable-statistics', default=False, action='store_true', help='Show statistics (attempts, failures, matches)')
    parser.add_argument('-tS', '--time-statistics', type=int, default=jobs.TIME_STATISTICS, help='Statistics interval')
    parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logs.logging.DEBUG, default=logs.logging.INFO, help='Enable debug mode (verbose output)')
    parsed = parser.parse_args(args)
    logs.init(parsed.loglevel)
    if parsed.list_services:
        print('Services: ' + ', '.join(sorted(services.Service.registry.keys())))
        sys.exit(0)

    logs.info('Preparing...')
    job = jobs.Job(
        threads_number=parsed.threads_number,
        failed_number=parsed.failed_number,
        connections_timeout=parsed.connections_timeout,
        time_wait=parsed.time_wait,
        time_randomize=parsed.time_randomize,
        first_match=parsed.enable_first_match,
        watch_failures=parsed.disable_failures,
        enable_statistics=parsed.enable_statistics,
        time_statistics=parsed.time_statistics
    )

    # NOTE: Read data from files.
    services_set = read_file(parsed, 'services_file').union(parsed.services)
    usernames_set = read_file(parsed, 'usernames_file').union(parsed.usernames)
    secrets_set = read_file(parsed, 'secrets_file').union(parsed.secrets)
    targets_set = read_file(parsed, 'targets_file').union(parsed.targets)
    ports_set = read_file(parsed, 'ports_file').union(parsed.ports)

    # NOTE: Now generate combinations.
    tasks = job.combine(services_set, usernames_set, secrets_set, targets_set, ports_set, None)

    # NOTE: Combine current set of tasks with data from a combo file.
    combo_args = read_combo(parsed, 'combo_file', parsed.combo_delimiter)
    if combo_args:
        tasks.extend(combo_args)

    # NOTE: If URI was provided, extract the data and use `ports` value for all tasks.
    if parsed.uri:
        # NOTE: Assuming URI argument creates a single row.
        normal_uri = job.combine(*job.split(parsed.uri))
        # NOTE: If URI was defined and ports is None use the URI schema value for given class.
        uri_ports = normal_uri[0][jobs.TASK_STRUCT_BY_NAME['ports']]
        uri_services = normal_uri[0][jobs.TASK_STRUCT_BY_NAME['services']]
        if uri_ports is None:
            normal_uri[0][jobs.TASK_STRUCT_BY_NAME['ports']] = services.Service.registry[uri_services].port
        tasks = job.replace(normal_uri, tasks)
    first_row = tasks[0]

    # NOTE: In case URI was not provided and `ports` still missing, use `services` for reference.
    for idx, val in enumerate(first_row):
        if val is None:
            missing = jobs.TASK_STRUCT[idx]
            if missing == 'ports':
                service = first_row[jobs.TASK_STRUCT_BY_NAME['services']]
                tasks = job.replace(
                    [[None, None, None, None, services.Service.registry[service].port, None]],
                    tasks
                )
                continue
            elif missing == 'options':
                # NOTE: It is currently not required for all tasks to have `options` defined, saves some memory.
                pass
            else:
                return [f'Missing argument `{missing}`!']

    logs.info(f'Executing {len(tasks)} tasks')
    try:
        job.start(tasks)
    except KeyboardInterrupt:
        logs.info(f'Exiting')
    return job.output()


def main():
    try:
        results = parse_args(sys.argv[1:])
    except (exceptions.ConfigurationError, exceptions.DataError) as exc:
        results = [exc.args[0]]
    if results:
        logs.info('Discovered the following credentials:\n' + '\n'.join(results))
    else:
        logs.info('No credentials discovered')


if __name__ == '__main__':
    sys.exit(main())
