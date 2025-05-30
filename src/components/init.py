from typing import Literal
from dotenv import load_dotenv
import streamlit as st
import lib.state as state
from lib.configuration import read_config
from lib.version import read_version
from model import NotExistingEndpoint, NotExistingDataBundle


def init(layout: Literal['centered', 'wide'] = 'centered') -> None:
    """Initialization function that runs on each page. Has to be the first thing to be called."""

    load_dotenv()

    try:

        # Tab/page infos
        st.set_page_config(
            page_title='Logre',
            page_icon='👹',
            layout=layout
        )

        # Hide anchor link for titles
        # st.html("<style>[data-testid='stHeaderActionElements'] {display: none;}</style>")

        # Load version number if not in state
        if not state.get_version():
            read_version()

        # If there is no config in state, read it
        if not state.get_has_config():
            read_config()

        # State initialization
        if not state.get_queries(): state.set_queries([])
        if not state.get_endpoints(): state.set_endpoints([])

        # Handle toasts: if some is asked, display it, and clear the state
        text, icon = state.get_toast()
        if text: 
            st.toast(text, icon=icon if icon else ':material/info:')
            state.clear_toast()

        # On each page load, clear the confirmation, 
        # so that it is not prefilled on new confirmation
        state.clear_confirmation()

        # Load information from the query params: Endpoint
        if state.has_query_params('endpoint'):
            endpoint_url = state.get_query_param('endpoint')
            all_endpoints = state.get_endpoints()
            selection = [e for e in all_endpoints if e.name == endpoint_url]
            if len(selection) == 0: raise NotExistingEndpoint(endpoint_url)
            else: endpoint = selection[0]
            state.set_endpoint(endpoint)

        # Load information from the query params: DataBundle
        if state.has_query_params('data_bundle'):
            # Get the endpoint (just set above)
            endpoint = state.get_endpoint() 
            data_bundle_name = state.get_query_param('data_bundle')
            selection = [e for e in endpoint.data_bundles if e.name == data_bundle_name]
            if len(selection) == 0: raise NotExistingDataBundle(data_bundle_name)
            else: data_bundle = selection[0]
            state.set_data_bundle(data_bundle)

        # Load information from the query params: Entity
        if state.has_query_params('entity'):
            data_bundle = state.get_data_bundle()
            entity_uri = state.get_query_param('entity')
            entity = data_bundle.get_entity_infos(entity_uri)
            state.set_entity(entity)

        # Once everythings is loaded from query params, clear them (from state)
        state.clear_query_param()


    except BaseException as error:

        raise error

        print('ERROR CAUGHT IN init.py/init():')
        print(error)

        st.error(str(error))
        st.stop()