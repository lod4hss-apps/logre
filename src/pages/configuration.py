import streamlit as st
from graphly.schema import Prefix, Prefixes

from components.init import init
from components.menu import menu
from dialogs.confirmation import dialog_confirmation
from dialogs.data_bundle_form import dialog_data_bundle_form
from dialogs.endpoint_form import dialog_endpoint_form
from lib import state
from schema.endpoint import Endpoint
from schema.data_bundle import DataBundle
from schema.sparql_technologies import SPARQLTechnology


def __clone_prefixes(prefixes: Prefixes) -> Prefixes:
    return Prefixes([Prefix(p.short, p.long) for p in prefixes])


def __persist_endpoint(endpoint: Endpoint, **changes) -> None:
    prefixes = changes.get('prefixes', endpoint.prefixes)
    updated = Endpoint(
        name=changes.get('name', endpoint.name),
        technology=changes.get('technology', endpoint.technology),
        url=changes.get('url', endpoint.url),
        username=changes.get('username', endpoint.username),
        password=changes.get('password', endpoint.password),
        prefixes=__clone_prefixes(prefixes),
        key=endpoint.key,
    )
    state.update_endpoint(endpoint, updated)
    st.rerun()


def __del_endpoint(endpoint: Endpoint) -> None:
    bundles = [db for db in state.get_data_bundles() if db.endpoint_key == endpoint.key]
    for bundle in bundles:
        state.update_data_bundle(bundle, None)
    state.update_endpoint(endpoint, None)
    state.set_toast('Endpoint removed', icon=':material/delete:')
    st.rerun()


def __del_data_bundle(db: DataBundle) -> None:
    state.update_data_bundle(db, None)
    state.set_toast('Data Bundle removed', icon=':material/delete:')
    st.rerun()


def __del_prefix(endpoint: Endpoint, prefix: Prefix) -> None:
    prefixes = __clone_prefixes(endpoint.prefixes)
    for idx, pref in enumerate(prefixes):
        if pref.short == prefix.short and pref.long == prefix.long:
            del prefixes.prefix_list[idx]
            break
    updated = Endpoint(
        name=endpoint.name,
        technology=endpoint.technology,
        url=endpoint.url,
        username=endpoint.username,
        password=endpoint.password,
        prefixes=prefixes,
        key=endpoint.key,
    )
    state.update_endpoint(endpoint, updated)
    state.set_toast('Prefix removed', icon=':material/delete:')
    st.rerun()


def __render_endpoint_settings(endpoint: Endpoint, index: int) -> None:
    st.markdown("### Connection")
    col1, col1_save = st.columns([10, 1], vertical_alignment='bottom')
    name = col1.text_input('Name', value=endpoint.name, key=f'endpoint-name-{index}')
    if name != endpoint.name and col1_save.button('', icon=':material/save:', type='tertiary', key=f'endpoint-name-save-{index}'):
        __persist_endpoint(endpoint, name=name)

    col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
    technologies = [e.value for e in SPARQLTechnology]
    technology = col1.selectbox('Technology', technologies, index=technologies.index(endpoint.technology), key=f'endpoint-tech-{index}')
    if technology != endpoint.technology and col1_save.button('', icon=':material/save:', type='tertiary', key=f'endpoint-tech-save-{index}'):
        __persist_endpoint(endpoint, technology=technology)

    url = col2.text_input('URL', value=endpoint.url, key=f'endpoint-url-{index}')
    if url != endpoint.url and col2_save.button('', icon=':material/save:', type='tertiary', key=f'endpoint-url-save-{index}'):
        __persist_endpoint(endpoint, url=url)

    col1, col1_save, col2, col2_save = st.columns([5, 1, 5, 1], vertical_alignment='bottom')
    username = col1.text_input('Username', value=endpoint.username, key=f'endpoint-username-{index}')
    if username != endpoint.username and col1_save.button('', icon=':material/save:', type='tertiary', key=f'endpoint-username-save-{index}'):
        __persist_endpoint(endpoint, username=username)

    password = col2.text_input('Password', value=endpoint.password, type='password', key=f'endpoint-password-{index}')
    if password != endpoint.password and col2_save.button('', icon=':material/save:', type='tertiary', key=f'endpoint-password-save-{index}'):
        __persist_endpoint(endpoint, password=password)


