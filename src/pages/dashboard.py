import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from requests.exceptions import HTTPError, ConnectionError

from components.help import help_text
from components.init import init
from components.menu import menu
from dialogs.entity_creation import dialog_entity_creation
from dialogs.find_entity import dialog_find_entity
from lib import state
from lib.errors import get_HTTP_ERROR_message
from lib.stats import summarize_classes, summarize_properties


# Initialize application context
init(layout='wide', query_param_keys=['endpoint', 'db'])
menu()


def show_metrics(overview: dict) -> None:
    """Display aggregated metrics for the data bundle."""
    counts = overview["counts"]
    col_entities, col_classes, col_props, col_triples = st.columns(4)
    metrics = [
        (col_entities, "Entities", counts['entities']),
        (col_classes, "Classes", counts['classes']),
        (col_props, "Properties", counts['properties']),
        (col_triples, "Triples", counts['triples']),
    ]
    for col, label, value in metrics:
        col.metric(label, format_short(value))


def show_quick_actions() -> None:
    """Display the primary actions prominently at the top."""
    data_bundle = state.get_data_bundle()
    model_ready = bool(data_bundle and data_bundle.has_model_definitions())
    disabled_help = "Import a SHACL model to enable this action." if data_bundle and not model_ready else None
    actions = st.columns(3)
    with actions[0]:
        st.button(
            'Find entity',
            icon=':material/search:',
            type='primary',
            use_container_width=True,
            on_click=dialog_find_entity,
            disabled=not model_ready,
            help=disabled_help or help_text("dashboard.find_entity")
        )
    with actions[1]:
        st.button(
            'Create entity',
            icon=':material/line_start_circle:',
            type='primary',
            use_container_width=True,
            on_click=dialog_entity_creation,
            disabled=not model_ready,
            help=disabled_help or help_text("dashboard.create_entity")
        )
    with actions[2]:
        if st.button('Export a table', icon=':material/download:', use_container_width=True, help=help_text("dashboard.export")):
            st.switch_page("pages/data-table.py")
    if data_bundle and not model_ready:
        st.caption("Import a SHACL model from the Configuration page to enable Find/Create.")


def show_top_classes(overview: dict) -> None:
    """Display a table with the most populated classes in the data bundle."""
    top_classes = overview["top_classes"]
    if not top_classes:
        st.caption("Unable to compute the most populated classes right now.")
        return

    df = pd.DataFrame(top_classes)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Class": st.column_config.TextColumn("Class"),
            "Instances": st.column_config.NumberColumn("Instances"),
            "Share": st.column_config.NumberColumn("Share (%)", format="%.1f %%"),
        },
    )

def show_top_properties(overview: dict) -> None:
    """Display a table with the most used properties in the data bundle."""
    top_props = overview.get("top_properties")
    if not top_props:
        st.caption("Unable to compute the most used properties right now.")
        return

    df = pd.DataFrame(top_props)
    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Property": st.column_config.TextColumn("Property"),
            "Triples": st.column_config.NumberColumn("Triples"),
            "Share": st.column_config.NumberColumn("Share (%)", format="%.1f %%"),
        },
    )

def show_pie_charts(data_bundle) -> None:
    """Display the class/property distributions previously exposed in the Statistics page."""
    classes_stats = summarize_classes(data_bundle)
    prop_stats = summarize_properties(data_bundle)

    charts = st.columns(2)
    with charts[0]:
        render_pie_chart(
            values=[row["count"] for row in classes_stats["top"]],
            labels=[row["label"] for row in classes_stats["top"]],
            title=f"Classes (Top {len(classes_stats['top'])})",
            empty_message="Aucune entité pour le moment",
        )

    with charts[1]:
        render_pie_chart(
            values=[row["count"] for row in prop_stats["top"]],
            labels=[row["label"] for row in prop_stats["top"]],
            title=f"Propriétés (Top {len(prop_stats['top'])})",
            empty_message="Aucune propriété détectée",
        )


def render_pie_chart(values, labels, title: str, empty_message: str) -> None:
    """Helper to draw consistent donut charts."""
    if not values:
        st.caption(empty_message)
        return

    chart = go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        textposition="inside",
        textinfo="percent+label",
        marker_colors=['rgb(255, 230, 204)', 'rgb(255, 216, 179)', 'rgb(255, 204, 153)', 'rgb(255, 191, 128)', 'rgb(255, 179, 102)', 'rgb(255, 165, 77)', 'rgb(255, 153, 51)', 'rgb(255, 140, 26)', 'rgb(255, 127, 0)']
    )
    fig = go.Figure()
    fig.add_trace(chart)
    fig.update_layout(showlegend=False, title=title, title_x=0.0)
    st.plotly_chart(fig, use_container_width=True)


