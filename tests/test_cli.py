import shlex

import pytest

import passtry
from passtry import exceptions


def test_list_services(capsys):
    args = shlex.split('--list-services')
    with pytest.raises(SystemExit) as exc:
        passtry.parse_args(args)
    assert exc.type == SystemExit
    assert exc.value.code == 0
    out, err = capsys.readouterr()
    assert out == 'Services: ftp, http, http-basic, ssh\n'


def test_one_result(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd! -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_no_results(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S Password -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    assert passtry.parse_args(args) == []


def test_uri_precedence(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s http -U user -S P@55w0rd! -p 80+8080 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_uri_precedence_three_ports(capsys, ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s http -U user -S P@55w0rd! -p 80+8080+8088 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_from_file(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -t {ssh_host} -p {ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_from_file_with_uri(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ftp -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -p 21 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_split_args(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S "Password+P@55w0rd!+Passw0rd" -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_adding_args_files_combo(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user+user2 -S "Password+P@55w0rd!+Passw0rd" -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -Cf {data_dir}/combo.txt -u ssh://{ssh_host}:{ssh_port}')
    assert set(passtry.parse_args(args)) == {
        f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user2:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user3:PassPass@{ssh_host}:{ssh_port}',
    }


def test_bad_combo(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Cf {data_dir}/bad_combo.txt -u ssh://{ssh_host}')
    with pytest.raises(exceptions.DataError):
        passtry.parse_args(args)


def test_doesnt_fail_without(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    assert passtry.parse_args([]) == ['Missing argument `services`!']


def test_default_port_from_service_as_arg(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S "P@55w0rd!" -t {ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_default_port_from_service_as_uri(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-S "P@55w0rd!" -u ssh://user@{ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_first_match(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-eF -S "Password+P@55w0rd!+password" -u ssh://user+user2@{ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_use_all_args(capsys, ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ftp -U user+user2 -eF -S "Password+P@55w0rd!" -t {ssh_host} -p 21 -tN 3 -fN 4 -cT 5 -tW 1 -tR 1 -eF -dF -u ssh://user@{ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']
