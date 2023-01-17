import streamlit as st
from streamlit_chat import message
import os
import openai
import re
from pathlib import Path
from datetime import datetime
import openai
from data import papers
import argparse
from haystack.document_stores import InMemoryDocumentStore
from haystack import Document
from haystack.nodes import PreProcessor, EmbeddingRetriever

@st.cache(allow_output_mutation=True)
class ChatBotModel:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')

        self.engine = "text-davinci-003"
        self.max_tokens = 1000
        self.temperature = 0.1
        self.similarity_threshold = 0.55

        #logging the conversation and prompt
        self.log_path = Path(__file__).resolve().parent / "logs" / str(datetime.now())
        self.log_path.mkdir(exist_ok=True)
        self.paper = papers.transformer
        # paper = papers.retro

        parser = argparse.ArgumentParser()
        parser.add_argument('--max_tokens', type=int, default=2000)
        parser.add_argument('--temperature', type=float, default=0.7)
        args = parser.parse_args()

        abstract = re.findall(r'Abstract(.*?)[\n\d]*Introduction', self.paper, re.DOTALL)[0].strip()
        abstract = " ".join(abstract.split('\n'))

        paper_body = re.findall(r'Introduction(.*?)[\n\d]*References', self.paper, re.DOTALL)[0].strip()
        paper_body = "1  Introduction  "+" ".join(paper_body.split('\n'))


        #create document store
        self.document_store = InMemoryDocumentStore(
            index="document",
            embedding_field="emb",
            embedding_dim=768,
            similarity="dot_product",
        )

        #create preprocessor
        self.preprocessor = PreProcessor(
            clean_empty_lines=True,
            clean_whitespace=True,
            clean_header_footer=False,
            split_by="word",
            split_length=100,
            split_overlap=30,
            split_respect_sentence_boundary=True,
            language="en"
        )

        #write document store
        paper_body_dict = {
            "id": 1,
            "content": paper_body,
            "meta": {
                "name": "paper"
            }
        }
        doc = [Document.from_dict(paper_body_dict)]
        docs = self.preprocessor.process(doc)

        self.document_store.write_documents(docs)

        #create retriever
        self.retriever = EmbeddingRetriever(
            document_store=self.document_store,
            embedding_model="sentence-transformers/multi-qa-mpnet-base-dot-v1",
            model_format="sentence_transformers",
            progress_bar=False,
        )
        self.document_store.update_embeddings(self.retriever)

        self.context = ''
        self.response_start = "\nA : "
        self.past_qa = []

        self.index = 0

        self.initial_prompt = f"""
            Q : You are a chatbot that can answer the questions about the paper. This is the abstract of the paper you should understand.
            {abstract}
            A : I understand the abstract. I'm ready to answer the questions.

            """

    def chat(self, user_input):
        sample_chunks = self.retriever.retrieve(query=user_input, top_k=5)
        with open(self.log_path / "retrieval.txt", 'a') as fh:
            fh.write("Question " + str(self.index) + " : " + user_input + "\n")
            fh.write("Answer : \n")
            for chunk in sample_chunks:
                fh.write("content : " + chunk.content + "\n")
                fh.write("score : " + str(chunk.score) + "\n")
            fh.write("\n\n")

        prompt = self.initial_prompt

        for qa in self.past_qa:
            prompt += "Q : " + qa["question"] + "\n"
            prompt += "A : " + qa["answer"] + "\n"

        prompt += "Q : " + user_input +"\n"
        print("similiarity between question and paper : ", sample_chunks[0].score)

        if sample_chunks[0].score >= self.similarity_threshold:
            prompt += "These informations from the paper below might be helpful.\n"
        
        for chunk in sample_chunks:
            if chunk.score >= self.similarity_threshold:
                prompt += chunk.content + "\n"
        
        prompt += "Answer to the question."
        prompt += self.response_start
        print("Prompt : " + prompt)

        response = openai.Completion.create(
            engine=self.engine,
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        self.past_qa.append({"question": user_input, "answer": response.choices[0].text})
        if len(self.past_qa) >= 10:
            self.past_qa.pop(0)

        # print("A : " + response.choices[0].text)
        self.index += 1
        return response.choices[0].text


model = ChatBotModel()

if __name__ == '__main__':

    st.header('Chat Bot')
    placeholder = st.empty()

    if 'past' not in st.session_state: # 내 입력채팅값 저장할 리스트
        st.session_state['past'] = [] 

    if 'generated' not in st.session_state: # 챗봇채팅값 저장할 리스트
        st.session_state['generated'] = []

    with st.form('form', clear_on_submit=True): # 채팅 입력창 생성
        user_input = st.text_input('당신: ', '') # 입력부분
        submitted = st.form_submit_button('전송') # 전송 버튼
    
    if submitted and user_input:
        user_input1 = user_input.strip() # 채팅 입력값 및 여백제거
        chatbot_output1 = model.chat(user_input1).strip() # text generation된 값 및 여백 제거
        st.session_state.past.append(user_input1) # 입력값을 past 에 append -> 채팅 로그값 저장을 위해
        st.session_state.generated.append(chatbot_output1)
    
    with placeholder.container(): # 리스트에 append된 채팅입력과 로봇출력을 리스트에서 꺼내서 메세지로 출력
        for i in range(len(st.session_state['past'])):
            message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')
            if len(st.session_state['generated']) > i:
                message(st.session_state['generated'][i], key=str(i) + '_bot')
