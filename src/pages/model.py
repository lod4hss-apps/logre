import streamlit as st
import json
from components.init import init
from components.menu import menu
from lib import state
from lib.shacl_maker import load_shacl_maker_js
from dialogs.confirmation import dialog_confirmation

# Initialize
init("wide", required_query_params=["endpoint", "db"])
menu()

# From state
data_bundle = state.get_data_bundle()
entity_uri = state.get_entity_uri()

if not data_bundle:
    st.warning("No data bundle selected.")
    st.stop()

# Title
col1, col2 = st.columns([5, 1], vertical_alignment="center")
col1.title("Data Bundle model")
col1.text("")

with col2.container(horizontal=True, horizontal_alignment="right"):
    if st.button(
        "Clear model",
        icon=":material/delete:",
        type="tertiary",
        help="Delete all SHACL triples from the model graph.",
    ):

        def clear_model_graph() -> None:
            data_bundle.model.delete([("?s", "?p", "?o")])
            data_bundle.load_model()
            state.invalidate_caches("clear_model")
            state.set_toast("Model cleared", icon=":material/delete:")

        dialog_confirmation(
            "You are about to clear the current model graph. This cannot be undone.",
            callback=clear_model_graph,
        )

st.info(
    "- This model view focuses on class-to-class structure and hides datatype properties (e.g. xsd:*).\n"
    "- To append SHACL profile(s), use the Import, Export page.",
    icon=":material/info:",
)

# with col2.container(horizontal=True, horizontal_alignment='right'):
# if st.button('Save'):
#   def replace_model() -> None:
#     # Clear old model
#     data_bundle.model.delete(('?s', '?p', '?o'))
#     # Upload new Turtle
#     graph_uri = data_bundle.prefixes.lengthen(data_bundle.graph_model.uri)
#     prefixes = json.dumps('\n'.join(list(map(lambda prefix: prefix.to_turtle(), data_bundle.prefixes))).split('<'))
#     st.html(f"""
#         <script>
#             var endpointTechnology = "{data_bundle.endpoint.technology_name}";
#             var username = "{data_bundle.endpoint.username}";
#             var password = "{data_bundle.endpoint.password}";
#             var url = "{data_bundle.endpoint.url}";
#             var graphURI = "{graph_uri}";
#             var prefixes = {prefixes}.join("<");
#             uploadTurtle(endpointTechnology, username, password, url, graphURI, prefixes);
#         </script>
#     """, unsafe_allow_javascript=True)
#   dialog_confirmation("Your are about to clear your model Named Graph and replace it by what is currently displayed.", replace_model, rerun=False)

# Get the js code
js_code, load_error = load_shacl_maker_js()
if js_code is None:
    st.warning(
        "Unable to load shacl-maker.js automatically. "
        f"Reason: {load_error}. "
        "Run `make install` locally or rebuild the Docker image to fetch it."
    )
    st.stop()


def _is_datatype_range(prop: dict) -> bool:
    range_info = prop.get("range") or {}
    range_uri = range_info.get("uri") if isinstance(range_info, dict) else None
    if not isinstance(range_uri, str):
        return False
    return range_uri.startswith("xsd:") or range_uri in {
        "rdfs:Datatype",
        "rdf:langString",
    }


properties = [prop.to_dict() for prop in data_bundle.model.properties]
properties = [prop for prop in properties if not _is_datatype_range(prop)]
properties_string = json.dumps(properties, ensure_ascii=False)

