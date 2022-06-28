import shlex

import passtry


def test_list_services(capsys):
    args = shlex.split('--list-services')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == 'Services: ssh, http, ftp\n'


def test_one_result(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -P P@55w0rd! -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}\n'


def test_no_results(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -P Password -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == '\n'


def test_uri_precedence(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s http -U user -P P@55w0rd! -p 80+8080 -u ssh://{ssh_host}:{ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}\nssh://user:P@55w0rd!@127.0.0.1:2222\n'


def test_from_file(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Uf {data_dir}/usernames.txt -Pf {data_dir}/passwords.txt -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}\n'


def test_from_file_with_uri(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ftp -Uf {data_dir}/usernames.txt -Pf {data_dir}/passwords.txt -p 21 -u ssh://{ssh_host}:{ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}\n'


def test_split_args(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -P "Password+P@55w0rd!+Passw0rd" -u ssh://{ssh_host}:{ssh_port}')
    passtry.parse_args(args)
    captured = capsys.readouterr()
    assert captured.out == f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}\n'
