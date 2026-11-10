# Open API Service 1 - Explore Artworks with the MET Museum API
# The museum keeps the data. Our app asks for it and displays it.

import requests
import streamlit as st

SEARCH_URL = "https://collectionapi.metmuseum.org/public/collection/v1.1/search"
OBJECT_URL = "https://collectionapi.metmuseum.org/public/collection/v1/objects"


@st.cache_data(ttl=3600)  # remember answers for 1 hour
def search_ids(query, limit):
    """Step 1: search returns only a list of object IDs."""
    resp = requests.get(
        SEARCH_URL,
        params={"q": query, "hasImages": "true", "limit": limit},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("objectIDs") or []   # no results gives null, so use []


@st.cache_data(ttl=3600)
def get_object(object_id):
    """Step 2: ask for the details of one artwork."""
    resp = requests.get(f"{OBJECT_URL}/{object_id}", timeout=10)
    resp.raise_for_status()
    return resp.json()


st.set_page_config(page_title="Explore Artworks", layout="centered")
st.title("Explore Artworks with the MET Museum API")
st.caption("Arts and Advanced Big Data | Open API, Service 1")

query = st.text_input("Search for Artworks", "flower")
count = st.slider("How many artworks to show", 3, 12, 6)

if query.strip():
    try:
        ids = search_ids(query.strip(), count)
        if not ids:
            st.info("No artworks found. Try another word, for example: cat, ocean, gold.")
        cols = st.columns(3)
        for i, object_id in enumerate(ids):
            art = get_object(object_id)
            image = art.get("primaryImageSmall")
            if not image:
                continue
            with cols[i % 3]:
                st.image(image, width="stretch")
                st.markdown(f"**{art.get('title', 'Untitled')}**")
                st.write(f"Artist: {art.get('artistDisplayName') or 'Unknown'}")
                st.write(f"Year: {art.get('objectDate') or 'Unknown'}")
                if art.get("objectURL"):
                    st.markdown(f"[View at the Met]({art['objectURL']})")
    except requests.RequestException:
        st.error("Could not reach the museum's service right now. Please try again in a minute.")

st.caption("Data: The Metropolitan Museum of Art Collection API (Open Access, CC0).")
