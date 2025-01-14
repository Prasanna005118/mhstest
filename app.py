import ollama

# Load the dataset
dataset = []
try:
    with open('KPK-Mental-Health.txt', 'r', encoding='utf-8') as file:
        dataset = file.readlines()
    print(f'Loaded {len(dataset)} entries')
except UnicodeDecodeError as e:
    print(f"Encoding issue: {e}")
except FileNotFoundError:
    print("The file 'KPK-Mental-Health.txt' was not found. Please check the file path.")

# Define models
EMBEDDING_MODEL = 'hf.co/CompendiumLabs/bge-base-en-v1.5-gguf'
LANGUAGE_MODEL = 'hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF'

# Initialize vector database
VECTOR_DB = []
def add_chunk_to_database(chunk):
    embedding = ollama.embed(model=EMBEDDING_MODEL, input=chunk)['embeddings'][0]
    VECTOR_DB.append((chunk, embedding))

for i, chunk in enumerate(dataset):
    add_chunk_to_database(chunk)
    #print(f'Added chunk {i+1}/{len(dataset)} to the database')

# Define cosine similarity
def cosine_similarity(a, b):
    dot_product = sum([x * y for x, y in zip(a, b)])
    norm_a = sum([x ** 2 for x in a]) ** 0.5
    norm_b = sum([x ** 2 for x in b]) ** 0.5
    return dot_product / (norm_a * norm_b)

# Retrieve relevant chunks
def retrieve(query, top_n=3):
    query_embedding = ollama.embed(model=EMBEDDING_MODEL, input=query)['embeddings'][0]
    similarities = []
    for chunk, embedding in VECTOR_DB:
        similarity = cosine_similarity(query_embedding, embedding)
        similarities.append((chunk, similarity))
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]

# Get user query
input_query = input('Ask me a question: ')
retrieved_knowledge = retrieve(input_query)

print('Retrieved knowledge:')
for chunk, similarity in retrieved_knowledge:
    print(f' - (similarity: {similarity:.2f}) {chunk}')

# Instruction prompt for the chatbot
instruction_prompt = f'''You are a helpful chatbot.
Use only the following pieces of context to answer the question. Don't make up any new information:
{''.join([f' - {chunk}' for chunk, similarity in retrieved_knowledge])}
'''

# Chatbot response
stream = ollama.chat(
    model=LANGUAGE_MODEL,
    messages=[
        {'role': 'system', 'content': instruction_prompt},
        {'role': 'user', 'content': input_query},
    ],
    stream=True,
)

# Print chatbot response in real-time
print('Chatbot response:')
for chunk in stream:
    print(chunk['message']['content'], end='', flush=True)