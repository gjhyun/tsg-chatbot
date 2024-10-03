import streamlit as st
import urllib.request
import json
import os
import ssl
from openai import OpenAI

def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

# Show title and description.
st.title("💬 Chatbot")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-3.5 model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input`.
# Alternatively, you can store the API key in `./.streamlit/secrets.toml` and access it
# via `st.secrets`, see https://docs.streamlit.io/develop/concepts/connections/secrets-management
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:

    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Create a session state variable to store the chat messages. This ensures that the
    # messages persist across reruns.
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display the existing chat messages via `st.chat_message`.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Create a chat input field to allow the user to enter a message. This will display
    # automatically at the bottom of the page.
    if prompt := st.chat_input("How can I help?"):

        # Store and display the current prompt.
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Query API
        # Request data goes here
        # The example below assumes JSON formatting which may be updated
        # depending on the format your endpoint expects.
        # More information can be found here:
        # https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script
        data = {"chat_history": st.session_state.messages, 'question': prompt}

        body = json.dumps(data).encode('utf-8')

        url = 'https://tsg-chatbot-amjby.eastus.inference.ml.azure.com/score'
        # Replace this with the primary/secondary key, AMLToken, or Microsoft Entra ID token for the endpoint

        headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ openai_api_key)};
        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)
            
            response_data = json.loads(response.read().decode('utf-8'))
            print(response_data)
            if 'answer' in response_data:
                with st.chat_message("assistant"):
                    st.markdown(response_data['answer'])
                
                st.session_state.messages.append(
                    {"inputs": {"question": prompt},
                     "outputs": {"answer": response_data['answer']}}
                )
            else:
                st.error("The response data does not contain a 'output' key.")

        except urllib.error.HTTPError as error:
            print("The request failed with status code: " + str(error.code))

            # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
            print(error.info())
            print(error.read().decode("utf8", 'ignore'))