def get_dashboard_overview(data_bundle) -> dict:
    """
    Gather counts and top classes from the active data bundle.
    """
    counts = get_counts(data_bundle)
    top_classes = get_top_classes(data_bundle, counts["entities"])
    top_properties = get_top_properties(data_bundle, counts["triples"])
    warnings = []
    if counts["entities"] == 0:
        warnings.append("This bundle does not contain any entity yet. Import data or create your first entity.")
    return {"counts": counts, "top_classes": top_classes, "top_properties": top_properties, "warnings": warnings}


def get_counts(data_bundle) -> dict:
    """
    Retrieve total number of entities, classes and triples in the bundle.
    """
    counts = {"entities": 0, "classes": 0, "properties": 0, "triples": 0}

    query_entities = f"""
        SELECT 
            (COUNT(?instance) AS ?entity_count) 
            (COUNT(DISTINCT ?class) AS ?class_count)
        WHERE {{ 
            {data_bundle.graph_data.sparql_begin}
                ?instance {data_bundle.model.type_property} ?class .
            {data_bundle.graph_data.sparql_end}
        }}
    """
    response_entities = data_bundle.graph_data.run(query_entities, data_bundle.prefixes)
    if response_entities:
        counts["entities"] = _to_int(response_entities[0].get("entity_count"))
        counts["classes"] = _to_int(response_entities[0].get("class_count"))

    query_props = f"""
        SELECT (COUNT(DISTINCT ?property) AS ?prop_count)
        WHERE {{
            {data_bundle.graph_data.sparql_begin}
                ?subject ?property ?object .
            {data_bundle.graph_data.sparql_end}
        }}
    """
    response_props = data_bundle.graph_data.run(query_props, data_bundle.prefixes)
    if response_props:
        counts["properties"] = _to_int(response_props[0].get("prop_count"))

    query_triples = f"""
        SELECT (COUNT(*) AS ?triples_count)
        WHERE {{
            {data_bundle.graph_data.sparql_begin}
                ?s ?p ?o .
            {data_bundle.graph_data.sparql_end}
        }}
    """
    response_triples = data_bundle.graph_data.run(query_triples, data_bundle.prefixes)
    if response_triples:
        counts["triples"] = _to_int(response_triples[0].get("triples_count"))

    return counts


def get_top_classes(data_bundle, total_entities: int, limit: int = 5) -> list[dict]:
    """
    Retrieve the most populated classes in the bundle.
    """
    query = f"""
        SELECT ?class (COUNT(?instance) AS ?count)
        WHERE {{
            {data_bundle.graph_data.sparql_begin}
                ?instance {data_bundle.model.type_property} ?class .
            {data_bundle.graph_data.sparql_end}
        }}
        GROUP BY ?class
        ORDER BY DESC(?count)
        LIMIT {limit}
    """
    response = data_bundle.graph_data.run(query, data_bundle.prefixes)
    if not response:
        return []

    rows = []
    for row in response:
        cls = data_bundle.model.find_class(row["class"])
        count = _to_int(row["count"])
        share = (count / total_entities * 100) if total_entities else 0
        label = cls.get_text() if cls else data_bundle.prefixes.shorten(row["class"])
        rows.append({"Class": label, "Instances": count, "Share": share})
    return rows


def get_top_properties(data_bundle, total_triples: int, limit: int = 5) -> list[dict]:
    query = f"""
        SELECT ?property (COUNT(*) AS ?count)
        WHERE {{
            {data_bundle.graph_data.sparql_begin}
                ?subject ?property ?object .
            {data_bundle.graph_data.sparql_end}
        }}
        GROUP BY ?property
        ORDER BY DESC(?count)
        LIMIT {limit}
    """
    response = data_bundle.graph_data.run(query, data_bundle.prefixes)
    if not response:
        return []

    rows = []
    for row in response:
        props = data_bundle.model.find_properties(row["property"])
        label = props[0].label if props and props[0].label else data_bundle.prefixes.shorten(row["property"])
        count = _to_int(row["count"])
        share = (count / total_triples * 100) if total_triples else 0
        rows.append({"Property": label, "Triples": count, "Share": share})
    return rows


def _to_int(value) -> int:
    """
    Safe conversion helper so SPARQL numeric strings are cast into integers.
    """
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def format_short(value: int) -> str:
    """
    Format large numbers using short notation (e.g., 8.3k, 9.2M).
    """
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}k"
    return f"{value:,}"


