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

def get_request_limits(headers):
    # Extracting rate limit information from the response headers
    limit = headers.get('X-RateLimit-Limit')
    remaining = headers.get('X-RateLimit-Remaining')
    reset = headers.get('X-RateLimit-Reset')

    return limit, remaining, reset

def get_boards(access_token):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get(f'{API_URL}/boards?withEnterprise=True', headers=headers)
    limit, remaining, reset = get_request_limits(response.headers)
    if response.status_code == 200:
        boards = response.json()
        return boards, limit, remaining, reset
    elif response.status_code == 429:
        st.error("API rate limit reached. Please try again later.")
        return [], limit, remaining, reset
    else:
        st.error(f"Error fetching boards: {response.status_code} - {response.text}")
        return [], limit, remaining, reset

def get_articles(access_token, board_id):
    headers = {
        'Authorization': f'OAuth {access_token}'
    }
    response = requests.get(f'{API_URL}/streams/contents', headers=headers, params={'streamId': board_id})
    limit, remaining, reset = get_request_limits(response.headers)
    if response.status_code == 200:
        articles = response.json().get('items', [])
        return articles, limit, remaining, reset
    elif response.status_code == 429:
        st.error("API rate limit reached. Please try again later.")
        return [], limit, remaining, reset
    else:
        st.error(f"Error fetching articles: {response.status_code} - {response.text}")
        return [], limit, remaining, reset

# Streamlit UI
st.title("Feedly Board and Articles Viewer")

# Authenticate and get access token
if 'access_token' not in st.session_state:
    access_token = get_access_token()
else:
    access_token = st.session_state['access_token']

if access_token:
    st.write("Fetching boards...")
    boards, limit, remaining, reset = get_boards(access_token)

    # Display API request count in the sidebar
    with st.sidebar:
        st.header("API Request Limits")
        st.write(f"Limit: {limit}")
        st.write(f"Remaining: {remaining}")
        st.write(f"Reset: {reset}")

    if boards:
        st.write("Boards fetched successfully.")
        st.write("Debug info: ", boards)  # Add this line to debug the structure of the boards

        board_labels = [board.get('label', 'No Label') for board in boards]
        selected_board_label = st.selectbox("Select a board:", board_labels)

        selected_board = next((board for board in boards if board.get('label') == selected_board_label), None)
        
        if selected_board:
            st.write(f"Fetching articles from board: {selected_board.get('label', 'No Label')}")
            articles, limit, remaining, reset = get_articles(access_token, selected_board.get('id'))

            # Update API request count in the sidebar
            with st.sidebar:
                st.write(f"Limit: {limit}")
                st.write(f"Remaining: {remaining}")
                st.write(f"Reset: {reset}")

            st.write("Articles:")
            for article in articles:
                st.write(f"- [{article.get('title', 'No Title')}]({article.get('alternate', [{}])[0].get('href', '')})")
        else:
            st.error("Selected board not found.")
    else:
        st.error("No boards available.")
else:
    st.error("Access token not available.")
