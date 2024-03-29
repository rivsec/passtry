import shlex

import pytest

import passtry
from passtry import exceptions


def test_list_services(capsys):
    args = shlex.split('--list-services')
    parser = passtry.get_parser()
    with pytest.raises(SystemExit) as exc:
        passtry.parse_args(parser, args)
    assert exc.type == SystemExit
    assert exc.value.code == 0
    out, err = capsys.readouterr()
    assert out == 'Services: ftp, http-basic, https-basic, ssh\n'


def test_print_output(ssh_service, capsys):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd! -t {ssh_host}')
    parser = passtry.get_parser()
    passtry.parse_args(parser, args)
    out, err = capsys.readouterr()
    assert out == 'ssh://user:P@55w0rd!@127.0.0.1:22\n'


def test_one_result(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd! -t {ssh_host}')
    parser = passtry.get_parser()
    assert passtry.parse_args(parser, args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_usernames_no_passwords(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user,user2 -t {ssh_host}')
    parser = passtry.get_parser()
    with pytest.raises(exceptions.DataError):
        passtry.parse_args(parser, args)


def test_targets_no_services(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-U user,user2 -S Password -t {ssh_host}')
    parser = passtry.get_parser()
    with pytest.raises(exceptions.DataError):
        passtry.parse_args(parser, args)


def test_one_result_set_port(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh:22 -U user -S P@55w0rd! -t {ssh_host}')
    parser = passtry.get_parser()
    assert passtry.parse_args(parser, args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_service_split_extra(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh,ftp,, -U user -S P@55w0rd! -t {ssh_host}')
    parser = passtry.get_parser()
    with pytest.raises(exceptions.ConfigurationError) as exc:
        passtry.parse_args(parser, args)
    assert 'Unknown service' in str(exc.value)


def test_secret_split_extra(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S P@55w0rd!,Password,, -t {ssh_host}')
    parser = passtry.get_parser()
    passtry.parse_args(parser, args)
    assert passtry.parse_args(parser, args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_no_results(ssh_service):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S Password -t {ssh_host}')
    parser = passtry.get_parser()
    assert passtry.parse_args(parser, args) == []


def test_from_file(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -t {ssh_host}')
    parser = passtry.get_parser()
    assert passtry.parse_args(parser, args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_split_args(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S "Password,P@55w0rd!,Passw0rd" -t {ssh_host}')
    parser = passtry.get_parser()
    assert passtry.parse_args(parser, args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_adding_args_files_combo(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-tN 1 -s ssh -U user,user2 -S "Password,P@55w0rd!,Passw0rd" -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -Cf {data_dir}/combo.txt -t {ssh_host}')
    parser = passtry.get_parser()
    assert set(passtry.parse_args(parser, args)) == {
        f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user2:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user3:PassPass@{ssh_host}:{ssh_port}',
    }


def test_bad_combo(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -Cf {data_dir}/bad_combo.txt -t {ssh_host}')
    parser = passtry.get_parser()
    with pytest.raises(exceptions.DataError):
        passtry.parse_args(parser, args)


def test_default_port_from_service_as_arg(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user -S "P@55w0rd!" -t {ssh_host}')
    parser = passtry.get_parser()
    assert passtry.parse_args(parser, args) == [f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}']


def test_first_match(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -eF -U user,user2 -S "Password,P@55w0rd!,password" -t {ssh_host}')
    parser = passtry.get_parser()
    assert len(passtry.parse_args(parser, args)) == 1


def test_use_all_args(ssh_service, data_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-s ssh -U user,user2 -eF -S "Password,P@55w0rd!" -t {ssh_host} -tN 1 -fN 4 -cT 5 -tW 1 -tR 1 -eF -dF -dR -eS -tS 10')
    parser = passtry.get_parser()
    assert len(passtry.parse_args(parser, args)) == 1


def test_mixing_services(ftp_service, http_service, https_service, ssh_service):
    ftp_host, ftp_port = ftp_service
    http_host, http_port = http_service
    https_host, https_port = https_service
    ssh_host, ssh_port = ssh_service
    assert ftp_host == http_host == https_host == ssh_host
    args = shlex.split(f'-s ftp,http-basic,https-basic,ssh -U user,user2 -S "Password,P@55w0rd!" -dF -t {ftp_host} -o http-basic:path=/http-basic/,https-basic:path=/http-basic/')
    parser = passtry.get_parser()
    assert set(passtry.parse_args(parser, args)) == {
        f'ftp://user:P@55w0rd!@{ftp_host}:{ftp_port}',
        f'ftp://user2:P@55w0rd!@{ftp_host}:{ftp_port}',
        f'http://user:P@55w0rd!@{http_host}:{http_port}/http-basic/',
        f'http://user2:P@55w0rd!@{http_host}:{http_port}/http-basic/',
        f'https://user:P@55w0rd!@{https_host}:{https_port}/http-basic/',
        f'https://user2:P@55w0rd!@{https_host}:{https_port}/http-basic/',
        f'ssh://user:P@55w0rd!@{ssh_host}:{ssh_port}',
        f'ssh://user2:P@55w0rd!@{ssh_host}:{ssh_port}',
    }


def test_saving_output(ssh_service, data_dir, tmp_dir):
    ssh_host, ssh_port = ssh_service
    args = shlex.split(f'-tN 1 -s ssh -U user,user2 -S "Password,P@55w0rd!,Passw0rd" -Uf {data_dir}/usernames.txt -Sf {data_dir}/secrets.txt -Cf {data_dir}/combo.txt -t {ssh_host} -Of {tmp_dir}/output.txt')
    parser = passtry.get_parser()
    passtry.parse_args(parser, args)
    with open(tmp_dir + '/output.txt') as fil:
        output = fil.read()
        assert 'user:P@55w0rd!' in output
        assert 'user2:P@55w0rd!' in output
        assert 'user3:PassPass' in output
