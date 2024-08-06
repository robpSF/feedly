import requests
import json
import pandas as pd
import streamlit as st
from docx import Document
from io import BytesIO

# Secrets are accessed using st.secrets
feedaccess = st.secrets["feedly"]["access_token"]

def get_boards():
    url = "https://cloud.feedly.com/v3/boards"
    headers = {'Authorization': 'OAuth ' + feedaccess}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"Error fetching boards: {response.text}")
        return [], pd.DataFrame()
    
    data = response.json()
    st.write("Board response", response)
    st.json(data)  # Print the raw response for debugging
    
    # Ensure the response contains the expected keys
    if "results" in data:
        df = pd.DataFrame(data["results"])
        st.write(df)  # Print the DataFrame for debugging
        boards = df["label"].tolist()
        return boards, df
    else:
        st.error("No boards found in the response.")
        return [], pd.DataFrame()

def get_feedly_articles(board_id):
    url = f"https://cloud.feedly.com/v3/streams/contents?streamId={board_id}"
    headers = {"Authorization": "OAuth " + feedaccess}
    response = requests.get(url, headers=headers)
    st.write("Articles response status code:", response.status_code)
    if response.status_code != 200:
        st.error("Error fetching articles: " + response.text)
        return None
    data = response.json()
    st.json(data)  # This will help us inspect the structure of the articles object
    return data

def create_word_document(articles):
    document = Document()
    for article in articles['items']:
        document.add_heading(article.get('title', 'No Title'), level=1)
        content = article.get('content', {}).get('content', 'No Content')
        document.add_paragraph(content)
    return document

def save_articles_to_files(df, document):
    # Save document to BytesIO
    doc_buffer = BytesIO()
    document.save(doc_buffer)
    doc_buffer.seek(0)

    # Save dataframe to BytesIO for Excel
    excel_buffer = BytesIO()
    df.to_excel(excel_buffer, encoding="utf-8", index=False)
    excel_buffer.seek(0)

    # Save dataframe to CSV (text) buffer
    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, encoding="utf-8", index=False)
    csv_buffer.seek(0)

    return doc_buffer, excel_buffer, csv_buffer

def main():
    st.title("Feedly Board Articles")
    
    boards, df = get_boards()
    selected_board = st.selectbox("Select a Board", boards)
    
    if selected_board:
        board_id = df[df["label"] == selected_board]["id"].values[0]
        st.write("Selected Board ID:", board_id)  # Debugging line to check the board ID
        articles = get_feedly_articles(board_id)
        
        if articles and 'items' in articles:
            df_articles = pd.json_normalize(articles['items'])
        
            if st.sidebar.button(label="Save file"):
                document = create_word_document(articles)
                doc_buffer, excel_buffer, csv_buffer = save_articles_to_files(df_articles, document)
                
                st.sidebar.download_button(
                    label="Download Word Document",
                    data=doc_buffer,
                    file_name="feedly_articles.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                
                st.sidebar.download_button(
                    label="Download Excel File",
                    data=excel_buffer,
                    file_name="news_scrape.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                st.sidebar.download_button(
                    label="Download CSV File",
                    data=csv_buffer,
                    file_name="news_scrape.csv",
                    mime="text/csv"
                )
                
                st.sidebar.text("Files saved: feedly_articles.docx, news_scrape.xlsx, news_scrape.csv")
                st.header("Done! Files saved")
        else:
            st.error("No articles found for the selected board or error fetching articles.")

if __name__ == "__main__":
    main()

