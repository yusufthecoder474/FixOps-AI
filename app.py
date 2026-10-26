from time import perf_counter
import streamlit as st
from fixops.config import Settings
from fixops.knowledge import load_runbooks
from fixops.retrieval import Retriever
from fixops.answer import answer
from fixops.history import History

st.set_page_config(page_title='FixOps AI', page_icon='🛠️', layout='wide')
st.title('FixOps AI')
st.caption('Intelligent IT incident troubleshooting · read-only investigation')
settings = Settings()

@st.cache_resource(show_spinner=False)
def get_retriever(backend, model, threshold):
    return Retriever(load_runbooks(), backend, model, threshold)

with st.sidebar:
    st.header('Investigation settings')
    backend = st.selectbox('Retrieval engine', ['semantic', 'tfidf'])
    st.caption('Semantic: all-MiniLM-L6-v2. TF-IDF is an explicit offline baseline.')
    use_llm = st.checkbox('Use optional LLM', value=bool(settings.api_key), disabled=not bool(settings.api_key))
    st.caption('The API receives only recognized incident categories and retrieved runbooks. Raw query text is never sent to it.')
    save_history = st.checkbox('Save private category-only history', value=True)
    st.caption('Keeps 100 entries locally. Raw questions, logs, secrets and credentials are not stored.')
    st.info('No infrastructure access, shell execution or automated remediation.')

st.write('Describe the symptoms, component and error code. Do not paste credentials or private logs.')
with st.form('incident', clear_on_submit=True):
    query = st.text_area('Incident description', placeholder='Checkout returns HTTP 500 after a deployment.', max_chars=3000)
    submitted = st.form_submit_button('Find investigation steps', type='primary')

if submitted:
    if not query.strip():
        st.warning('Enter an incident description.')
    else:
        start = perf_counter()
        try:
            with st.spinner('Loading retrieval engine and searching runbooks…'):
                threshold = settings.semantic_threshold if backend == 'semantic' else settings.tfidf_threshold
                retriever = get_retriever(backend, settings.model, threshold)
                result = retriever.search(query)
                steps, notice = answer(result, query, settings, use_llm)
            total = (perf_counter() - start)*1000
            st.session_state['last'] = (result, steps, notice, total)
            if save_history:
                try:
                    History(settings.history_path).add(query, result)
                except Exception:
                    st.warning('Could not save local history; retrieval still succeeded.')
        except Exception:
            st.session_state.pop('last', None)
            st.error('Retrieval engine could not start. Semantic mode needs the model downloaded once. Select TF-IDF to work offline; see README for setup.')

if 'last' in st.session_state:
    result, steps, notice, total = st.session_state['last']
    (st.success if result.supported else st.warning)(result.reason)
    a, b, c = st.columns(3)
    a.metric('Retrieval', f'{result.latency_ms:.1f} ms')
    b.metric('Total request', f'{total:.1f} ms')
    c.metric('Engine', result.backend)
    st.caption('Total includes initialization and optional LLM time. Cosine similarities are ranking scores, not calibrated probabilities or evidence of a root cause.')
    if steps:
        st.subheader('Suggested investigation')
        for i, step in enumerate(steps, 1):
            st.write(f'{i}. {step}')
    st.caption(notice)
    st.subheader('Top 3 retrieved sources' if result.supported else 'Nearest matches — insufficient evidence')
    for hit in result.hits:
        d = hit.doc
        with st.expander(f"{d['id']} · {d['title']} · cosine {hit.score:.3f}", expanded=result.supported):
            st.caption(d['provenance'])
            st.write(d['symptoms'])
            for i, step in enumerate(d['steps'], 1):
                st.write(f"{i}. {step} [{d['id']}]")
            st.write('Evidence to collect: ' + d['evidence'])
            st.write('Escalation: ' + d['escalation'])
            st.caption('Background references (authored procedure above is not a vendor quotation):')
            for ref in d['references']:
                st.markdown(f"[{ref['title']}]({ref['url']})")

with st.expander('Local incident-category history'):
    try:
        st.dataframe(History(settings.history_path).recent(), use_container_width=True)
    except Exception:
        st.caption('History unavailable.')
