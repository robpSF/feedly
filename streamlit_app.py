import streamlit as st
import requests
import json

# Constants from Streamlit secrets
CLIENT_ID = st.secrets["feedly"]["client_id"]
CLIENT_SECRET = st.secrets["feedly"]["client_secret"]
REDIRECT_URI = 'http://localhost'
TOKEN_URL = 'https://cloud.feedly.com/v3/auth/token'
API_URL = 'https://cloud.feedly.com/v3'
ACCESS_TOKEN = st.secrets["feedly"]["access_token"]

# Function to get access token (if not already provided in secrets)
def get_access_token():
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    auth_url = f'https://cloud.feedly.com/v3/auth/auth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=https://cloud.feedly.com/subscriptions'
    st.write(f'Go to the following URL and authorize the application: [Authorize Feedly]({auth_url})')
    auth_code = st.text_input('Enter the authorization code:')

    if auth_code:
        response = requests.post(TOKEN_URL, data={
            'code': auth_code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code'
        })

        response_data = response.json()
        access_token = response_data.get('access_token')
        st.session_state['access_token'] = access_token
        st.write(f'Access Token: {access_token}')
        return access_token
    return None

def get_boards(access_token):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get(f'{API_URL}/collections', headers=headers)
    if response.status_code == 200:
        boards = response.json()
        return boards
    else:
        st.error(f"Error fetching boards: {response.status_code} - {response.text}")
        return []

def get_articles(access_token, board_id):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get(f'{API_URL}/streams/contents', headers=headers, params={'streamId': board_id})
    if response.status_code == 200:
        articles = response.json().get('items', [])
        return articles
    else:
        st.error(f"Error fetching articles: {response.status_code} - {response.text}")
        return []

# Streamlit UI
st.title("Feedly Board and Articles Viewer")

# Authenticate and get access token
if 'access_token' not in st.session_state:
    access_token = get_access_token()
else:
    access_token = st.session_state['access_token']

if access_token:
    st.write("Fetching boards...")
    boards = get_boards(access_token)

    if boards:
        st.write("Boards fetched successfully.")
        st.write("Debug info: ", boards)  # Add this line to debug the structure of the boards

        board_titles = [board.get('title', 'No Title') for board in boards]
        selected_board_title = st.selectbox("Select a board:", board_titles)

        selected_board = next((board for board in boards if board.get('title') == selected_board_title), None)
        
        if selected_board:
            st.write(f"Fetching articles from board: {selected_board.get('title', 'No Title')}")
            articles = get_articles(access_token, selected_board.get('id'))

            st.write("Articles:")
            for article in articles:
                st.write(f"- [{article.get('title', 'No Title')}]({article.get('alternate', [{}])[0].get('href', '')})")
        else:
            st.error("Selected board not found.")
    else:
        st.error("No boards available.")
else:
    st.error("Access token not available.")
