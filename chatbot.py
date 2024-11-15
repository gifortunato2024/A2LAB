from llama_index.llms.groq import Groq
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, get_response_synthesizer
from llama_index.core import StorageContext
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core import Settings
from llama_index.vector_stores.duckdb import DuckDBVectorStore

import os 

#Variáveis do ambiente
with open('chave_groq', 'r') as arquivo:
    chave_groq = arquivo.read()
groq_model = 'llama-3.2-90b-vision-preview'
pasta_pdfs = 'pdfs'
modelo_embeddings = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
Settings.llm = Groq(api_key=chave_groq, model=groq_model, temperature=0)
Settings.embed_model = HuggingFaceEmbedding(model_name=modelo_embeddings)
Settings.chunk_size = 2048
Settings.chunk_overlap = 512

documents = SimpleDirectoryReader(pasta_pdfs).load_data()

#Criação do índice
vector_store = DuckDBVectorStore('rag.duckdb', persist_dir='rag')
storage_context = StorageContext.from_defaults(vector_store=vector_store)
vector_index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

#Criação do recuperador
retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=5)
response_synthesizer = get_response_synthesizer()
query_engine = RetrieverQueryEngine.from_args(retriever=retriever, response_synthesizer=response_synthesizer,
                                    response_mode='tree_sumarize',
                                    node_postprocessors=[SimilarityPostprocessor(similarity_threshold=0.3)])