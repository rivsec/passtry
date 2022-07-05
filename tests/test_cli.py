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
    assert out == 'Services: ftp, http-basic, https-basic, ssh\n'


def test_one_result(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd! -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_no_results(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S Password -t {ssh_host} -p {ssh_port}')
    passtry.parse_args(args)
    assert passtry.parse_args(args) == []


def test_uri_precedence_service_mismatch(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s http-basic -U user -S P@55w0rd! -p 80+8080 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == []


def test_uri_precedence(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd! -p 80+8080 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_uri_precedence_three_ports(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd! -p 80+8080+8088 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_from_file(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -t {ssh_host} -p {ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_from_file_with_uri(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -p 21 -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_split_args(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S "Password+P@55w0rd!+Passw0rd" -u ssh://{ssh_host}:{ssh_port}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_adding_args_files_combo(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user+user2 -S "Password+P@55w0rd!+Passw0rd" -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -Cf {data_dir}/combo.txt -u ssh://{ssh_host}:{ssh_port}')
    assert set(passtry.parse_args(args)) == {
        f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user2:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user3:PassPass@{ssh_host}:{ssh_port}',
    }


def test_bad_combo(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Cf {data_dir}/bad_combo.txt -u ssh://{ssh_host}')
    with pytest.raises(exceptions.DataError):
        passtry.parse_args(args)


def test_default_port_from_service_as_arg(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S "P@55w0rd!" -t {ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_default_port_from_service_as_uri(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-S "P@55w0rd!" -u ssh://user@{ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_first_match(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-eF -S "Password+P@55w0rd!+password" -u ssh://user+user2@{ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_use_all_args(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user+user2 -eF -S "Password+P@55w0rd!" -t {ssh_host} -p 21 -tN 3 -fN 4 -cT 5 -tW 1 -tR 1 -eF -dF -u ssh://user@{ssh_host}')
    assert passtry.parse_args(args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_mixing_services(ftp_service, http_service, https_service, ssh_service):
    ftp_host, ftp_port = ftp_service
    http_host, http_port = http_service
    https_host, https_port = https_service
    ssh_host, ssh_port = ssh_service
    assert ftp_host == http_host == https_host == ssh_host
    args = shlex.split(f'-s ftp+http-basic+https-basic+ssh -U user+user2 -S "Password+P@55w0rd!" -tN 1 -t {ftp_host} -u http-basic+https-basic://{http_host}/http-basic/')
    assert set(passtry.parse_args(args)) == {
        f"ftp://user:P@55w0rd!@{ftp_host}:{ftp_port}",
        f"ftp://user2:P@55w0rd!@{ftp_host}:{ftp_port}",
        f"http-basic://user:P@55w0rd!@{http_host}:{http_port} -- {{'path': '/http-basic/'}}",
        f"http-basic://user2:P@55w0rd!@{http_host}:{http_port} -- {{'path': '/http-basic/'}}",
        f"https-basic://user:P@55w0rd!@{https_host}:{https_port} -- {{'path': '/http-basic/'}}",
        f"https-basic://user2:P@55w0rd!@{https_host}:{https_port} -- {{'path': '/http-basic/'}}",
        f"ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}",
        f"ssh://user2:P@55w0rd!@{ssh_host}:{ssh_port}",
    }
