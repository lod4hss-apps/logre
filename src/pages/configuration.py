import streamlit as st
from graphly.schema import Prefix
from components.init import init
from components.menu import menu
from dialogs.confirmation import dialog_confirmation
from lib import state
from dialogs.data_bundle_form import dialog_data_bundle_form
from schema.data_bundle import DataBundle
from components.help import info_icon

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

# Initialize
init(query_param_keys=['endpoint', 'db'])
menu()

# Title
st.markdown('# Configuration')
st.markdown('')

active_bundle = state.get_data_bundle()

### Prefixes ###

with st.expander("Prefixes"):
    header_cols = st.columns([20, 1], vertical_alignment="center")
    header_cols[0].markdown("#### Prefixes", width='content')
    with header_cols[1]:
        info_icon("configuration.prefixes")
    # From state
    prefixes = state.get_prefixes()

    # Flag to allow creation of a new prefix or not (every prefixes needs to be correcteclyt set in order to create another one)
    all_prefixes_are_set = True

    # Loop for each prefixes
    for i, prefix in enumerate(prefixes):
        if not prefix.short or not prefix.long:
            all_prefixes_are_set = False

        # The prefix itself
        with st.container(horizontal=True, vertical_alignment="bottom"):
            new_short = st.text_input('Prefix short', value=prefix.short, width=100)
            new_long = st.text_input('Prefix long', value=prefix.long)

            # Delete button
            if st.button('', icon=':material/delete:', type='tertiary', key=f'config-prefix-{i}'):
                def callback_delete_prefix(prefix: Prefix) -> None:
                    state.update_prefix(prefix, None)
                    state.set_toast('Prefix removed', icon=':material/delete:')
                dialog_confirmation(f"You are about to delete the prefix *{prefix.short}:{prefix.long}*", callback_delete_prefix, prefix=prefix)

            # Update button
            if new_short != prefix.short or new_long != prefix.long:
                state.update_prefix(prefix, Prefix(new_short, new_long))
                state.set_toast('Prefix updated', icon=':material/edit:')
                st.rerun()

    st.write('')

    # Add a new prefix if the flag is True
    if all_prefixes_are_set and st.button('Add a new Prefix'):
        state.update_prefix(None, Prefix('', ''))
        state.set_toast('Prefix created', icon=':material/add:')
        st.rerun()


### Data bundles ###

# Loop through all data bundles and display a short version of it
with st.expander(f"Data bundles"):
    data_header_cols = st.columns([20, 1], vertical_alignment="center")
    data_header_cols[0].markdown("#### Data bundles", width='content')
    with data_header_cols[1]:
        info_icon("configuration.data_bundles")
    # From state
    data_bundles = state.get_data_bundles()
    for i, db in enumerate(data_bundles):
        
        # The data bundle itself
        with st.container(horizontal=True, vertical_alignment='center'):
            st.markdown(f"**{db.name}**")

            # Handle default options (set to default + label)
            if state.get_default_data_bundle() == db: 
                st.markdown('*Default*', width='content')
            else:  
                if st.button('Set as default', type='tertiary', key=f'config-data-bundle-default-{i}'):
                    state.set_default_data_bundle(db)
                    st.rerun()

            # Edit button
            if st.button('', icon=':material/edit:', type='tertiary', key=f'config-data-bundle-edit-{i}'):
                dialog_data_bundle_form(db)

            # Delete button
            if st.button('', icon=':material/delete:', type='tertiary', key=f'config-data-bundle-delete-{i}'):
                def callback_delete_data_bundle(db: DataBundle) -> None:
                    state.update_data_bundle(db, None)
                    state.set_toast('Data Bundle removed', icon=':material/delete:')
                dialog_confirmation(f"You are about to delete the Data Bundle *{db.name}*", callback_delete_data_bundle, db=db)
        
    st.write('')

    # Add button
    if st.button('Add a Data Bundle'):
        dialog_data_bundle_form()

st.write('')

