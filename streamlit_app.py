import requests
import json
import pandas as pd
import streamlit as st
from docx import Document
from io import BytesIO

# Secrets are accessed using st.secrets
feedaccess = st.secrets["feedly"]["access_token"]

def get_boards():
    url = "https://cloud.feedly.com/v3/boards?withEnterprise=True"
    headers = {'Authorization': 'OAuth ' + feedaccess}
    response = requests.get(url, headers=headers)
    data = json.loads(response.content)
    st.write("Board response", response)
    df = pd.DataFrame.from_dict(data)
    st.write(df)
    boards = df["label"].tolist()
    return boards, df

def get_feedly_articles(board_id):
    url = f"https://cloud.feedly.com/v3/boards/{board_id}/contents"
    headers = {"Authorization": "OAuth " + feedaccess}
    response = requests.get(url, headers=headers)
    data = json.loads(response.content)
    return data

def create_word_document(articles):
    document = Document()
    for article in articles['items']:
        document.add_heading(article['title'], level=1)
        document.add_paragraph(article['content']['content'])
    return document

def main():
    st.title("Feedly Board Articles")
    
    boards, df = get_boards()
    selected_board = st.selectbox("Select a Board", boards)
    
    if selected_board:
        board_id = df[df["label"] == selected_board]["id"].values[0]
        articles = get_feedly_articles(board_id)
        
        if st.button("Download Articles as Word Document"):
            document = create_word_document(articles)
            buffer = BytesIO()
            document.save(buffer)
            buffer.seek(0)
            st.download_button(
                label="Download Word Document",
                data=buffer,
                file_name="feedly_articles.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

if __name__ == "__main__":
    main()