st.components.v1.html(
    f"""
    <style>
      html, body {{
        margin: 0;
        padding: 0;
        height: 100%;
      }}
      #canvas-wrapper {{
        width: 100%;
        height: 100%;
        min-height: 520px;
      }}
      #canvas-shacl-maker {{
        display: block;
        width: 100%;
        height: 100%;
      }}
    </style>

    <div id="canvas-wrapper">
      <canvas id="canvas-shacl-maker" tabindex="0"></canvas>
    </div>

    <script>{js_code}</script>
    <script>
      (function () {{
        const triples = {properties_string};
        let initialized = false;

        function setModelCanvasSize() {{
          const wrapper = document.getElementById("canvas-wrapper");
          const canvas = document.getElementById("canvas-shacl-maker");
          if (!wrapper || !canvas) return false;

          const rect = wrapper.getBoundingClientRect();
          const height = Math.max(520, window.innerHeight - rect.top - 24);
          const width = wrapper.clientWidth;
          if (width <= 0 || height <= 0) return false;

          wrapper.style.height = height + "px";
          canvas.width = width;
          canvas.height = height;
          return true;
        }}

        function layoutAndDraw() {{
          if (!setModelCanvasSize()) return;
          if (typeof draw === "function") draw();
        }}

        function initCanvas() {{
          const canvas = document.getElementById("canvas-shacl-maker");
          if (!canvas || typeof setCanvas !== "function") return false;
          if (!setModelCanvasSize()) return false;
          if (!initialized) {{
            setCanvas(canvas);
            addTriples(triples);
            initialized = true;
          }}
          layoutAndDraw();
          return true;
        }}

        function bindListeners() {{
          if (window.__logreModelListenersBound) return;
          window.addEventListener("resize", layoutAndDraw);
          document.addEventListener("visibilitychange", function () {{
            if (!document.hidden) setTimeout(layoutAndDraw, 0);
          }});

          if (window.ResizeObserver) {{
            const wrapper = document.getElementById("canvas-wrapper");
            if (wrapper) {{
              window.__logreModelResizeObserver = new ResizeObserver(layoutAndDraw);
              window.__logreModelResizeObserver.observe(wrapper);
            }}
          }}

          window.__logreModelListenersBound = true;
        }}

        function boot(attempt) {{
          const currentAttempt = attempt || 0;
          if (initCanvas()) {{
            bindListeners();
            requestAnimationFrame(layoutAndDraw);
            setTimeout(layoutAndDraw, 120);
            return;
          }}
          if (currentAttempt < 60) {{
            setTimeout(function () {{
              boot(currentAttempt + 1);
            }}, 50);
          }}
        }}

        if (document.readyState === "loading") {{
          document.addEventListener("DOMContentLoaded", function () {{
            boot(0);
          }}, {{ once: true }});
        }} else {{
          boot(0);
        }}

        window.addEventListener("load", function () {{
          setTimeout(layoutAndDraw, 0);
        }}, {{ once: true }});
      }})();
    </script>
""",
    height=760,
)

# st.title('How to...')

# st.markdown('##### ... select a box or a link?')
# st.markdown('> Simply click on it.')

# st.markdown('##### ... unselect a box or a link?')
# st.markdown('> Simply click on the empty space.')

# st.markdown('##### ... create a new box?')
# st.markdown('> When nothing is selected, press on "b" on your keyboard (canvas should be focused).')

# st.markdown('##### ... edit a box (class URI or name)?')
# st.markdown('> When a box(es) is(are) selected, simply hit the keyboard, this will change the box content. Remember that first line is the class URI, and second is the class name.')

# st.markdown('##### ... move one or multiple boxes?')
# st.markdown('> To move something, you need to select it, and then drag and drop on the canvas.')

# st.markdown('##### ...move everything?')
# st.markdown('> To move everything - or said otherwise, to move the camera - just have nothing selected and drag and drop')

# st.markdown('##### ... zoom or unzoom?')
# st.markdown('> Use your wheeler (mouse or pad) to zoom or unzoom. There is also a way of fitting all your model in the canvas at once: press "z" key.')

# st.markdown('##### ... link two boxes?')
# st.markdown('> When nothing is selected, press "l" key, that will activate the create link mode (not visible at this point). Then you need to click on the first box concerned by the link (the subject). Your will then see your mouse linked to the box. Finally, click on the target (the object). You have then created a link (a predicate)!')

# st.markdown('##### ... change information of a link?')
# st.markdown('> When a link is selected, you just can hit the keyboard, and it will start the update. To update the predicate label, write "label: " followed by the label you would like to set/update. To update the URI of the link, write "uri: " followed by the uri you want to set/update. To update the cardinatlity of the link, write "card: " followed by the cardinality you want to set/update (eg: "0..3" or "0..\*" or "1"). To update the order of appearance of the property in formular, write "order: " followed by the order you want to set/update. You can also update multiple attribute at once, for example you can write "uri: rdfs:label - label: has name - card: 0..\*"')
