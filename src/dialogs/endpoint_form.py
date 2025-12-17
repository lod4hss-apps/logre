import streamlit as st
from graphly.schema import Prefixes, Prefix

from lib import state
from schema.endpoint import Endpoint
from schema.sparql_technologies import SPARQLTechnology


ENDPOINT_TECHNOLOGIES_STR = [e.value for e in list(SPARQLTechnology)]


@st.dialog("Endpoint", width='medium')
def dialog_endpoint_form(endpoint: Endpoint | None = None) -> None:
    """
    Dialog for creating or editing an endpoint.
    """
    new_name = st.text_input('Name ❗️', value=endpoint.name if endpoint else '')

    new_technology = st.selectbox(
        'Endpoint technology ❗️',
        options=ENDPOINT_TECHNOLOGIES_STR,
        index=ENDPOINT_TECHNOLOGIES_STR.index(endpoint.technology) if endpoint else None,
    )
    new_url = st.text_input('Endpoint URL ❗️', value=endpoint.url if endpoint else '')

    col_user, col_pass = st.columns(2)
    new_username = col_user.text_input('Endpoint username', value=endpoint.username if endpoint else '')
    new_password = col_pass.text_input('Endpoint password', type='password', value=endpoint.password if endpoint else '')

    disabled = not (new_name and new_technology and new_url)

    if st.button('Save' if endpoint else 'Create', type='primary', disabled=disabled):
        if endpoint:
            prefixes = Prefixes([Prefix(p.short, p.long) for p in endpoint.prefixes])
            updated_endpoint = Endpoint(
                name=new_name,
                technology=new_technology,
                url=new_url,
                username=new_username,
                password=new_password,
                prefixes=prefixes,
                key=endpoint.key,
            )
            state.update_endpoint(endpoint, updated_endpoint)
        else:
            template = state.get_default_endpoint_prefixes()
            prefixes = Prefixes([Prefix(p.short, p.long) for p in template])
            new_endpoint = Endpoint(
                name=new_name,
                technology=new_technology,
                url=new_url,
                username=new_username,
                password=new_password,
                prefixes=prefixes,
            )
            state.update_endpoint(None, new_endpoint)

        st.rerun()
