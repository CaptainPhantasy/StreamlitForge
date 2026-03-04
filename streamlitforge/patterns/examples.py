"""Example patterns for StreamlitForge."""

# Chat UI Pattern
CHAT_PATTERN = {
    'name': 'chat-ui',
    'category': 'ui',
    'description': 'Standard chat interface with message history',
    'template': '''import streamlit as st

st.title("Chat Interface")

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Type a message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = generate_response(prompt)
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
''',
    'usage': 'Use for LLM-powered chat applications'
}

# Dashboard Layout Pattern
DASHBOARD_PATTERN = {
    'name': 'dashboard-layout',
    'category': 'layout',
    'description': 'Layout pattern for data dashboards',
    'template': '''import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

with st.sidebar:
    filter_options = st.selectbox("Filter", ["All", "Option1", "Option2"])

data = load_data()

st.title("Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total", len(data))

with col2:
    st.metric("Average", data["value"].mean())

fig = px.line(data, x="date", y="value")
st.plotly_chart(fig, use_container_width=True)
''',
    'usage': 'Use for analytics dashboards'
}
