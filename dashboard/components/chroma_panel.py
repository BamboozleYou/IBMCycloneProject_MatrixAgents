"""Similar cyclones panel — queries ChromaDB and renders cards."""
from __future__ import annotations

import streamlit as st


def render_similar_cyclones(docs: list[dict]) -> None:
    """Render ChromaDB RAG results as styled cards."""
    if not docs:
        st.info("No similar historical cyclones found in ChromaDB.")
        return

    st.markdown('<div class="section-head">Similar Historical Cyclones (ChromaDB RAG)</div>',
                unsafe_allow_html=True)
    for doc in docs:
        meta = doc.get("metadata", {})
        name     = meta.get("name", doc.get("id", "Unknown"))
        year     = meta.get("year", "")
        category = meta.get("category", "")
        region   = meta.get("landfall_region", "")
        summary  = doc.get("summary", "")

        cat_colour = "#0F62FE"
        if "Super" in category:       cat_colour = "#6929c4"
        elif "Extremely" in category: cat_colour = "#a61f1f"
        elif "Very Severe" in category: cat_colour = "#da1e28"
        elif "Severe" in category:    cat_colour = "#ff832b"
        elif "Cyclonic Storm" in category: cat_colour = "#f1c21b"

        st.markdown(
            f'<div class="similar-card">'
            f'<b style="color:#f4f4f4">{name}</b> '
            f'<span class="tag" style="background:{cat_colour}22;color:{cat_colour}">{year}</span>'
            f'<span class="tag" style="background:#39393944;color:#a8a8a8">{region}</span>'
            f'<br><span style="font-size:12px;color:#8d8d8d">{category}</span>'
            f'<p style="font-size:13px;color:#c6c6c6;margin:6px 0 0 0">{summary[:220]}…</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
