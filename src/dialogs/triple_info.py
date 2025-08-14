import streamlit as st
from model import Statement
from lib import state

@st.dialog('Triple information')
def dialog_triple_info(triple: Statement) -> None:
    """
    Dialog function to display basic information about a triple.

    Args:
        triple (Statement): The statement to display information from.
    """

    # From state
    endpoint = state.get_endpoint()
    
    ### Subject ###

    st.markdown('### Subject')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{triple.subject.uri}]({endpoint.sparql.unroll_uri(triple.subject.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(triple.subject.label)

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Comment**")
    col2.markdown(triple.subject.comment)

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**Class**")
    col2.markdown(f"{triple.subject.class_label} ([{triple.subject.class_uri}]({endpoint.sparql.unroll_uri(triple.subject.class_uri)}))")

    st.divider()

    ### Predicate ###

    st.markdown('### Predicate')
    col1, col2 = st.columns([1, 3])

    col1, col2 = st.columns([1, 3])
    col1.markdown(f"**URI**")
    col2.markdown(f"[{triple.predicate.uri}]({endpoint.sparql.unroll_uri(triple.predicate.uri)})")

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Label**")
    col2.markdown(triple.predicate.label or '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Order**")
    col2.markdown(triple.predicate.order if triple.predicate.order != 1000000000000000000 else '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Cardinality**")
    from_count = triple.predicate.min_count or '0'
    to_count = triple.predicate.max_count or 'n' if triple.predicate.max_count != 1000000000000000000 else 'n'
    col2.markdown(f"{from_count} to {to_count}")
    
    col1, col2 = st.columns([1, 3])
    col1.markdown("**Domain class**")
    col2.markdown(triple.predicate.domain_class_uri or '')

    col1, col2 = st.columns([1, 3])
    col1.markdown("**Range class**")
    col2.markdown(triple.predicate.range_class_uri or '')

    st.divider()

    ### Object ###

    # If the object is a value
    if triple.object.is_literal:
        st.markdown('### Object (Literal)')
        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Value**")
        col2.markdown(triple.object.label)

    # If the object is a class instance
    else:
        st.markdown('### Object')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**URI**")
        col2.markdown(f"[{triple.object.uri}]({endpoint.sparql.unroll_uri(triple.object.uri)})")

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Label**")
        col2.markdown(triple.object.label)

        col1, col2 = st.columns([1, 3])
        col1.markdown("**Comment**")
        col2.markdown(triple.object.comment or '')

        col1, col2 = st.columns([1, 3])
        col1.markdown(f"**Class**")
        first_part = triple.object.class_label or ''
        second_part = f" ([{triple.object.class_uri}]({endpoint.sparql.unroll_uri(triple.object.class_uri)}))" if triple.object.class_uri else ""
        col2.markdown(first_part + second_part)