def show_configuration_panel(current_bundle, data_bundles):
    """Render a discrete configuration block with bundle selector and graph reminders."""
    if not data_bundles:
        st.info("No data bundle configured yet. Visit the Configuration page to create one.", icon=":material/info:")
        return

    with st.expander("Configuration & context (overview)", expanded=False):
        endpoint_groups = state.get_endpoint_groups()
        if not endpoint_groups:
            st.info("Configure an endpoint and a Data Bundle from the Configuration page.", icon=":material/info:")
            return

        endpoint_key = state.get_endpoint_key()
        endpoint_labels = [group['label'] for group in endpoint_groups]
        endpoint_index = 0
        if endpoint_key:
            endpoint_index = next((i for i, group in enumerate(endpoint_groups) if group['key'] == endpoint_key), 0)

        st.caption("Need to edit bundles, prefixes or import data? Head to the full [Configuration page](/configuration).")
        selected_endpoint_label = st.selectbox(
            "Active endpoint",
            options=endpoint_labels,
            index=endpoint_index,
            key="dashboard-endpoint-select"
        )
        selected_endpoint = endpoint_groups[endpoint_labels.index(selected_endpoint_label)]
        if endpoint_key != selected_endpoint['key']:
            state.set_endpoint_key(selected_endpoint['key'])
            st.rerun()

        bundles = selected_endpoint['data_bundles']
        active = current_bundle if current_bundle in bundles else None
        bundle_names = [db.name for db in bundles]

        if bundles:
            bundle_index = bundle_names.index(active.name) if active else 0
            selected_bundle_label = st.selectbox(
                "Active data bundle",
                options=bundle_names,
                index=bundle_index,
                key="dashboard-bundle-select",
                help=help_text("dashboard.data_bundle_select")
            )
            selected_bundle = bundles[bundle_names.index(selected_bundle_label)]
            if current_bundle != selected_bundle:
                state.set_data_bundle(selected_bundle)
                st.rerun()
            active = selected_bundle
        else:
            st.warning("This endpoint has no configured Data Bundle yet.", icon=":material/info:")
            active = None

        if active:
            st.caption(f"Endpoint: {active.endpoint.url}")
            st.caption(f"Base URI: {active.base_uri}")
            st.markdown(
                f"""
                - **Data graph**: `{active.graph_data.uri or 'default graph'}`
                - **Model graph**: `{active.graph_model.uri or 'default graph'}`
                - **Metadata graph**: `{active.graph_metadata.uri or 'default graph'}`
                """
            )
            try:
                model_count_query = f"""
                    SELECT (COUNT(*) AS ?count)
                    WHERE {{
                        {active.graph_model.sparql_begin}
                            ?s ?p ?o .
                        {active.graph_model.sparql_end}
                    }}
                """
                model_count_resp = active.graph_model.run(model_count_query, active.prefixes) or []
                model_count = _to_int(model_count_resp[0]['count']) if model_count_resp else 0
            except Exception:
                model_count = 0
            if model_count == 0:
                st.warning("Your SHACL model is empty. Import a model from the Configuration page before editing entities.")
            st.caption("See [How to configure data bundles](/documentation#how-to-create-a-data-bundle) for details.")


def show_data_insights(overview, data_bundle):
    """Grouped visualisation for metrics, charts and tables."""
    show_metrics(overview)

    chart_section = st.container()
    with chart_section:
        show_pie_charts(data_bundle)

    table_section = st.container()
    with table_section:
        st.caption("Top 5 classes")
        show_top_classes(overview)
        st.caption("Top 5 properties")
        show_top_properties(overview)


try:
    data_bundle = state.get_data_bundle()
    data_bundles = state.get_data_bundles()

    if not data_bundle:
        st.warning("Aucun data bundle actif pour le moment.")
        st.write(
            "Sélectionnez ou créez un bundle dans la section de configuration ci-dessous pour commencer."
        )
        st.caption("En savoir plus : [What are data bundles?](/documentation#what-are-data-bundles).")
    else:
        overview = get_dashboard_overview(data_bundle)

        if overview["warnings"]:
            for warning in overview["warnings"]:
                st.info(warning, icon=":material/info:")

        show_quick_actions()
        show_data_insights(overview, data_bundle)

    st.divider()
    show_configuration_panel(data_bundle, data_bundles)

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))

except ConnectionError:
    st.error('Failed to connect to server: check your internet connection and/or server status.')
    print('[CONNECTION ERROR]')
