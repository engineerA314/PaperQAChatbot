# PaperQAChatbot

openai api key 세팅 후
```
pip install -r requirements.txt
streamlit run streamlit_practice.py
```
## Abstract
haystack 을 이용한 Retrieval Augmented Generator + Chatbot

Transformer 논문과 RETRO 논문에 대한 QA가 가능한 chatbot 구현

streamlit을 통해 간단하게 앱 프로토타입 구현

## Idea
질문이 들어오면 haystack 의 DocumentStore 와 EmbeddingRetreiver 를 이용해 질문과 가장 유사도가 높은 Chunk를 뽑고, 이를 chatbot의 prompt에 넣어줌

**개선점**
- Question 과 Document의 chunk 들 사이의 유사도를 확인해 threshold=0.55 이하일 경우에는 chatbot에게 chunk를 제공하지 않음
  - 이를 통해 일상적인 대화가 가능해졌음


## Prompt Design
- gpt 논문 QA 챗봇 세팅 prompt & Abstract of the paper
```
    Q : You are a chatbot that can answer the questions about the paper. This is the abstract of the paper you should understand.
    {abstract}
    A : I understand the abstract. I'm ready to answer the questions.
```
- past QA list
- Question
- relative information chunks
```
These informations from the paper below might be helpful.
{chunk1}
{chunk2}
{chunk3}
```

## Result
![image](https://user-images.githubusercontent.com/86403521/212892566-f69302cd-302d-4c72-8713-5d4ab309a079.png)


## Problems
1. embedding dot product 기반 유사도가 적절하지 못함. 질문과 크게 관련없어보이는 정보들을 가져옴 - **개선 완료**
- 숫자가 들어있는 무의미한 chunk들이 선택되는 경우가 종종 있음.

![image](https://user-images.githubusercontent.com/86403521/212065152-f5390207-db00-470a-8675-0d9e6cb8b4de.png)


- top k 만 사용하지 말고 score 에 threshold 를 설정해놓는 것이 좋지 않을까 싶음.


2. relative information chunks 는 유저에게 보이지 않는데, 이를 유저가 안다는 식으로 대답함. "in paragraph 1, ..." 와 같은 식으로 relative information chunks 내부의 내용을 인용하면서 대답하는 경우가 있음

3. abstract 를 논문에서 주어진 것을 사용했는데 이거보다 더 좋은 방법이 있을 수도 있음

4. 일상적인 대화가 불가능함  - **개선 완료**
```
Ask Question : Thank you. You helped me a lot.
A :  I understand the information. I'm ready to answer the questions.
```
위와 같은 식으로 prompt 에 의해 일상적인 대화를 할 수가 없음.


