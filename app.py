import streamlit as st
from snowflake.snowpark import Session
from snowflake.core import Root
import pandas as pd
import json

pd.set_option("max_colwidth",None)

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
def config_options():
    if not session:
        return

    # Set the generator model directly
    generator_model = 'mistral-large2'
    # You can use 'generator_model' in the rest of your code where needed

    try:
        st.write("Configuration options set.")
    except Exception as e:
        st.error(f"Configuration failed: {str(e)}")

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
           You are an expert chat assistance that extracs information from the CONTEXT provided
           between <context> and </context> tags.
           When ansering the question contained between <question> and </question> tags
           be concise and do not hallucinate. 
           If you don´t have the information just say so.
           Only anwer the question if you can extract it from the CONTEXT provideed.
           
           Do not mention the CONTEXT used in your answer.
    
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
        
    st.title(f":speech_balloon: Chat Document Assistant with Snowflake Cortex")
    
    try:
        st.write("This is the list of documents you already have and that will be used to answer your questions:")
        docs_available = session.sql("ls @docs").collect()
        list_docs = []
        for doc in docs_available:
            list_docs.append(doc["name"])
        st.dataframe(list_docs)
    except Exception as e:
        st.error(f"Failed to fetch document list: {str(e)}")
        st.write("No documents available or error accessing document store")

    config_options()

    st.session_state.rag = st.sidebar.checkbox('Use your own documents as context?')

    question = st.text_input("Enter question", placeholder="Is there any special lubricant to be used with the premium bike?", label_visibility="collapsed")

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
                
if __name__ == "__main__":
    main()