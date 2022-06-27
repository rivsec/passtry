import shlex

import passtry


def test_list_services(capsys):
    args = shlex.split('--list-services')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == 'Services: ssh, http, ftp\n'
