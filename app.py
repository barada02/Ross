import streamlit as st
from snowflake.snowpark import Session
from snowflake.core import Root
import pandas as pd
import json
from streamlit_lottie import st_lottie

pd.set_option("max_colwidth",None)

st.set_page_config(
    page_title="PhytoSense: an mistral powered RAG Application",
    page_icon="https://banner2.cleanpng.com/20180429/dzw/avd1hzie1.webp"
)


### Default Values
NUM_CHUNKS = 3 # Num-chunks provided as context. Play with this to check how it affects your accuracy

# service parameters
CORTEX_SEARCH_DATABASE = st.secrets["connections"]["snowflake"]["database"]
CORTEX_SEARCH_SCHEMA = st.secrets["connections"]["snowflake"]["schema"]
CORTEX_SEARCH_SERVICE = "CC_SEARCH_SERVICE_CS"

# columns to query in the service
COLUMNS = [
    "chunk",
    "relative_path"
]

@st.cache_resource
def init_snowflake_connection():
    """Initialize Snowflake connection with error handling"""
    try:
        # Get connection parameters from secrets
        snowflake_config = st.secrets["connections"]["snowflake"]
        
        # Create Snowpark session
        session = Session.builder.configs({
            "account": snowflake_config["account"],
            "user": snowflake_config["user"],
            "password": snowflake_config["password"],
            "role": snowflake_config["role"],
            "warehouse": snowflake_config["warehouse"],
            "database": snowflake_config["database"],
            "schema": snowflake_config["schema"]
        }).create()
        
        root = Root(session)
        svc = root.databases[CORTEX_SEARCH_DATABASE].schemas[CORTEX_SEARCH_SCHEMA].cortex_search_services[CORTEX_SEARCH_SERVICE]
        return session, root, svc
    except Exception as e:
        st.error(f"Failed to connect to Snowflake: {str(e)}")
        st.error("Please check your credentials in .streamlit/secrets.toml")
        return None, None, None

# Initialize connection
session, root, svc = init_snowflake_connection()

### Functions


def get_similar_chunks_search_service(query):
    if not svc:
        st.error("Snowflake connection not available")
        return []

    try:
        response = svc.search(query, COLUMNS, limit=NUM_CHUNKS)
        st.sidebar.json(response.json())
        return response.json()
    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return []

def create_prompt(myquestion):
    if st.session_state.rag == 1:
        prompt_context = get_similar_chunks_search_service(myquestion)
        if not prompt_context:
            return "", set()

        prompt = f"""
           You are a highly specialized chatbot designed to extract and process information solely from provided text. 
           Your responses must be concise, accurate, 
           and based exclusively on the content between <context> and </context> tags. 
           Do not generate information that is not explicitly present in the provided text (no hallucinations).

           Your task is to Answer questions enclosed within <question> and </question> tags using only the information within the corresponding context. 
           If the answer cannot be derived from the provided context, respond with "The answer is not in the provided document."
           Do not mention or reference "context," "document," or similar terms in your answers. Simply provide the direct answer.
    
           <context>          
           {prompt_context}
           </context>
           <question>  
           {myquestion}
           </question>
           Answer: 
           """

        json_data = json.loads(prompt_context)
        relative_paths = set(item['relative_path'] for item in json_data['results'])
        
    else:     
        prompt = f"""[0]
         'Question:  
           {myquestion} 
           Answer: '
           """
        relative_paths = "None"
            
    return prompt, relative_paths

def complete(myquestion):
    if not session:
        st.error("Snowflake connection not available")
        return None, "None"

    try:
        prompt, relative_paths = create_prompt(myquestion)
        if not prompt:
            return None, "None"

        cmd = """
                select snowflake.cortex.complete(?, ?) as response
              """
        
        df_response = session.sql(cmd, params=['mistral-large2', prompt]).collect()
        return df_response, relative_paths
    except Exception as e:
        st.error(f"Completion failed: {str(e)}")
        return None, "None"

def main():
    if not session:
        st.error("Failed to connect to Snowflake. Please check your credentials and try again.")
        return
        
    # Display the image as a smaller logo at the top of the app
    st.image('thumbnail.png', width=200)
    st.title(f" PhytoSense: an snowflake and mistral powered RAG Application")
    st.sidebar.title("Instructions")
    st.sidebar.title("Available Documents")
    try:
        docs_available = session.sql("ls @docs").collect()
        list_docs = []
        for doc in docs_available:
            list_docs.append(doc["name"])
        st.sidebar.dataframe(list_docs)
    except Exception as e:
        st.sidebar.error(f"Failed to fetch document list: {str(e)}")
        st.sidebar.write("No documents available or error accessing document store")

    st.session_state.rag = st.sidebar.checkbox('Use your own documents as context?')

    response, relative_paths = None, "None"

    # Sample questions dropdown
    sample_questions = [
        "What are the advantages of using edible vaccines?",
        "What are some examples of potential synergism between plant extracts/essential oils and conventional antimicrobial drugs?",
        "Why is caution advised when using Goldenseal or other herbs containing berberine for extended periods?",
        "What analytical techniques are useful for the quality control of medicinal plants?",
        "What are the challenges in ensuring the quality of herbal medicines?",
        "What are the main classes of phytochemicals found in plants with potential antimicrobial activity?",
        "What is the role of hydrophobicity in the antimicrobial action of essential oils?",
        "What is the mechanism of action of cinnamaldehyde?",
        "How do the chemical structures of carvacrol and thymol differ, and what is the significance of this difference?"
    ]

    selected_question = st.selectbox("Select a sample question:", options=["Select a question..."] + sample_questions)

    # Use the selected question as the default in the text input if one is selected
    question = st.text_input(
        "Enter question", 
        value=selected_question if selected_question != "Select a question..." else "",
        placeholder="What are some safety concerns associated with the use of Alfalfa?",
        label_visibility="collapsed"
    )

    if question:
        response, relative_paths = complete(question)

    if response:
        res_text = response[0].RESPONSE
        st.markdown(res_text)

        if relative_paths != "None":
            with st.sidebar.expander("Related Documents"):
                try:
                    for path in relative_paths:
                        cmd2 = f"select GET_PRESIGNED_URL(@docs, '{path}', 360) as URL_LINK from directory(@docs)"
                        df_url_link = session.sql(cmd2).to_pandas()
                        url_link = df_url_link._get_value(0,'URL_LINK')
                
                        display_url = f"Doc: [{path}]({url_link})"
                        st.sidebar.markdown(display_url)
                except Exception as e:
                    st.sidebar.error(f"Failed to generate document links: {str(e)}")

    # Load the Lottie animation with UTF-8 encoding
    with open('plantanimation.json', 'r', encoding='utf-8') as f:
        lottie_animation = json.load(f)

    # Display the Lottie animation
    st_lottie(lottie_animation, height=300, key="plant_animation")

    

if __name__ == "__main__":
    main()