from click.testing import CliRunner
import pytest
import expipe
from expipe.cli import expipe
from pathlib import Path
import os, shutil


def test_cli():
    runner = CliRunner()
    result = runner.invoke(expipe, ["--help"])
    assert result.exit_code == 0
    result = runner.invoke(expipe, ["create",  "my_project"])
    assert result.exit_code == 0
    assert Path('my_project').is_dir()
    result = runner.invoke(expipe, ["config", "--help"])
    assert result.exit_code == 0
    os.mkdir("my_other_project")
    os.chdir('my_other_project')
    print(os.getcwd())
    result = runner.invoke(expipe, ["init"])
    assert result.exit_code == 0
    result = runner.invoke(expipe, ["init-lfs"])
    assert result.exit_code == 0
    result = runner.invoke(expipe, ["list", "actions"])
    assert result.exit_code == 0
    result = runner.invoke(expipe, ["list", "entities"])
    assert result.exit_code == 0
    result = runner.invoke(expipe, ["list", "modules"])
    assert result.exit_code == 0
    result = runner.invoke(expipe, ["status"])
    assert result.exit_code == 0
    os.chdir('..')
    shutil.rmtree('my_project')
    shutil.rmtree('my_other_project')