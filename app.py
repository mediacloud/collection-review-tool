import csv
import io
import os
from typing import Dict, List, TypedDict

import streamlit as st
from mediacloud.api import DirectoryApi


class MediaSource(TypedDict, total=False):
  media_id: int
  name: str
  url: str
  country: str
  language: str


class ReviewDecision(TypedDict):
  media_id: int
  action: str
  reason: str


API_KEY_ENV_VAR = "MEDIACLOUD_API_KEY"


@st.cache_resource
def get_directory_client() -> DirectoryApi:
  api_key = os.getenv(API_KEY_ENV_VAR)
  if not api_key:
    raise RuntimeError(
      f"Missing API key. Please set the {API_KEY_ENV_VAR} environment variable "
      "before running the app."
    )
  return DirectoryApi(api_key)


@st.cache_data(show_spinner="Loading collection media…")
def fetch_collection_media(collection_id: int) -> List[MediaSource]:
  """
  Fetch media sources in a collection using the Media Cloud DirectoryApi.

  This uses DirectoryApi.source_list filtered by collection_id.
  """
  client = get_directory_client()
  data = client.source_list(collection_id=collection_id, limit=500)

  # API may return sources under 'results' or 'sources' depending on version.
  raw_sources = data.get("results") or data.get("sources") or []

  media_list: List[MediaSource] = []
  for src in raw_sources:
    media_list.append(
      MediaSource(
        media_id=src.get("id") or src.get("media_id"),
        name=src.get("name") or src.get("label") or "",
        url=src.get("url") or src.get("homepage") or "",
        country=src.get("country", ""),
        language=src.get("language", ""),
      )
    )

  return media_list


def ensure_session_state():
  if "decisions" not in st.session_state:
    st.session_state["decisions"]: Dict[int, ReviewDecision] = {}


def main():
  st.set_page_config(page_title="UNDP Collections Inspector", layout="wide")
  st.title("UNDP Collections Inspector")
  st.write(
    "Review sources in a Media Cloud collection and mark each for **add**, "
    "**remove** (with explanation), or **no change**."
  )

  ensure_session_state()

  with st.sidebar:
    st.header("Collection")
    collection_id = st.number_input(
      "Collection ID",
      min_value=1,
      step=1,
      value=1,
      help="Enter the Media Cloud collection (tags) ID to review.",
    )
    load_clicked = st.button("Load collection", type="primary", use_container_width=True)

  media: List[MediaSource] = []

  if load_clicked:
    if not collection_id:
      st.error("Please enter a valid collection ID.")
    else:
      try:
        media = fetch_collection_media(int(collection_id))
        if not media:
          st.warning("No media sources found for this collection.")
        else:
          st.success(f"Loaded {len(media)} sources for collection {int(collection_id)}.")
      except Exception as exc:  # noqa: BLE001
        st.error(f"Error loading collection: {exc}")

      # Reset decisions when a new collection is loaded
      st.session_state["decisions"] = {}
      st.session_state["loaded_collection_id"] = int(collection_id)

  # If we've previously loaded a collection in this session, show its media
  if not media and "loaded_collection_id" in st.session_state:
    try:
      media = fetch_collection_media(int(st.session_state["loaded_collection_id"]))
    except Exception:
      media = []

  if media:
    st.subheader(f"Sources in collection {int(st.session_state['loaded_collection_id'])}")

    decisions: Dict[int, ReviewDecision] = st.session_state["decisions"]

    # Render each source with controls
    for source in media:
      media_id = source.get("media_id")
      if media_id is None:
        continue

      name = source.get("name", f"Media {media_id}")
      url = source.get("url", "")
      country = source.get("country", "")
      language = source.get("language", "")

      default_decision: ReviewDecision = {
        "media_id": int(media_id),
        "action": "unchanged",
        "reason": "",
      }
      decision = decisions.get(int(media_id), default_decision)

      st.markdown("---")
      cols = st.columns([3, 2])
      with cols[0]:
        st.markdown(f"**{name}**  `#{media_id}`")
        if url:
          st.markdown(f"[{url}]({url})")

        meta_bits = []
        if country:
          meta_bits.append(country)
        if language:
          meta_bits.append(language)
        if meta_bits:
          st.caption(" · ".join(meta_bits))

      with cols[1]:
        action = st.radio(
          "Decision",
          options=["unchanged", "add", "remove"],
          format_func=lambda v: {"unchanged": "No change", "add": "Add", "remove": "Remove"}[v],
          index=["unchanged", "add", "remove"].index(decision["action"]),
          key=f"action_{media_id}",
          horizontal=True,
        )

        reason = decision["reason"]
        if action == "remove":
          reason = st.text_area(
            "Removal reason",
            value=reason,
            key=f"reason_{media_id}",
            placeholder="Explain why this source should be removed…",
            height=60,
          )
        else:
          # Clear any stale reason when not removing
          reason = ""

        decisions[int(media_id)] = {
          "media_id": int(media_id),
          "action": action,
          "reason": reason,
        }

    # Persist updated decisions in session state
    st.session_state["decisions"] = decisions

    # Summary & export
    st.markdown("---")
    st.subheader("Review summary")

    all_decisions: List[ReviewDecision] = list(decisions.values())
    total = len(all_decisions)
    to_add = sum(1 for d in all_decisions if d["action"] == "add")
    to_remove = sum(1 for d in all_decisions if d["action"] == "remove")
    unchanged = sum(1 for d in all_decisions if d["action"] == "unchanged")

    st.write(
      f"Total sources: **{total}** · To add: **{to_add}** · "
      f"To remove: **{to_remove}** · Unchanged: **{unchanged}**"
    )

    collection_id = st.session_state.get("loaded_collection_id")

    def decisions_to_csv(decisions_subset: List[ReviewDecision]) -> str:
      buffer = io.StringIO()
      writer = csv.writer(buffer)
      # First column header `id` matches Media Cloud's CSV import.
      writer.writerow(["id", "collection_id", "action", "reason"])
      for d in decisions_subset:
        writer.writerow(
          [
            d["media_id"],
            collection_id,
            d["action"],
            d["reason"],
          ]
        )
      return buffer.getvalue()

    keep_decisions = [d for d in all_decisions if d["action"] == "unchanged"]
    add_decisions = [d for d in all_decisions if d["action"] == "add"]
    remove_decisions = [d for d in all_decisions if d["action"] == "remove"]

    keep_csv = decisions_to_csv(keep_decisions)
    add_csv = decisions_to_csv(add_decisions)
    remove_csv = decisions_to_csv(remove_decisions)

    st.markdown("#### Export CSVs for Media Cloud")

    col_keep, col_add, col_remove = st.columns(3)
    with col_keep:
      st.download_button(
        "Download KEEP CSV",
        data=keep_csv,
        file_name=f"collection_{collection_id}_keep.csv",
        mime="text/csv",
      )
    with col_add:
      st.download_button(
        "Download ADD CSV",
        data=add_csv,
        file_name=f"collection_{collection_id}_add.csv",
        mime="text/csv",
      )
    with col_remove:
      st.download_button(
        "Download REMOVE CSV",
        data=remove_csv,
        file_name=f"collection_{collection_id}_remove.csv",
        mime="text/csv",
      )


if __name__ == "__main__":
  main()