def __render_data_bundles(endpoint: Endpoint, default_bundle: DataBundle | None, index_endpoint: int) -> None:
    st.markdown("### Data Bundles")
    bundles = [db for db in state.get_data_bundles() if db.endpoint_key == endpoint.key]

    if not bundles:
        st.info("No data bundle configured yet")

    for idx, db in enumerate(bundles):
        with st.container(border=True):
            cols = st.columns([6, 2, 1, 1], vertical_alignment='center')
            cols[0].markdown(f"**{db.name}**")
            if default_bundle == db:
                cols[1].markdown('*Default*')
            elif cols[1].button('Set as default', type='tertiary', key=f'default-db-{index_endpoint}-{idx}'):
                state.set_default_data_bundle(db)
                st.rerun()

            if cols[2].button('', icon=':material/edit:', type='tertiary', key=f'edit-db-{index_endpoint}-{idx}'):
                dialog_data_bundle_form(endpoint, db)
            if cols[3].button('', icon=':material/delete:', type='tertiary', key=f'del-db-{index_endpoint}-{idx}'):
                dialog_confirmation(
                    f"You are about to delete the Data Bundle *{db.name}*",
                    __del_data_bundle,
                    db=db
                )

    st.write('')
    if st.button('Add a Data Bundle', key=f'add-bundle-{index_endpoint}'):
        dialog_data_bundle_form(endpoint)


def __render_prefixes(endpoint: Endpoint, index_endpoint: int) -> None:
    st.markdown("### Prefixes")
    prefixes = list(endpoint.prefixes)
    if not prefixes:
        st.info("No prefixes configured for this endpoint.")

    for idx, prefix in enumerate(sorted(prefixes, key=lambda p: p.short)):
        col1, col1_save, col2, col2_save, col_delete = st.columns([2, 1, 8, 1, 1], vertical_alignment='bottom')
        short = col1.text_input('Short', value=prefix.short, key=f'prefix-short-{index_endpoint}-{idx}')
        if short != prefix.short and col1_save.button('', icon=':material/save:', type='tertiary', key=f'prefix-short-save-{index_endpoint}-{idx}'):
            updated_prefixes = __clone_prefixes(endpoint.prefixes)
            updated_prefixes[idx].short = short
            __persist_endpoint(endpoint, prefixes=updated_prefixes)

        long = col2.text_input('Long', value=prefix.long, key=f'prefix-long-{index_endpoint}-{idx}')
        if long != prefix.long and col2_save.button('', icon=':material/save:', type='tertiary', key=f'prefix-long-save-{index_endpoint}-{idx}'):
            updated_prefixes = __clone_prefixes(endpoint.prefixes)
            updated_prefixes[idx].long = long
            __persist_endpoint(endpoint, prefixes=updated_prefixes)

        if col_delete.button('', icon=':material/delete:', type='tertiary', key=f'prefix-del-{index_endpoint}-{idx}'):
            dialog_confirmation(
                f"You are about to delete prefix\n{prefix.short}: {prefix.long}",
                __del_prefix,
                endpoint=endpoint,
                prefix=prefix
            )

    st.write('')
    if st.button('Add a new Prefix', key=f'prefix-add-{index_endpoint}'):
        updated_prefixes = __clone_prefixes(endpoint.prefixes)
        updated_prefixes.add(Prefix('', ''))
        __persist_endpoint(endpoint, prefixes=updated_prefixes)


##### PAGE #####

init(query_param_keys=['endpoint', 'db'])
menu()

st.markdown('# Configuration')
st.markdown('')

endpoints = state.get_endpoints()
default_bundle = state.get_default_data_bundle()

if st.button('Add a new Endpoint', icon=':material/add:'):
    dialog_endpoint_form()

if not endpoints:
    st.info("No endpoint configured yet. Create one to get started.", icon=":material/info:")

for index_endpoint, endpoint in enumerate(endpoints):
    with st.expander(f"Endpoint *{endpoint.name}*"):
        header_cols = st.columns([6, 1], vertical_alignment='center')
        header_cols[0].markdown(f"## Endpoint *{endpoint.name}*")
        if header_cols[1].button('Delete Endpoint', icon=':material/delete:', type='tertiary', key=f'delete-endpoint-{index_endpoint}'):
            dialog_confirmation(
                f"You are about to delete the Endpoint:\n{endpoint.name}",
                __del_endpoint,
                endpoint=endpoint
            )

        st.write('')
        __render_endpoint_settings(endpoint, index_endpoint)
        st.divider()
        __render_data_bundles(endpoint, default_bundle, index_endpoint)
        st.divider()
        __render_prefixes(endpoint, index_endpoint)
