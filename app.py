import streamlit as st
import asyncio
from langgraph_sdk import get_client


URL=st.secrets["Service"]

# -------------------------------
# Async helper to interact with graph
# -------------------------------
async def run_research(topic: str, max_analysts: int, feedback: str):
    client = get_client(url=URL)  # change if deployed

    # Create a new thread (persist across reruns)
    if "thread_id" not in st.session_state:
        thread = await client.threads.create()
        st.session_state["thread_id"] = thread["thread_id"]

    # Input payload for graph
    input_data = {
        "topic": topic,
        "max_analysts": max_analysts,
        "human_analyst_feedback": feedback,
    }

    collected_state = {}
    # Stream events
    async for event in client.runs.stream(
        thread_id=st.session_state["thread_id"],
        assistant_id="research_assistant",   # must match your graph ID
        input=input_data,
        stream_mode="values",
    ):
        if event.data:
            collected_state.update(event.data)

    return collected_state


# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="Research Assistant", layout="centered")
st.title("🧑‍🔬 Research Assistant")

# Form for research inputs (single step)
with st.form("research_form"):
    topic = st.text_input("Enter Research Topic", "Future of AI in Healthcare")
    max_analysts = st.number_input("Number of Analysts", min_value=1, max_value=10, value=3)
    feedback = st.text_area("Initial Human Input / Feedback", "Please ensure analysts cover ethics and regulations.")
    submitted = st.form_submit_button("Run Research")

# Run graph once submitted
if submitted:
    with st.spinner("Running research graph..."):
        state = asyncio.run(run_research(topic, max_analysts, feedback))

        # Display analysts
        if "analysts" in state and state["analysts"]:
            st.subheader("👩‍🔬 Analysts")
            for a in state["analysts"]:
                st.markdown(f"**Name:** {a['name']}")
                st.markdown(f"**Affiliation:** {a['affiliation']}")
                st.markdown(f"**Role:** {a['role']}")
                st.write(a['description'])
                st.markdown("---")

        # Display final report
        if "final_report" in state and state["final_report"]:
            st.subheader("📄 Final Report")
            st.markdown(state["final_report"])
