import shlex

import passtry


def test_list_services(capsys):
    args = shlex.split('--list-services')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == 'Services: ssh, http, ftp\n'


def test_one_result(capsys, ssh_service):
    ssh_ip, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -P P@55w0rd! -t {ssh_ip} -p {ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_ip}:{ssh_port}\n'


def test_no_results(capsys, ssh_service):
    ssh_ip, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -P Password -t {ssh_ip} -p {ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == '\n'


def test_uri_precedence(capsys, ssh_service):
    ssh_ip, ssh_port = ssh_service
    args = shlex.split(f'-s http -U user -P P@55w0rd! -p 80+8080 -u ssh://{ssh_ip}:{ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_ip}:{ssh_port}\n'
