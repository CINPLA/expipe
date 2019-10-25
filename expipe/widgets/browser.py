import expipe
import pathlib
import uuid
import json
from collections import OrderedDict
from . import display
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError as e:
    HAS_PANDAS = False
try:
    import IPython.display as ipd
    import ipywidgets
    HAS_IPYW = True
except ImportError as e:
    HAS_IPYW = False
    IPYW_ERR = e
try:
    from tqdm import tqdm
except:
    def tqdm(x, **kw):
        return x

class Browser:
    def __init__(self, project_path=None):
        if not HAS_IPYW:
            raise IPYW_ERR
        project_path = project_path or pathlib.Path.cwd()
        self.project_path = pathlib.Path(project_path)
        self.project = expipe.require_project(self.project_path)

        self.action_attributes = OrderedDict([
            ('tags', {}),
            ('location', {}),
            ('users', {}),
            ('entities', {}),
            ('datetime', {}),
        ])
        for action in tqdm(self.project.actions, desc='Indexing project'):
            for key, container in self.action_attributes.items():
                values = getattr(self.project.actions[action], key)
                values = values if isinstance(values, expipe.core.PropertyList) else [values]
                for attr in values:
                    attr = str(attr)
                    if attr in container:
                        container[attr]['actions'].append(action)
                    else:
                        container[attr] = {
                            'actions': [action],
                            'state': False
                        }

    def _export_view(self):
        actions_list = list(self.project.actions.keys())
        actions_visible = ipywidgets.SelectMultiple(
            options=actions_list,
            disabled=False,
            layout={'height': '500px'}
        )

        checkbox_group = {}

        def on_checkbox_change(change):
            if change['name'] == 'value':
                ch = change['owner']
                group = checkbox_group[ch]
                self.action_attributes[group][ch.description]['state'] = ch.value
                actions = [set(g['actions']) for attr in self.action_attributes.values() for g in attr.values() if g['state']]
                states = [g['state'] for attr in self.action_attributes.values() for g in attr.values()]

                if not any(states):
                    actions_visible.options = self.project.actions.keys()
                else:
                    actions = actions + [set(actions_list)]
                    actions = set.intersection(*actions)
                    actions_visible.options = actions


        export_actions_name = ipywidgets.Text(
            placeholder='Action name for export')

        export_csv_name = ipywidgets.Text(
            placeholder='File name for export')

        def on_export_actions(change):
            if not HAS_PANDAS:
                print('Unable to export to csv without pandas.')
                return
            if export_actions_name.value == '':
                print('You have to give a name to export actions list.') # TODO show text in widget
                return
            actions = actions_visible.value
            if len(actions) == 0:
                print('You have to select from the list, "ctrl+a" for all') # TODO show text in widget
                return
            action_for_export = self.project.require_action(export_actions_name.value)
            df = []
            tags = []
            for action_name in actions:
                a = self.project.actions[action_name]
                v = {
                    'action': action_name,
                    'users': '//'.join(a.users),
                    'entities': '//'.join(a.entities),
                    'location': a.location,
                    'datetime': a.datetime
                }
                for tag in a.tags:
                    v[tag] = True
                    tags.append(tag)
                df.append(v)
            csv_name = export_csv_name.value
            csv_name = csv_name.replace('.csv', '')
            action_for_export.data[csv_name] = csv_name + '.csv'
            df = pd.DataFrame(df)
            for tag in set(tags):
                df[tag].fillna(False, inplace=True)
            df.to_csv(action_for_export.data_path(csv_name), index=False)
            print(
                'Actions successfully exported.\n'
                'To load use "pd.read_csv(project.actions["{}"].data_path("{}"))"'.format(export_actions_name.value, csv_name))


        export_actions_button = ipywidgets.Button(
            description='Export to csv',
            disabled=False,
            button_style='',
        )
        export_actions_button.on_click(on_export_actions)

        checkbox_groups = []
        checkbox_group_names = []
        for name, value in self.action_attributes.items():
            temp = []
            for key in value:
                ch = ipywidgets.Checkbox(
                    value=False,
                    description=key,
                    disabled=False
                )
                ch.observe(on_checkbox_change, names='value')
                temp.append(ch)
                checkbox_group[ch] = name
            box = ipywidgets.VBox(temp)
            checkbox_groups.append(box)
            checkbox_group_names.append(name)

        action_attributes = ipywidgets.Accordion(
            checkbox_groups, layout={'height': '500px'})
        for i, name in enumerate(checkbox_group_names):
            action_attributes.set_title(i, name.capitalize())

        actions_select = ipywidgets.VBox(
            [actions_visible, export_actions_name, export_csv_name, export_actions_button])
        return ipywidgets.HBox([action_attributes, actions_select])

    def _action_modules_view(self):
        return display.objects_and_modules_view(self.project.actions)

    def _action_messages_view(self):
        return display.objects_and_messages_view(self.project.actions)

    def _entity_modules_view(self):
        return display.objects_and_modules_view(self.project.entities)

    def _entity_messages_view(self):
        return display.objects_and_messages_view(self.project.entities)

    def _project_modules_view(self):
        return display.modules_view(self.project)

    def _templates_view(self):
        return display.templates_view(self.project)

    def _action_attributes_view(self):
        return display.actions_view(self.project)

    def _entities_view(self):
        return display.entities_view(self.project)

    def display(self):
        # Actions tab
        actions_tab_tab_titles = ['Export', 'Attributes', 'Modules', 'Messages']
        actions_tab = ipywidgets.Tab()
        actions_tab.children = [
            self._export_view(), self._action_attributes_view(),
            self._action_modules_view(), self._action_messages_view()
        ]
        for i, title in enumerate(actions_tab_tab_titles):
            actions_tab.set_title(i, title)

        # Entities tab
        entities_tab_tab_titles = ['Attributes', 'Modules', 'Messages']
        entities_tab = ipywidgets.Tab()
        entities_tab.children = [
            self._entities_view(),
            self._entity_modules_view(), self._entity_messages_view()
        ]
        for i, title in enumerate(entities_tab_tab_titles):
            entities_tab.set_title(i, title)

        tab_titles = ['Actions', 'Modules', 'Templates', 'Entities']
        tab = ipywidgets.Tab()
        tab.children = [
            actions_tab, self._project_modules_view(), self._templates_view(),
            entities_tab
        ]
        for i, title in enumerate(tab_titles):
            tab.set_title(i, title)
        ipd.clear_output()
        ipd.display(tab)
