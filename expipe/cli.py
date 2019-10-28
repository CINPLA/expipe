# -*- coding: utf-8 -*-

"""CLI tool."""


#------------------------------------------------------------------------------
# Imports
#------------------------------------------------------------------------------

import os
import os.path as op
import sys
import click
import json
import subprocess
import pathlib
from .cliutils import load_plugins, IPlugin
import expipe as expipe_module

# ------------------------------------------------------------------------------
# CLI tool
# ------------------------------------------------------------------------------

@click.group()
# @click.version_option(version=__version_git__)
@click.help_option('-h', '--help')
@click.pass_context
def expipe(ctx):
    """Add subcommands to 'expipe' with plugins
    using `attach_to_cli()` and the `click` library.

    Note that you can get help from a COMMAND by "expipe COMMAND --help"
    """
    pass


class Default(IPlugin):
    def attach_to_cli(self, cli):
        @cli.command('create')
        @click.argument(
            'project-id', type=click.STRING
        )
        def create(project_id):
            """Create a project."""
            cwd = pathlib.Path.cwd()
            try:
                expipe_module.create_project(path=cwd / project_id)
            except KeyError as e:
                print(str(e))

        @cli.command('init')
        def init():
            """Initialize a project."""
            cwd = pathlib.Path.cwd()
            try:
                expipe_module.create_project(path=cwd, init=True)
            except KeyError as e:
                print(str(e))

        @cli.command('init-lfs')
        def initlfs():
            """Initialize a project."""
            cwd = pathlib.Path.cwd()
            try:
                project = expipe_module.get_project(path=cwd)
            except KeyError as e:
                print(str(e))
                return
            project_path = project._backend.path
            attributes_path = project_path / '.gitattributes'
            with attributes_path.open('w') as f:
                f.write('actions/*/data/**/* filter=lfs diff=lfs merge=lfs -text\n')
                f.write('*.yaml !filter !diff !merge')
            config_path = project_path / '.lfsconfig'
            with config_path.open('w') as f:
                f.write('[lfs]\n')
                f.write('       fetchexclude = *')

        @cli.command('browser')
        @click.option(
            '--run', is_flag=True,
        )
        def browser(run, overwrite):
            """Open a jupyter notebook with project browser, notebook is stored in project root."""
            try:
                project = expipe_module.get_project(path=pathlib.Path.cwd())
            except KeyError as e:
                print(str(e))
                return
            project_root, _ = expipe_module.config._load_local_config(pathlib.Path.cwd())
            fnameout = project_root / 'browser.ipynb'
            utils_path = pathlib.Path(__file__).parent / 'utils'
            fname = utils_path / 'browser-template.ipynb'
            with fname.open('r') as infile:
                notebook = json.load(infile)
            notebook['cells'][1]['source'] = ['project_path = r"{}"'.format(project_root)]
            print('Generating notebook "' + str(fnameout) + '"')
            if not fnameout.exists():
                with fnameout.open('w') as outfile:
                    json.dump(notebook, outfile, sort_keys=True, indent=4)
            if run:
                subprocess.run(['jupyter', 'notebook', str(fnameout)])

        @cli.command('status')
        def status():
            """Print project status."""
            try:
                project = expipe_module.get_project(path=pathlib.Path.cwd())
            except KeyError as e:
                print(str(e))
                return
            for k, v in project.config.items():
                print('{}: {}'.format(k, v))

        @cli.command('list')
        @click.argument(
            'object-type', type=click.Choice(['actions', 'entities', 'modules'])
        )
        def list_stuff(object_type):
            """Print project objects."""
            try:
                project = expipe_module.get_project(path=pathlib.Path.cwd())
            except KeyError as e:
                print(str(e))
                return
            for object in getattr(project, object_type):
                print(object)


        @cli.command('config')
        @click.argument(
            'target', type=click.Choice(['global', 'project', 'local'])
        )
        @click.option(
            '--project-id', type=click.STRING,
        )
        @click.option(
            '--add', '-a', nargs=2, multiple=True
        )
        def set_config(project_id, target, add):
            """Set config info."""
            cwd = pathlib.Path.cwd()
            local_root, _ = expipe_module.config._load_local_config(cwd)
            if local_root is None and target != 'global':
                print(
                    'Unable to load config, move into a project ' +
                    'to configure target: "local" or "project". ' +
                    'To only configure target: "project" give "--project-id".')
                return
            if target == 'local':
                if project_id is not None:
                    raise IOError(
                        'Unable to find path to {}'.format(project_id))
                path = local_root / 'expipe.yaml'
                project_id = local_root.stem
            if target == 'global':
                path = None
            if target == 'project':
                project_id = project_id or local_root.stem
                path = project_id
            config = expipe_module.config._load_config_by_name(path)
            plugin = [a[1] for a in add if a[0] == 'plugin']
            add = [a[1] for a in add if a[0] != 'plugin']
            if len(plugin) > 0:
                current_plugins = config.get('plugins') or []
                plugins = [p for p in plugin] + current_plugins
                add.append(('plugins', list(set(plugins))))
            config.update({a[0]: a[1] for a in add})

            expipe_module.config._dump_config_by_name(path, config)


# ------------------------------------------------------------------------------
# CLI plugins
# ------------------------------------------------------------------------------

def load_cli_plugins(cli, modules=None):
    """Load all plugins and attach them to a CLI object."""
    modules = modules or []
    plugins = load_plugins(modules)
    for plugin in plugins:
        if not hasattr(plugin, 'attach_to_cli'):
            continue
        # NOTE: plugin is a class, so we need to instantiate it.
        try:
            plugin().attach_to_cli(cli)
        except Exception as e:
            print("Error when loading plugin `%s`" % plugin)
            raise e


# Load all plugins when importing this module.

def list_plugins():
    cwd = pathlib.Path.cwd()
    try:
        project = expipe_module.get_project(path=pathlib.Path.cwd())
        config = project.config
    except KeyError as e:
        config = expipe_module.settings
    return config.get('plugins')

load_cli_plugins(expipe, list_plugins())
