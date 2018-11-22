import ipywidgets
import expipe
import pathlib
import uuid
import IPython.display as ipd
import json
from collections import OrderedDict
from . import display


class Browser:
    def __init__(self, project_path):
        self.project_path = pathlib.Path(project_path)
        self.project = expipe.require_project(self.project_path)

        self.action_attributes = OrderedDict([
            ('tags', {}),
            ('location', {}),
            ('users', {}),
            ('entities', {}),
            ('datetime', {}),
        ])
        for action in self.project.actions:
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

    def _actions_view(self):
        actions_list = list(self.project.actions.keys())
        actions_visible = ipywidgets.SelectMultiple(
            options=actions_list,
            disabled=False
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


        export_actions_name = ipywidgets.Text()

        def on_export_actions(change):
            if export_actions_name.value == '':
                print('You have to give a name to export actions list.') # TODO show text in widget
                return
            actions = actions_visible.value
            if len(actions) == 0:
                print('You have to select from the list, "ctrl+a" for all') # TODO show text in widget
            action = self.project.create_action(export_actions_name.value)
            actions_select_module = action.create_module(
                'actions_to_include', contents={'actions': actions})


        export_actions_button = ipywidgets.Button(
            description='Export actions',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
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
            box = ipywidgets.VBox(temp, layout={'overflow': 'scroll'})
            checkbox_groups.append(box)
            checkbox_group_names.append(name)

        action_attributes = ipywidgets.Accordion(checkbox_groups)
        for i, name in enumerate(checkbox_group_names):
            action_attributes.set_title(i, name.capitalize())
        actions_visible.layout = {'overflow': 'scroll', 'height': '750px'} #TODO figure out how to automatically scale list height

        actions_select = ipywidgets.VBox([actions_visible, export_actions_name, export_actions_button])
        return ipywidgets.HBox([action_attributes, actions_select])

    def _action_modules_view(self):
        actions_list = list(self.project.actions.keys())
        if len(actions_list) == 0:
            actions_list_empty = True
            modules_list_empty = True
            action_first_modules = []
        else:
            actions_list_empty = False
            action_first = self.project.actions[actions_list[0]]
            action_first_modules = list(action_first.modules.keys())
            if len(action_first_modules) == 0:
                modules_list_empty = True
            else:
                modules_list_empty = False
                module_first = action_first.modules[action_first_modules[0]]

        actions_select = ipywidgets.Select(
            options=actions_list,
            disabled=False,
            value=None if actions_list_empty else actions_list[0]
        )
        modules_list = ipywidgets.Select(
            options=action_first_modules,
            disabled=False,
            value=None if modules_list_empty else action_first_modules[0]
        )
        out = ipywidgets.Output()
        if not modules_list_empty:
            with out:
                display.display_dict_html(module_first.contents)

        curr_state = {'action': action_first}

        def on_select_action(change):
            if change['name'] == 'value':
                action = self.project.actions[change['owner'].value]
                curr_state['action'] = action
                modules_list.options = action.modules.keys()

        def on_select_module(change):
            if change['name'] == 'value':
                module = curr_state['action'].modules[change['owner'].value]
                with out:
                    display.display_dict_html(module.contents)

        actions_select.observe(on_select_action, names='value')
        modules_list.observe(on_select_module, names='value')

        return ipywidgets.HBox([actions_select, modules_list, out], style={'overflow': 'scroll'})

    def _action_messages_view(self):
        actions_list = list(self.project.actions.keys())
        if len(actions_list) == 0:
            actions_list_empty = True
            messages_list_empty = True
            action_first_messages = []
        else:
            actions_list_empty = False
            action_first = self.project.actions[actions_list[0]]
            action_first_messages = list(action_first.messages.keys())
            if len(action_first_messages) == 0:
                messages_list_empty = True
            else:
                messages_list_empty = False
                message_first = action_first.messages[action_first_messages[0]]

        actions_select = ipywidgets.Select(
            options=actions_list,
            disabled=False,
            value=None if actions_list_empty else actions_list[0]
        )
        messages_list = ipywidgets.Select(
            options=action_first_messages,
            disabled=False,
            value=None if messages_list_empty else action_first_messages[0]
        )
        out = ipywidgets.Output()
        if not messages_list_empty:
            with out:
                display.display_dict_html(message_first.contents)

        curr_state = {'action': action_first}

        def on_select_action(change):
            if change['name'] == 'value':
                action = self.project.actions[change['owner'].value]
                curr_state['action'] = action
                messages_list.options = action.messages.keys()

        def on_select_message(change):
            if change['name'] == 'value':
                message = curr_state['action'].messages[change['owner'].value]
                with out:
                    display.display_dict_html(message.contents)

        actions_select.observe(on_select_action, names='value')
        messages_list.observe(on_select_message, names='value')

        return ipywidgets.HBox([actions_select, messages_list, out], style={'overflow': 'scroll'})

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
            self._actions_view(), self._action_attributes_view(),
            self._action_modules_view(), self._action_messages_view()
        ]
        for i, title in enumerate(actions_tab_tab_titles):
            actions_tab.set_title(i, title)

        tab_titles = ['Actions', 'Modules', 'Templates', 'Entities']
        tab = ipywidgets.Tab()
        tab.children = [
            actions_tab, self._project_modules_view(), self._templates_view(),
            self._entities_view()
        ]
        for i, title in enumerate(tab_titles):
            tab.set_title(i, title)
        ipd.display(tab)


# def multi_checkbox_widget(descriptions):
#     """ Widget with a search field and lots of checkboxes """
#     search_widget = ipywidgets.Text()
#     options_dict = {description: ipywidgets.Checkbox(description=description, value=False) for description in descriptions}
#     options = [options_dict[description] for description in descriptions]
#     options_widget = ipywidgets.VBox(options, layout={'overflow': 'scroll'})
#     multi_select = ipywidgets.VBox([search_widget, options_widget])
#
#     # Wire the search field to the checkboxes
#     def on_text_change(change):
#         search_input = change['new']
#         if search_input == '':
#             # Reset search field
#             new_options = [options_dict[description] for description in descriptions]
#         else:
#             # Filter by search field using difflib.
#             close_matches = difflib.get_close_matches(search_input, descriptions, cutoff=0.0)
#             new_options = [options_dict[description] for description in close_matches]
#         options_widget.children = new_options
#
#     search_widget.observe(on_text_change, names='value')
#     return multi_select
