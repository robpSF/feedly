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
    boards = response.json()
    return boards

def get_articles(access_token, board_id):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get(f'{API_URL}/streams/contents', headers=headers, params={'streamId': board_id})
    articles = response.json().get('items', [])
    return articles

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

    board_titles = [board['title'] for board in boards]
    selected_board_title = st.selectbox("Select a board:", board_titles)

    selected_board = next(board for board in boards if board['title'] == selected_board_title)
    st.write(f"Fetching articles from board: {selected_board['title']}")
    
    articles = get_articles(access_token, selected_board['id'])

    st.write("Articles:")
    for article in articles:
        st.write(f"- [{article['title']}]({article.get('alternate', [{}])[0].get('href', '')})")
