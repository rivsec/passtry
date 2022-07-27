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
        setattr(namespace, self.dest, values.split(','))


def get_parser():
    parser = argparse.ArgumentParser(
        prog='passtry',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.print_usage = parser.print_help
    parser.add_argument('-s', '--services', action=ArgSplitAction, default=list(), help='Services (`,` separated, e.g. `ssh` or `ssh:2222`)')
    parser.add_argument('-sf', '--services-file', type=argparse.FileType('r'), default=list(), help='Services file')
    parser.add_argument('-U', '--usernames', action=ArgSplitAction, default=list(), help='Usernames (`,` separated)')
    parser.add_argument('-Uf', '--usernames-file', type=argparse.FileType('r'), default=list(), help='Usernames file')
    parser.add_argument('-S', '--secrets', action=ArgSplitAction, default=list(), help='Secrets (`,` separated)')
    parser.add_argument('-Sf', '--secrets-file', type=argparse.FileType('r'), default=list(), help='Secrets file')
    parser.add_argument('-Cf', '--combo-file', type=argparse.FileType('r'), default=list(), help='Combo file')
    parser.add_argument('-Cd', '--combo-delimiter', default=':', help='Combo file delimiter')
    parser.add_argument('-t', '--targets', action=ArgSplitAction, default=list(), help='Targets (`,` separated, e.g. `example.com` or `example.com:22`)')
    parser.add_argument('-tf', '--targets-file', type=argparse.FileType('r'), default=list(), help='Targets file')
    parser.add_argument('-o', '--options', action=ArgSplitAction, default=dict(), help='Options (`,` separated, e.g. `http-basic:path=/secret-path/`)')
    parser.add_argument('-tN', '--threads-number', type=int, default=jobs.THREADS_NUMBER, help='Number of worker threads')
    parser.add_argument('-fN', '--failed-number', type=int, default=jobs.FAILED_NUMBER, help='Maximum number of failed connections')
    parser.add_argument('-cT', '--connections-timeout', type=int, default=jobs.CONNECTIONS_TIMEOUT, help='Connections timeout')
    parser.add_argument('-tW', '--time-wait', type=float, default=jobs.TIME_WAIT, help='Time to wait between connections')
    parser.add_argument('-tR', '--time-randomize', type=int, default=jobs.TIME_RANDOMIZE, help='Randomized time in seconds to add to wait time (`--time-wait`)')
    parser.add_argument('--list-services', action='store_true', help='Show available services')
    parser.add_argument('-eF', '--enable-first-match', default=False, action='store_true', help='Abort processing on first match')
    parser.add_argument('-dF', '--disable-failures', default=True, action='store_false', help='Disable counter for failed connections')
    parser.add_argument('-dR', '--disable-retry', default=True, action='store_false', help='Disable retry for failed connections')
    parser.add_argument('-eS', '--enable-statistics', default=False, action='store_true', help='Show statistics (attempts, successful/failed connections, matches)')
    parser.add_argument('-tS', '--time-statistics', type=int, default=jobs.TIME_STATISTICS, help='Statistics interval')
    parser.add_argument('-Of', '--output-file', default=None, help='Save results to a file')
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logs.logging.DEBUG, default=logs.logging.INFO, help='Enable debug mode (verbose output)')
    verbosity.add_argument('-q', '--quiet', action='store_const', dest='loglevel', const=logs.logging.NOTSET, default=logs.logging.INFO, help='Enable quiet mode')
    return parser


def parse_args(parser, args):
    parsed = parser.parse_args(args)
    logs.init(parsed.loglevel)
    if parsed.list_services:
        print('Services: ' + ', '.join(sorted(services.Service.registry.keys())))
        sys.exit(0)

    logs.logger.info('Preparing')
    job = jobs.Job(
        threads_number=parsed.threads_number,
        failed_number=parsed.failed_number,
        connections_timeout=parsed.connections_timeout,
        time_wait=parsed.time_wait,
        time_randomize=parsed.time_randomize,
        first_match=parsed.enable_first_match,
        watch_failures=parsed.disable_failures,
        retry_failed=parsed.disable_retry,
        enable_statistics=parsed.enable_statistics,
        time_statistics=parsed.time_statistics,
        output_file=parsed.output_file
    )

    data_services = list()
    data_usernames = list()
    data_secrets = list()
    data_targets = list()
    data_options = dict()

    # NOTE: Read data from files and CLI arguments
    logs.logger.debug('Reading data from files and CLI arguments')

    logs.logger.debug('Reading `services`')
    data_services.extend(job.read_file(parsed.services_file))
    data_services.extend(ele for ele in parsed.services if ele not in data_services)

    logs.logger.debug('Reading `usernames`')
    data_usernames.extend(job.read_file(parsed.usernames_file))
    data_usernames.extend(ele for ele in parsed.usernames if ele not in data_usernames)

    logs.logger.debug('Reading `secrets`')
    data_secrets.extend(job.read_file(parsed.secrets_file))
    data_secrets.extend(ele for ele in parsed.secrets if ele not in data_secrets)

    logs.logger.debug('Reading `targets`')
    data_targets.extend(job.read_file(parsed.targets_file))
    data_targets.extend(ele for ele in parsed.targets if ele not in data_targets)

    logs.logger.debug('Reading combo file if present')
    data_combos = job.read_combo(parsed.combo_file, parsed.combo_delimiter)

    if not data_services:
        raise exceptions.DataError('Missing `services` data! (-s/-sf)')

    if not data_usernames and data_secrets:
        raise exceptions.DataError('Missing `usernames` data! (-U/-Uf)')

    if not data_secrets and data_usernames:
        raise exceptions.DataError('Missing `secrets` data! (-S/-Sf)')

    if not data_targets:
        raise exceptions.DataError('Missing `targets` data! (-t/-tf)')

    if not data_usernames and not (data_secrets or data_combos):
        raise exceptions.DataError('Nothing to do!')

    for opt in parsed.options:
        try:
            service, params = opt.split(':')
        except ValueError:
            raise exceptions.ConfigurationError(f'Invalid `options` argument: `{opt}`')
        attr, value = params.split('=')
        data_options[service] = {attr: value}

    job.start(data_services, data_targets, data_usernames, data_secrets, data_options, data_combos)
    return job.output


def main():
    parser = get_parser()
    try:
        results = parse_args(parser, sys.argv[1:])
    except (exceptions.ConfigurationError, exceptions.DataError) as exc:
        logs.logger.error(exc)
        parser.error(exc)
    except KeyboardInterrupt:
        logs.logger.info(f'Exiting')
    else:
        if not results:
            logs.logger.info('No credentials discovered')


if __name__ == '__main__':
    sys.exit(main())
