import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from requests.exceptions import HTTPError, ConnectionError

from components.init import init
from components.menu import menu
from schema.data_bundle import DataBundle
from lib import state
from lib.errors import get_HTTP_ERROR_message
from lib.stats import summarize_classes, summarize_properties


# Initialize application context
init(layout='wide', required_query_params=['endpoint', 'db'])
menu()


def show_metrics(overview: dict) -> None:
    """Display aggregated metrics for the data bundle."""
    counts = overview["counts"]

    col_title_model, col_title_data = st.columns(2)
    with col_title_model.container(horizontal=True, horizontal_alignment="center"):
        st.markdown('### Model', width="content")
    with col_title_data.container(horizontal=True, horizontal_alignment="center"):
        st.markdown('### Data', width="content")

    col_classes, col_props, col_entities, col_triples = st.columns(4)
    metrics_model = [
        (col_classes, "Classes", counts['classes']),
        (col_props, "Properties", counts['properties']),
    ]
    metrics_data = [
        (col_entities, "Entities", counts['entities']),
        (col_triples, "Triples", counts['triples']),
    ]

    for col, label, value in metrics_model:
        with col.container(horizontal=True, horizontal_alignment='center'):
            st.metric(label, format_short(value), width="content")

    for col, label, value in metrics_data:
        with col.container(horizontal=True, horizontal_alignment='center'):
            st.metric(label, format_short(value), width="content")


def show_top_classes(overview: dict) -> None:
    """Display a table with the most populated classes in the data bundle."""
    top_classes = overview["top_classes"]
    if not top_classes:
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
        )

    with charts[1]:
        render_pie_chart(
            values=[row["count"] for row in prop_stats["top"]],
            labels=[row["label"] for row in prop_stats["top"]],
            title=f"Propriétés (Top {len(prop_stats['top'])})",
        )


def render_pie_chart(values, labels, title: str) -> None:
    """Helper to draw consistent donut charts."""
    if not values:
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


@st.cache_data(ttl=60, hash_funcs={DataBundle: lambda db: db.key}, show_spinner=False)
def get_dashboard_overview(data_bundle: DataBundle) -> dict:
    """
    Gather counts and top classes from the active data bundle.
    """
    counts = get_counts(data_bundle)
    top_classes = get_top_classes(data_bundle, counts["entities"])
    top_properties = get_top_properties(data_bundle, counts["triples"])
    warnings = []
    return {"counts": counts, "top_classes": top_classes, "top_properties": top_properties, "warnings": warnings}


def get_counts(data_bundle: DataBundle) -> dict:
    """
    Retrieve total number of entities, classes and triples in the bundle.
    """
    counts = {"entities": 0, "classes": 0, "properties": 0, "triples": 0}

    query_entities = f"""
        SELECT 
            (COUNT(?instance) AS ?entity_count) 
            (COUNT(DISTINCT ?class) AS ?class_count)
        WHERE {{ 
            {data_bundle.data.sparql_begin}
                ?instance {data_bundle.model.type_property} ?class .
            {data_bundle.data.sparql_end}
        }}
    """
    response_entities = data_bundle.data.run(query_entities)
    if response_entities:
        counts["entities"] = _to_int(response_entities[0].get("entity_count"))
        counts["classes"] = _to_int(response_entities[0].get("class_count"))

    query_props = f"""
        SELECT (COUNT(DISTINCT ?property) AS ?prop_count)
        WHERE {{
            {data_bundle.data.sparql_begin}
                ?subject ?property ?object .
            {data_bundle.data.sparql_end}
        }}
    """
    response_props = data_bundle.data.run(query_props)
    if response_props:
        counts["properties"] = _to_int(response_props[0].get("prop_count"))

    query_triples = f"""
        SELECT (COUNT(*) AS ?triples_count)
        WHERE {{
            {data_bundle.data.sparql_begin}
                ?s ?p ?o .
            {data_bundle.data.sparql_end}
        }}
    """
    response_triples = data_bundle.data.run(query_triples)
    if response_triples:
        counts["triples"] = _to_int(response_triples[0].get("triples_count"))

    return counts


