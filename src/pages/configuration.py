import streamlit as st
from graphly.schema import Prefix, Sparql
from components.init import init
from components.doc_links import decorate_doc_links
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
st.markdown("# Configuration")
st.markdown("")


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
            new_short = st.text_input(
                "Prefix short", value=prefix.short, width=100, key=f"prefix-short-{i}"
            )
            new_long = st.text_input(
                "Prefix long", value=prefix.long, key=f"prefix-long-{i}"
            )
            new_short_clean = new_short.strip()
            new_long_clean = new_long.strip()

            # Delete button
            if st.button(
                "", icon=":material/delete:", type="tertiary", key=f"config-prefix-{i}"
            ):

                def callback_delete_prefix(prefix: Prefix) -> None:
                    state.update_prefix(prefix, None)
                    state.set_toast("Prefix removed", icon=":material/delete:")

                dialog_confirmation(
                    f"You are about to delete the prefix *{prefix.short}:{prefix.long}*",
                    callback_delete_prefix,
                    prefix=prefix,
                )

            # Update button
            if new_short_clean != prefix.short or new_long_clean != prefix.long:
                state.update_prefix(prefix, Prefix(new_short_clean, new_long_clean))
                state.set_toast("Prefix updated", icon=":material/edit:")
                st.rerun()

    st.write("")

    # Add a new prefix if the flag is True
    if all_prefixes_are_set and st.button("Add a new Prefix"):
        state.update_prefix(None, Prefix("", ""))
        state.set_toast("Prefix created", icon=":material/add:")
        st.rerun()

with st.container(horizontal=True, horizontal_alignment="right"):
    st.markdown(
        decorate_doc_links(
            "More on prefixes in the [Documentation FAQ](/documentation?section=what-are-prefixes)"
        ),
        width="content",
    )


### SPARQL endpoints ###

if st.button("Add an Endpoint"):
    dialog_endpoint_form()

if not endpoints:
    st.info("No endpoint configured yet. Create one to get started.")

for endpoint_index, endpoint in enumerate(endpoints):
    with st.expander(f"Endpoint *{endpoint.name}*"):
        header_cols = st.columns([6, 1, 1], vertical_alignment="center")
        header_cols[0].markdown(f"**{endpoint.name}**")

        if header_cols[1].button(
            "",
            icon=":material/edit:",
            type="tertiary",
            key=f"config-endpoint-edit-{endpoint_index}",
        ):
            dialog_endpoint_form(endpoint)

        if header_cols[2].button(
            "",
            icon=":material/delete:",
            type="tertiary",
            key=f"config-endpoint-delete-{endpoint_index}",
        ):
            used_endpoint = list(map(lambda db: db.endpoint, data_bundles))
            if endpoint in used_endpoint:
                dialog_error_message(
                    "You can not delete this SPARQL endpoint configuration: at least one data bundle relies on it."
                )
            else:

                def callback_delete_sparql_endpoint(sparql: Sparql) -> None:
                    state.update_endpoint(sparql, None)
                    state.set_toast("SPARQL endpoint removed", icon=":material/delete:")

                dialog_confirmation(
                    f"You are about to delete the SPARQL endpoint *{endpoint.name}*",
                    callback_delete_sparql_endpoint,
                    sparql=endpoint,
                )

        st.write("")
        st.markdown("### Data Bundles")

        endpoint_data_bundles = list(
            filter(lambda db: db.endpoint == endpoint, data_bundles)
        )
        if not endpoint_data_bundles:
            st.info("No data bundle configured for this endpoint yet")

        for bundle_index, db in enumerate(endpoint_data_bundles):
            with st.container(horizontal=True, vertical_alignment="center"):
                st.markdown(f"> **{db.name}**")

                if state.get_default_data_bundle() == db:
                    st.markdown("*Default*", width="content")
                else:
                    if st.button(
                        "Set as default",
                        type="tertiary",
                        key=f"config-data-bundle-default-{endpoint_index}-{bundle_index}",
                    ):
                        state.set_default_data_bundle(db)
                        state.invalidate_caches("set_default_data_bundle")
                        st.rerun()

                if st.button(
                    "",
                    icon=":material/edit:",
                    type="tertiary",
                    key=f"config-data-bundle-edit-{endpoint_index}-{bundle_index}",
                ):
                    dialog_data_bundle_form(db)

                if st.button(
                    "",
                    icon=":material/delete:",
                    type="tertiary",
                    key=f"config-data-bundle-delete-{endpoint_index}-{bundle_index}",
                ):

                    def callback_delete_data_bundle(db: DataBundle) -> None:
                        state.update_data_bundle(db, None)
                        state.set_toast("Data Bundle removed", icon=":material/delete:")

                    dialog_confirmation(
                        f"You are about to delete the Data Bundle *{db.name}*",
                        callback_delete_data_bundle,
                        db=db,
                    )

        st.write("")
        if st.button(
            "Add a Data Bundle", key=f"config-data-bundle-add-{endpoint_index}"
        ):
            dialog_data_bundle_form()

with st.container(horizontal=True, horizontal_alignment="right"):
    st.markdown(
        decorate_doc_links(
            "More on SPARQL endpoints in the [Documentation FAQ](/documentation?section=what-is-a-sparql-endpoint)"
        ),
        width="content",
    )
    st.markdown(
        decorate_doc_links(
            "More on data bundles in the [Documentation FAQ](/documentation?section=what-are-data-bundles)"
        ),
        width="content",
    )