with st.expander("Import data"):
    import_header_cols = st.columns([20, 1], vertical_alignment="center")
    import_header_cols[0].markdown("#### Import data", width='content')
    with import_header_cols[1]:
        info_icon("configuration.import_data")
    if not active_bundle:
        st.warning("Select an active data bundle (via the dashboard) before importing data.")
    else:
        with st.container(horizontal=True, horizontal_alignment='center'):
            file_format_str = st.radio('Format', options=['n-Quads (.nq)', 'Turtle (.ttl)'], horizontal=True, label_visibility='collapsed', key='radio-import-config')
            file_format = file_format_str[file_format_str.index('(.') + 2:file_format_str.index(')')]

        st.divider()

        file = st.file_uploader(f"Load your {file_format_str} file:", type=[file_format], disabled=(file_format_str is None), accept_multiple_files=False)
        if file:
            file_content = file.read().decode("utf-8")

            st.write('')
            st.write('')

            with st.container(horizontal=True, horizontal_alignment='center'):
                st.markdown(f'The file will be imported into *{active_bundle.name}*.', width='content')

            st.divider()

            if file_format == 'nq':
                with st.container(horizontal=True, horizontal_alignment='center'):
                    if st.button('Upload n-Quads', type='primary', icon=':material/upload:', key='config-upload-nq'):
                        def upload_nquads(nquad_content) -> None:
                            active_bundle.endpoint.upload_nquads(nquad_content)
                            state.set_toast('n-Quad file uploaded', icon=':material/done:')
                        dialog_confirmation(f'You are about to upload the file {file.name}.', callback=upload_nquads, nquad_content=file_content)
            else:
                with st.container(horizontal=True, horizontal_alignment='center'):
                    data_type = st.radio('What is in the file?', options=['Data', 'Model', 'Metadata'], horizontal=True, key='config-import-type')

                st.divider()

                with st.container(horizontal=True, horizontal_alignment='center'):
                    if st.button(f'Upload Turtle file into the {data_type.upper()} named graph', type='primary', icon=':material/upload:', key='config-upload-ttl'):
                        def upload_turtle(turtle_content: str) -> None:
                            if data_type == "Data": graph = active_bundle.graph_data
                            if data_type == "Model": graph = active_bundle.graph_model
                            if data_type == "Metadata": graph = active_bundle.graph_metadata
                            graph.upload_turtle(turtle_content)
                            state.set_toast('Turtle file uploaded', icon=':material/done:')
                        confirmation_text = f'You are about to upload the file *{file.name}* into the {data_type} named graph.'
                        dialog_confirmation(confirmation_text, callback=upload_turtle, turtle_content=file_content)

with st.expander("Update the model (SHACL)"):
    update_header_cols = st.columns([20, 1], vertical_alignment="center")
    update_header_cols[0].markdown("#### Update the model (SHACL)", width='content')
    with update_header_cols[1]:
        info_icon("configuration.update_model")
    if not active_bundle:
        st.warning("Select an active data bundle before editing the model.")
    else:
        with st.container(horizontal=True, horizontal_alignment='center'):
            with st.spinner("Extraction du modèle..."):
                current_model = active_bundle.graph_model.dump_turtle(active_bundle.prefixes)
            st.download_button(
                "Download current model (.ttl)",
                data=current_model,
                file_name=f"logre_{active_bundle.key}_model.ttl",
                mime="text/turtle",
                icon=":material/download:",
                key="download-current-model-btn"
            )
            if st.button("Delete current model", type="secondary", icon=":material/delete:", key="delete-model-btn"):
                def clear_model() -> None:
                    active_bundle.delete('model', [('?s', '?p', '?o')])
                    state.set_toast('Model cleared', icon=':material/delete:')
                    active_bundle.load_model()
                dialog_confirmation(
                    "You are about to delete every triple from the model graph.",
                    callback=clear_model
                )

        files = st.file_uploader("Upload your SHACL files (.ttl)", type=['ttl'], accept_multiple_files=True)
        if files:
            files_content = ''
            for file in files:
                files_content += '\n' + file.read().decode("utf-8")

            st.write('')
            st.write('')

            with st.container(horizontal=True, horizontal_alignment='center'):
                st.markdown("Files will be imported into the configured **model graph**.")
                st.warning("If your model shares the same named graph as your data, this operation will delete everything in that graph.")

            st.divider()

            with st.container(horizontal=True, horizontal_alignment='center'):
                if st.button('Replace current model', type='primary', icon=':material/upload:'):
                    def replace_model(turtle_content: str) -> None:
                        active_bundle.delete('model', [('?s', '?p', '?o')])
                        active_bundle.graph_model.upload_turtle(turtle_content)
                        state.set_toast('Model replaced', icon=':material/done:')
                        active_bundle.load_model()
                    dialog_confirmation(
                        'You are about to replace the existing model by the provided files.',
                        callback=replace_model,
                        turtle_content=files_content
                    )
