import streamlit as st
import time,PyPDF2,pinecone
from langchain_huggingface import HuggingFaceEndpointEmbeddings
# from langchain_experimental.text_splitter import SemanticChunker
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Correct Import
from langchain_pinecone import PineconeVectorStore
from uuid import uuid4
from langchain_core.documents import Document
import re
import unicodedata

pinecone_api_key = "pcsk_ffUJz_7hkW8pZMvpf99EXNU1y65SehYwa2nPKSbrtC8SCZX3mqUGPeYahH6gXpae1SNY6"  # Shivam's Api Key For Vector Store
pinecone_environment = "us-east-1"  
pinecone_index_name = "example-index"
pc = pinecone.Pinecone(api_key=pinecone_api_key)
model_id = "sentence-transformers/all-MiniLM-L6-v2"
# hf_token = "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" shivam
hf_token = "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"

def preprocess_text(text):
    # 1. Unicode Normalization:
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')

    # 2. Remove URLs:
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)

    # 3. Remove HTML tags (if present):
    text = re.sub('<.*?>+', '', text)

    # 4. Remove special characters and non-alphanumeric characters (keep hyphens and apostrophes):
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text) #Keep hyphens and apostrophes
    #text = re.sub(r'[^\w\s-]', '', text)

    # 5. Remove extra whitespace:
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def upload_and_analyze():
    uploaded_file = st.file_uploader("Upload the PDF file only",type=['pdf'])
    r_text = ""
    if uploaded_file is not None:
        try:
            reader = PyPDF2.PdfReader(uploaded_file)
            for page_num in range(len(reader.pages)):
                r_text += reader.pages[page_num].extract_text()

            st.session_state['pdf_uploaded'] = True
        except:
            st.error("This file is unable to read!!!")
            r_text = ""
    return r_text

def store_in_vector(docs,embeddings):
    if pinecone_index_name not in pc.list_indexes().names():
        pc.create_index(
            name=pinecone_index_name,
            dimension=384,
            metric='cosine',
            spec=pinecone.ServerlessSpec(cloud='aws', region=pinecone_environment)
        )
        while not pc.describe_index(pinecone_index_name).status["ready"]:
            time.sleep(1)
    
    index = pc.Index(pinecone_index_name)
    vector_store = PineconeVectorStore(index=index, embedding=embeddings)
    documents = [Document(page_content = doc.page_content, metadata={"source": "general pdf data"},) for doc in docs]
    uuids = [str(uuid4()) for _ in range(len(documents))]

    vector_store.add_documents(documents=documents, ids=uuids)
    st.session_state["uploaded_and_analyzed"] = True
    st.rerun()

def generate_embedding(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_text(text)

    filtered_chunks = [chunk for chunk in chunks if chunk.strip()]

    docs = []
    embeddings_list = []

    for chunk in filtered_chunks:
        preprocessed_chunk = preprocess_text(chunk)

        if not preprocessed_chunk:
            continue  # Skip if empty after preprocessing

        try:
            embedding = HuggingFaceEndpointEmbeddings(model=model_id, task="feature-extraction", huggingfacehub_api_token=hf_token).embed_query(preprocessed_chunk)

            if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding) and len(embedding) > 0:
                docs.append(Document(page_content=chunk, metadata={"source": "general pdf data"}))
                embeddings_list.append(embedding)
            else:
                st.warning(f"Invalid embedding for chunk (truncated): {preprocessed_chunk[:50]}...")

        except Exception as e:
            st.error(f"Error generating embedding for chunk (truncated): {preprocessed_chunk[:50]}... Error: {e}")
            continue

    if docs:
       embeddings = HuggingFaceEndpointEmbeddings(model=model_id, task="feature-extraction", huggingfacehub_api_token=hf_token)
       store_in_vector(docs, embeddings)
    else:
        st.warning("No valid chunks found after filtering and preprocessing. Check your PDF content.")


def generate_embedding2(text):
    # Use RecursiveCharacterTextSplitter - More robust
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50) # Adjust chunk size as needed
    chunks = text_splitter.split_text(text)

    # Filter out empty or whitespace chunks
    filtered_chunks = [chunk for chunk in chunks if chunk.strip()] #Remove empty string from chunks

    docs = []
    embeddings_list = []  # Store embeddings for later use

    for chunk in filtered_chunks:
        try:
            embedding = HuggingFaceEndpointEmbeddings(model=model_id, task="feature-extraction", huggingfacehub_api_token=hf_token).embed_query(chunk)
            if isinstance(embedding, list) and all(isinstance(x, float) for x in embedding) and len(embedding) > 0: #Check if embedding is valid
                docs.append(Document(page_content=chunk, metadata={"source": "general pdf data"}))
                embeddings_list.append(embedding)
            else:
                st.warning(f"Invalid embedding for chunk: {chunk[:50]}...") #Log invalid embedding

        except Exception as e:
            st.error(f"Error generating embedding for chunk: {chunk[:50]}... Error: {e}")
            continue # Skip this chunk and continue with the next


    if docs:  # Only call store_in_vector if there are valid documents and embeddings
        store_in_vector(docs, HuggingFaceEndpointEmbeddings(model=model_id, task="feature-extraction", huggingfacehub_api_token=hf_token))
    else:
        st.warning("No valid chunks found after filtering. Check your PDF content.")

  



    
    # text_splitter = SemanticChunker(HuggingFaceEndpointEmbeddings(model=model_id,task="feature-extraction",huggingfacehub_api_token=hf_token),breakpoint_threshold_type="gradient")
    # docs = text_splitter.create_documents([text])
    # embeddings = HuggingFaceEndpointEmbeddings(model=model_id,task="feature-extraction",huggingfacehub_api_token=hf_token)
    # store_in_vector(docs,embeddings)

def upload_pdf():
    text = upload_and_analyze()
    if text:
        with st.spinner("Your Pdf is being analyzed, Please Wait..."):
            generate_embedding(text)

def material_uploader_interface():
    if st.session_state["uploaded_and_analyzed"]:
        st.success("Your pdf has been successfully uploaded, Now you can go to Test with your own material option to get Quiz.")
        if st.button("Want to upload another Pdf"):
            st.session_state['uploaded_and_analyzed'] = False
            upload_pdf()
    else:
        upload_pdf()
