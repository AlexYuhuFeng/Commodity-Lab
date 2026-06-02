from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.deepseek import ask_deepseek
from core.db import default_db_path, get_conn, init_db, list_instruments


def render_assistant_sidebar(workspace_root: Path) -> None:
    if "assistant_open" not in st.session_state:
        st.session_state.assistant_open = True
    if "assistant_history" not in st.session_state:
        st.session_state.assistant_history = []
    if "assistant_mode" not in st.session_state:
        st.session_state.assistant_mode = "Guidance & mentoring"
    if "assistant_prompt" not in st.session_state:
        st.session_state.assistant_prompt = ""
    if "assistant_followup" not in st.session_state:
        st.session_state.assistant_followup = ""

    con = get_conn(default_db_path(workspace_root))
    init_db(con)
    instruments = list_instruments(con, only_watched=True)
    portfolio_summary = "\n".join(
        f"{row['ticker']}: source={row['source']}, exchange={row['exchange']}" for _, row in instruments.iterrows()
    )

    st.markdown("### ✨ AI Assistant")
    st.caption(
        "A persistent hedge learning coach available while you browse market data and simulate trades."
    )

    with st.expander("Open assistant", expanded=st.session_state.assistant_open):
        st.session_state.assistant_open = True
        st.radio(
            "Advisor mode",
            [
                "Performance review",
                "Guidance & mentoring",
                "Hints and next steps",
            ],
            key="assistant_mode",
        )
        st.text_area(
            "Question",
            key="assistant_prompt",
            height=100,
            placeholder=(
                "What do you want help with? E.g. risk balance, exposure, timing, or strategy guidance."
            ),
        )
        st.text_area(
            "Clarify or ask for a hint",
            key="assistant_followup",
            height=80,
            placeholder=(
                "Ask a follow-up or request a concrete next step."
            ),
        )

        if st.button("Send to AI Advisor", key="assistant_send"):
            query = st.session_state.assistant_followup.strip() or st.session_state.assistant_prompt.strip()
            if not query:
                st.warning(
                    "Enter a question or a follow-up request so the assistant can help you."
                )
            else:
                try:
                    answer = ask_deepseek(
                        query,
                        context=portfolio_summary,
                        mode=st.session_state.assistant_mode,
                        history=st.session_state.assistant_history,
                    )
                    st.session_state.assistant_history.append(
                        {
                            "mode": st.session_state.assistant_mode,
                            "question": query,
                            "answer": answer,
                        }
                    )
                    st.session_state.assistant_prompt = ""
                    st.session_state.assistant_followup = ""
                except Exception as exc:
                    st.error(str(exc))

    if st.session_state.assistant_history:
        st.markdown("---")
        st.markdown("#### Conversation history")
        for entry in reversed(st.session_state.assistant_history[-5:]):
            st.markdown(f"**{entry['mode']}**: {entry['question']}")
            st.info(entry["answer"])

    if st.button("Clear assistant history", key="assistant_clear"):
        st.session_state.assistant_history = []
        st.success("Assistant history cleared.")

    try:
        con.close()
    except Exception:
        pass
