import streamlit as st
from graphly.schema import Prefix, Sparql
from components.init import init
from components.menu import menu
from lib import state
from dialogs.confirmation import dialog_confirmation
from dialogs.endpoint_form import dialog_endpoint_form
from dialogs.data_bundle_form import dialog_data_bundle_form
from dialogs.error_message import dialog_error_message
from schema.data_bundle import DataBundle

# Page parameters
PAGINATION_LENGTH = 5
MAX_STRING_LENGTH = 80

# Initialize
init()
menu()

# Title
st.markdown('# Configuration')
st.markdown('')


# From state
prefixes = state.get_prefixes()
endpoints = state.get_endpoints()
data_bundles = state.get_data_bundles()

### Prefixes ###

with st.expander("Prefixes"):

    # Flag to allow creation of a new prefix or not (every prefixes needs to be correcteclyt set in order to create another one)
    all_prefixes_are_set = True

    # Loop for each prefixes
    for i, prefix in enumerate(prefixes):
        if not prefix.short or not prefix.long:
            all_prefixes_are_set = False

        # The prefix itself
        with st.container(horizontal=True, vertical_alignment="bottom"):
            new_short = st.text_input('Prefix short', value=prefix.short, width=100, key=f"prefix-short-{i}")
            new_long = st.text_input('Prefix long', value=prefix.long, key=f"prefix-long-{i}")

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

with st.container(horizontal=True, horizontal_alignment='right'):
    st.markdown("More on prefixes in the [Documentation FAQ](/documentation#what-are-prefixes)", width='content')


### SPARQL endpoints ###

with st.expander(f"SPARQL endpoints"):

    # Loop through all endpoints, and display a short version of them
    for i, endpoint in enumerate(endpoints):

        # The endpoint itself
        with st.container(horizontal=True, vertical_alignment='center'):
            st.markdown(f"**{endpoint.name}**")

            # Edit button
            if st.button('', icon=':material/edit:', type='tertiary', key=f'config-endpoint-edit-{i}'):
                dialog_endpoint_form(endpoint)

            # Delete button
            if st.button('', icon=':material/delete:', type='tertiary', key=f'config-endpoint-delete-{i}'):

                used_endpoint = list(map(lambda db: db.endpoint, data_bundles))
                if endpoint in used_endpoint:
                    dialog_error_message('You can not delete this SPARQL endpoint configuration: at least one data bundle relies on it.')
                else:
                    def callback_delete_sparql_endpoint(sparql: Sparql) -> None:
                        state.update_endpoint(sparql, None)
                        state.set_toast('SPARQL endpoint removed', icon=':material/delete:')
                    dialog_confirmation(f"You are about to delete the SPARQL endpoint *{endpoint.name}*", callback_delete_sparql_endpoint, sparql=endpoint)
        
        
    st.write('')

    # Add button
    if st.button('Add an Endpoint'):
        dialog_endpoint_form()
    
with st.container(horizontal=True, horizontal_alignment='right'):
    st.markdown("More on SPARQL endpoints in the [Documentation FAQ](/documentation#what-is-a-sparql-endpoint)", width='content')

### Data bundles ###

with st.expander(f"Data bundles"):
    
    # Loop through all data bundles and display a short version of them
    for i, db in enumerate(data_bundles):
        
        # The data bundle itself
        with st.container(horizontal=True, vertical_alignment='center'):
            st.markdown(f"**{db.name}** - *{db.endpoint.name}*")

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
    
with st.container(horizontal=True, horizontal_alignment='right'):
    st.markdown("More on data bundles in the [Documentation FAQ](/documentation#what-are-data-bundles)", width='content')