def get_top_classes(data_bundle: DataBundle, total_entities: int, limit: int = 5) -> list[dict]:
    """
    Retrieve the most populated classes in the bundle.
    """
    query = f"""
        SELECT ?class (COUNT(?instance) AS ?count)
        WHERE {{
            {data_bundle.data.sparql_begin}
                ?instance {data_bundle.model.type_property} ?class .
            {data_bundle.data.sparql_end}
        }}
        GROUP BY ?class
        ORDER BY DESC(?count)
        LIMIT {limit}
    """
    response = data_bundle.data.run(query)
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


def get_top_properties(data_bundle: DataBundle, total_triples: int, limit: int = 5) -> list[dict]:
    query = f"""
        SELECT ?property (COUNT(*) AS ?count)
        WHERE {{
            {data_bundle.data.sparql_begin}
                ?subject ?property ?object .
            {data_bundle.data.sparql_end}
        }}
        GROUP BY ?property
        ORDER BY DESC(?count)
        LIMIT {limit}
    """
    response = data_bundle.data.run(query)
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


def show_configuration_panel() -> None:
    """Render a discrete configuration block with bundle selector and graph reminders."""

    # From state
    endpoint = state.get_endpoint()
    data_bundle = state.get_data_bundle()

    if endpoint:
        st.markdown(f"**Endpoint**: {endpoint.name}")
    
    if data_bundle:
        st.markdown(f"**Data bundle**: {data_bundle.name}")
        st.caption(f"Base URI: {data_bundle.base_uri}")
        st.markdown(
            f"""
            - **Data graph**: `{data_bundle.data.uri or '*Default Graph*'}`
            - **Model graph**: `{data_bundle.model.uri or '*Default Graph*'}`
            - **Metadata graph**: `{data_bundle.metadata.uri or '*Default Graph*'}`
            """
        )
        # try:
        model_count_query = f"""
            SELECT (COUNT(*) AS ?count)
            WHERE {{
                {data_bundle.model.sparql_begin}
                    ?s ?p ?o .
                {data_bundle.model.sparql_end}
            }}
        """
        model_count_resp = data_bundle.model.run(model_count_query) or []
        model_count = _to_int(model_count_resp[0]['count']) if model_count_resp else 0
        # except Exception:
        #     model_count = 0
        if model_count == 0:
            st.warning("You do not have any model yet. Import one from the Import/export page to enable entity creation.")
        st.caption("See [How to configure data bundles](/documentation#how-to-create-a-data-bundle) for details.")


def show_data_insights(overview, data_bundle):
    """Grouped visualisation for metrics, charts and tables."""
    show_metrics(overview)
    
    chart_section = st.container()
    with chart_section:
        show_pie_charts(data_bundle)

    # table_section = st.container()
    # with table_section:
    #     st.caption("Top 5 classes")
    #     show_top_classes(overview)
    #     st.caption("Top 5 properties")
    #     show_top_properties(overview)


try:
    data_bundle = state.get_data_bundle()
    data_bundles = state.get_data_bundles()

    if not data_bundle:
        st.switch_page('server.py')
    else:
        with st.spinner('Loading statistics...'):
            overview = get_dashboard_overview(data_bundle)

            if overview["warnings"]:
                for warning in overview["warnings"]:
                    st.info(warning, icon=":material/info:")

            show_data_insights(overview, data_bundle)

    st.divider()
    show_configuration_panel()

except HTTPError as err:
    message = get_HTTP_ERROR_message(err)
    st.error(message)
    print(message.replace('\n\n', '\n'))

except ConnectionError:
    st.error('Failed to connect to server: check your internet connection and/or server status.')
    print('[CONNECTION ERROR]')
