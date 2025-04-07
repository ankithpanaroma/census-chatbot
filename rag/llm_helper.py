from openai import OpenAI
from fastapi import HTTPException
import cohere
import os

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
co = cohere.Client(api_key=os.environ.get('COHERE_API_KEY'))

COHERE_EMBEDDING_MODEL = 'embed-english-v3.0'


def fetch_embeddings(texts: list[str], embedding_type: str = 'search_document', batch_size: int = 10) -> list[list[float]]:
    """
    Fetch embeddings using the Cohere API in batches.
    :param texts: List of texts to embed.
    :param embedding_type: Type of embedding (not used for Cohere).
    :param batch_size: Number of texts to process in each batch.
    :return: List of embeddings.
    """
    embeddings = []
    try:
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            results = co.embed(
                texts=batch,
                model=COHERE_EMBEDDING_MODEL,
                input_type="search_query"  # Ensure input_type is set to "text"
            ).embeddings
            embeddings.extend(results)
        return embeddings
    except Exception as e:
        print(e)
        raise HTTPException(
            404, detail=f'Cohere embedding fetch failed with error: {e}'
        )


def question_and_answer_prompt(question: str, context: list[str]) -> str:
    context_str = '\n'.join(context)
    return f"""
   You are an expert on the Census of India instruction manuals, including 'Houselisting and Housing Census,' 'Updating of Abridged Houselist and Filling up of the Household Schedule,' and 'National Population Register.' Please answer users' questions based on these documents. Continue the conversation based on the context below.
    ---------------------
    {context_str}
    ---------------------
    Given the context information and prior knowledge, answer the query.
    Query: {question}
    Answer:
    """

def synthesize_answer(question: str, context: list[str]) -> str:
    print("context::", context)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": question_and_answer_prompt(
                question, context)}
        ],
        temperature=0
    )
    answer = response.choices[0].message.content.strip()  # Ensure the answer is a clean string
    print(f"Price: {response.usage.total_tokens * 0.003 / 1000} $")
    return answer
