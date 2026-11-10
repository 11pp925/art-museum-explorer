"""Art Museum Explorer Plus — student extension of MET Museum API classroom example."""
import requests
import streamlit as st

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects"

st.set_page_config(page_title="Art Museum Explorer Plus", page_icon="🎨", layout="wide")
st.markdown("""<style>
.block-container {max-width: 1200px; padding-top: 2rem;}
h1 {letter-spacing: -.03em;}
[data-testid="stVerticalBlockBorderWrapper"] {border-radius: 14px;}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=3600, show_spinner=False)
def search_ids(query, limit):
    r = requests.get(SEARCH_URL, params={"q": query, "hasImages": "true", "limit": limit}, timeout=30)
    r.raise_for_status()
    return r.json().get("objectIDs") or []

@st.cache_data(ttl=3600, show_spinner=False)
def get_object(object_id):
    r = requests.get(f"{OBJECT_URL}/{object_id}", timeout=20)
    r.raise_for_status()
    return r.json()

if "favorites" not in st.session_state:
    st.session_state.favorites = {}
if "results" not in st.session_state:
    st.session_state.results = []
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

st.title("🎨 Art Museum Explorer Plus")
st.caption("An interactive digital gallery powered by The Metropolitan Museum of Art Collection API")
st.write("Search artworks, discover their stories, and build a personal mini-gallery.")

with st.sidebar:
    st.header("Explore")
    query = st.text_input("Keyword", value="flower", placeholder="e.g. flower, cat, ocean")
    count = st.slider("Search candidates", min_value=6, max_value=36, value=18, step=6)
    category = st.selectbox("Object type", ["All types", "Paintings", "Sculpture", "Drawings", "Photographs", "Other"])
    view = st.radio("Gallery", ["Explore artworks", "My favorites"])
    search_clicked = st.button("🔎 Search artworks", use_container_width=True, type="primary")
    st.caption("Favorites are saved only during this browser session.")

def matches_category(art, selected):
    if selected == "All types":
        return True
    value = " ".join(str(art.get(k) or "") for k in ("classification", "objectName")).lower()
    terms = {
        "Paintings": ("painting",),
        "Sculpture": ("sculpture", "statue", "figurine", "bust"),
        "Drawings": ("drawing",),
        "Photographs": ("photograph", "negative"),
    }
    if selected == "Other":
        return not any(any(t in value for t in ts) for ts in terms.values())
    return any(term in value for term in terms[selected])

if search_clicked and query.strip():
    with st.spinner("Contacting the museum API..."):
        try:
            ids = search_ids(query.strip(), count)
            artworks = []
            for object_id in ids:
                try:
                    art = get_object(object_id)
                    if art.get("primaryImageSmall"):
                        artworks.append(art)
                except (requests.RequestException, ValueError):
                    continue
            st.session_state.results = artworks
            st.session_state.last_query = query.strip()
        except (requests.RequestException, ValueError) as exc:
            st.error(f"Museum API request failed: {exc}")
elif search_clicked:
    st.warning("Enter a keyword to search.")

if view == "My favorites":
    artworks = list(st.session_state.favorites.values())
    st.subheader(f"My favorites · {len(artworks)}")
    if not artworks:
        st.info("No favorites yet. Search for artworks and click Save to favorites.")
else:
    artworks = st.session_state.results
    st.subheader("Explore artworks")
    if st.session_state.last_query:
        st.caption(f"Results for: {st.session_state.last_query}")
    else:
        st.info("Enter a keyword and click Search artworks to begin.")

visible = [art for art in artworks if matches_category(art, category)]
if artworks and not visible:
    st.info("No matching artworks in the fetched candidates. Try All types or a larger search count.")
if visible:
    st.caption(f"Showing {len(visible)} artwork(s) after filtering. Categories apply to fetched results, not the full museum collection.")

for start in range(0, len(visible), 3):
    cols = st.columns(3)
    for col, art in zip(cols, visible[start:start + 3]):
        object_id = art.get("objectID")
        with col:
            with st.container(border=True):
                st.image(art["primaryImageSmall"], use_container_width=True)
                st.markdown(f"**{art.get('title') or 'Untitled'}**")
                st.caption(f"{art.get('artistDisplayName') or 'Unknown artist'} · {art.get('objectDate') or 'Date unknown'}")
                with st.expander("Artwork details"):
                    st.write("**Department:**", art.get("department") or "Unknown")
                    st.write("**Classification:**", art.get("classification") or "Unknown")
                    st.write("**Medium:**", art.get("medium") or "Unknown")
                    st.write("**Culture:**", art.get("culture") or "Unknown")
                    if art.get("objectURL"):
                        st.link_button("View at The Met", art["objectURL"])
                saved = object_id in st.session_state.favorites
                if st.button("♥ Remove favorite" if saved else "♡ Save to favorites", key=f"fav_{view}_{object_id}", use_container_width=True):
                    if saved:
                        del st.session_state.favorites[object_id]
                    else:
                        st.session_state.favorites[object_id] = art
                    st.rerun()

st.divider()
st.caption("Source: The Metropolitan Museum of Art Collection API. Artworks and images are subject to the museum's available records and image rights. This is an educational project.")
