import ipywidgets as widgets
import expipe
import pathlib
import uuid
from IPython.display import display_javascript, display_html, display, clear_output
import json
from expipe.backends.filesystem import convert_quantities
from collections import OrderedDict


def _build_dict_tree(key, value):
    contents = "<li>"
    contents += "{}: ".format(key)
    try:
        items = value.items()
        inner_contents = ""
        for subkey, subvalue in items:
            inner_contents += _build_dict_tree(subkey, subvalue)
        if inner_contents != "":
            contents += "<ul>{}</ul>".format(inner_contents)
    except AttributeError:
        contents += "{}".format(value)

    contents += "</li>"

    return contents


def dict_html(dictionary):
    output = ""
    for key, value in dictionary.items():
        output += _build_dict_tree(key, value)
    return "<ul>{}</ul>".format(output)


def display_dict_html(dictionary):
    clear_output()
    dictionary = convert_quantities(dictionary)
    display_html(dict_html(dictionary), raw=True)


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
        actions_visible = widgets.SelectMultiple(
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


        export_actions_name = widgets.Text()

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


        export_actions_button = widgets.Button(
            description='Export actions',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
        )
        export_actions_button.on_click(on_export_actions)

        checkbox_groups = []
        checkbox_group_names = []
        for name, value in self.action_attributes.items():
            print(name)
            temp = []
            for key in value:
                ch = widgets.Checkbox(
                    value=False,
                    description=key,
                    disabled=False
                )
                ch.observe(on_checkbox_change, names='value')
                temp.append(ch)
                checkbox_group[ch] = name
            box = widgets.VBox(temp, layout={'overflow': 'scroll'})
            checkbox_groups.append(box)
            checkbox_group_names.append(name)

        action_attributes = widgets.Accordion(checkbox_groups)
        for i, name in enumerate(checkbox_group_names):
            action_attributes.set_title(i, name.capitalize())
        actions_visible.layout = {'overflow': 'scroll', 'height': '750px'} #TODO figure out how to automatically scale list height

        actions_select = widgets.VBox([actions_visible, export_actions_name, export_actions_button])
        return widgets.HBox([action_attributes, actions_select])

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

        actions_select = widgets.Select(
            options=actions_list,
            disabled=False,
            value=None if actions_list_empty else actions_list[0]
        )
        modules_list = widgets.Select(
            options=action_first_modules,
            disabled=False,
            value=None if modules_list_empty else action_first_modules[0]
        )
        out = widgets.Output()
        if not modules_list_empty:
            with out:
                display_dict_html(module_first.contents)

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
                    display_dict_html(module.contents)

        actions_select.observe(on_select_action, names='value')
        modules_list.observe(on_select_module, names='value')

        return widgets.HBox([actions_select, modules_list, out], style={'overflow': 'scroll'})

    def _project_modules_view(self):
        modules_list = list(self.project.modules.keys())
        if len(modules_list) == 0:
            modules_list_empty = True
        else:
            modules_list_empty = False
            module_first = self.project.modules[modules_list[0]]

        modules_select = widgets.Select(
            options=modules_list,
            disabled=False,
            value=None if modules_list_empty else modules_list[0]
        )
        out = widgets.Output()
        if not modules_list_empty:
            with out:
                display_dict_html(module_first.contents)


        def on_select_module(change):
            if change['name'] == 'value':
                module = self.project.modules[change['owner'].value]
                with out:
                    display_dict_html(module.contents)

        modules_select.observe(on_select_module, names='value')

        return widgets.HBox([modules_select, out], style={'overflow': 'scroll'})

    def _templates_view(self):
        templates_list = list(self.project.templates.keys())
        if len(templates_list) == 0:
            templates_list_empty = True
        else:
            templates_list_empty = False
            template_first = self.project.templates[templates_list[0]]

        templates_select = widgets.Select(
            options=templates_list,
            disabled=False,
            value=None if templates_list_empty else templates_list[0]
        )

        out = widgets.Output()
        if not templates_list_empty:
            with out:
                display_dict_html(template_first.contents)

        def on_select_template(change):
            if change['name'] == 'value':
                template = self.project.templates[change['owner'].value]
                with out:
                    display_dict_html(template.contents)

        templates_select.observe(on_select_template, names='value')

        return widgets.HBox([templates_select, out])

    def _action_attributes_view(self):
        actions_list = list(self.project.actions.keys())
        if len(actions_list) == 0:
            actions_list_empty = True
        else:
            actions_list_empty = False
            action_first = self.project.actions[actions_list[0]]

        actions_select = widgets.Select(
            options=actions_list,
            disabled=False,
            value=None if actions_list_empty else actions_list[0]
        )

        out = widgets.Output()
        if not actions_list_empty:
            with out:
                display_dict_html(action_first.attributes)

        def on_select_action(change):
            if change['name'] == 'value':
                action = self.project.actions[change['owner'].value]
                with out:
                    display_dict_html(action.attributes)

        actions_select.observe(on_select_action, names='value')

        return widgets.HBox([actions_select, out], style={'overflow': 'scroll'})

    def _entities_view(self):
        entities_list = list(self.project.entities.keys())
        if len(entities_list) == 0:
            entities_list_empty = True
        else:
            entities_list_empty = False
            entity_first = self.project.entities[entities_list[0]]

        entities_select = widgets.Select(
            options=entities_list,
            disabled=False,
            value=None if entities_list_empty else entities_list[0]
        )

        out = widgets.Output()
        if not entities_list_empty:
            with out:
                display_dict_html(entity_first.attributes)

        def on_select_entity(change):
            if change['name'] == 'value':
                entity = self.project.entities[change['owner'].value]
                with out:
                    display_dict_html(entity.attributes)

        entities_select.observe(on_select_entity, names='value')

        return widgets.HBox([entities_select, out], style={'overflow': 'scroll'})

    def display(self):
        # Actions tab
        actions_tab_tab_titles = ['Export', 'Attributes', 'Modules']
        actions_tab = widgets.Tab()
        actions_tab.children = [
            self._actions_view(), self._action_attributes_view(),
            self._action_modules_view()
        ]
        for i, title in enumerate(actions_tab_tab_titles):
            actions_tab.set_title(i, title)

        tab_titles = ['Actions', 'Modules','Templates', 'Entities']
        tab = widgets.Tab()
        tab.children = [
            actions_tab, self._project_modules_view(), self._templates_view(),
            self._entities_view()
        ]
        for i, title in enumerate(tab_titles):
            tab.set_title(i, title)
        display(tab)


# def multi_checkbox_widget(descriptions):
#     """ Widget with a search field and lots of checkboxes """
#     search_widget = widgets.Text()
#     options_dict = {description: widgets.Checkbox(description=description, value=False) for description in descriptions}
#     options = [options_dict[description] for description in descriptions]
#     options_widget = widgets.VBox(options, layout={'overflow': 'scroll'})
#     multi_select = widgets.VBox([search_widget, options_widget])
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
