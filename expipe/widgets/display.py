import ipywidgets
import IPython.display as ipd
import difflib
import expipe


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
    ipd.clear_output()
    dictionary = expipe.backends.filesystem.convert_quantities(dictionary)
    ipd.display_html(dict_html(dictionary), raw=True)


def modules_view(holder):
    modules_list = list(holder.modules.keys())
    if len(modules_list) == 0:
        modules_list_empty = True
    else:
        modules_list_empty = False
        module_first = holder.modules[modules_list[0]]

    modules_select = ipywidgets.Select(
        options=modules_list,
        disabled=False,
        value=None if modules_list_empty else modules_list[0],
        layout={'height': '200px'}
    )
    out = ipywidgets.Output(layout={'height': '250px'})
    if not modules_list_empty:
        with out:
            display_dict_html(module_first.contents)


    def on_select_module(change):
        if change['name'] == 'value':
            module = holder.modules[change['owner'].value]
            with out:
                display_dict_html(module.contents)

    modules_select.observe(on_select_module, names='value')
    search_select = _add_search_field(modules_select)

    return ipywidgets.HBox([search_select, out], style={'overflow': 'scroll'})


def messages_view(holder):
    messages_list = list(holder.messages.keys())
    if len(messages_list) == 0:
        messages_list_empty = True
    else:
        messages_list_empty = False
        message_first = holder.messages[messages_list[0]]

    messages_select = ipywidgets.Select(
        options=messages_list,
        disabled=False,
        value=None if messages_list_empty else messages_list[0],
        layout={'height': '200px'}
    )
    out = ipywidgets.Output(layout={'height': '250px'})
    if not messages_list_empty:
        with out:
            display_dict_html(message_first.contents)


    def on_select_message(change):
        if change['name'] == 'value':
            message = holder.messages[change['owner'].value]
            with out:
                display_dict_html(message.contents)

    messages_select.observe(on_select_message, names='value')
    search_select = _add_search_field(messages_select)

    return ipywidgets.HBox([search_select, out], style={'overflow': 'scroll'})


def templates_view(project):
    templates_list = list(project.templates.keys())
    if len(templates_list) == 0:
        templates_list_empty = True
    else:
        templates_list_empty = False
        template_first = project.templates[templates_list[0]]

    templates_select = ipywidgets.Select(
        options=templates_list,
        disabled=False,
        value=None if templates_list_empty else templates_list[0],
        layout={'height': '200px'}
    )

    out = ipywidgets.Output(layout={'height': '250px'})
    if not templates_list_empty:
        with out:
            display_dict_html(template_first.contents)

    def on_select_template(change):
        if change['name'] == 'value':
            template = project.templates[change['owner'].value]
            with out:
                display_dict_html(template.contents)

    templates_select.observe(on_select_template, names='value')
    search_select = _add_search_field(templates_select)

    return ipywidgets.HBox([search_select, out])


def entities_view(project):
    entities_list = list(project.entities.keys())
    if len(entities_list) == 0:
        entities_list_empty = True
    else:
        entities_list_empty = False
        entity_first = project.entities[entities_list[0]]

    entities_select = ipywidgets.Select(
        options=entities_list,
        disabled=False,
        value=None if entities_list_empty else entities_list[0],
        layout={'height': '200px'}
    )

    out = ipywidgets.Output(layout={'height': '250px'})
    if not entities_list_empty:
        with out:
            display_dict_html(entity_first.attributes)

    def on_select_entity(change):
        if change['name'] == 'value':
            entity = project.entities[change['owner'].value]
            with out:
                display_dict_html(entity.attributes)

    entities_select.observe(on_select_entity, names='value')
    search_select = _add_search_field(entities_select)

    return ipywidgets.HBox([search_select, out], style={'overflow': 'scroll'})


def actions_view(project):
    actions_list = list(project.actions.keys())
    if len(actions_list) == 0:
        actions_list_empty = True
    else:
        actions_list_empty = False
        action_first = project.actions[actions_list[0]]

    actions_select = ipywidgets.Select(
        options=actions_list,
        disabled=False,
        value=None if actions_list_empty else actions_list[0],
        layout={'height': '200px'}
    )

    out = ipywidgets.Output(layout={'height': '250px'})
    if not actions_list_empty:
        with out:
            display_dict_html(action_first.attributes)

    def on_select_action(change):
        if change['name'] == 'value':
            action = project.actions[change['owner'].value]
            with out:
                display_dict_html(action.attributes)

    actions_select.observe(on_select_action, names='value')
    search_select = _add_search_field(actions_select)

    return ipywidgets.HBox([search_select, out], style={'overflow': 'scroll'})


def _add_search_field(selectbox):
    search_widget = ipywidgets.Text(placeholder='Search')
    orig_list = list(selectbox.options)
    # Wire the search field to the checkboxes
    def on_text_change(change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = orig_list
        else:
            # Filter by search field using difflib.
            new_options = [a for a in orig_list if search_input in a]
        selectbox.options = new_options

    search_widget.observe(on_text_change, names='value')
    return ipywidgets.VBox([search_widget, selectbox])
