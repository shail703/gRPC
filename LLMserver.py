from concurrent import futures
import grpc
import lms_pb2
import lms_pb2_grpc
from sentence_transformers import SentenceTransformer, util
import torch
import os
import re
from transformers import GPT2Tokenizer, GPT2LMHeadModel, pipeline

# Define the device for transformers
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the GPT-2 model and tokenizer for fallback answers
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
model = GPT2LMHeadModel.from_pretrained('gpt2').to(device)
generator = pipeline('text-generation', model=model, tokenizer=tokenizer, device=device.index if device.type == 'cuda' else -1)

# Load the sentence transformer model for finding relevant content in files
sentence_model = SentenceTransformer('all-MiniLM-L6-v2').to(device)

# Teaching prompts predefined for core Computer Science topics
teaching_prompts = {
    "algorithm": ("An algorithm is a set of instructions designed to perform a specific task. "
                  "For example, the bubble sort algorithm repeatedly steps through the list to be sorted, "
                  "compares each pair of adjacent items, and swaps them if they are in the wrong order."),
    "data structure": ("Data structures are ways of organizing and storing data. Common data structures include "
                       "arrays, linked lists, stacks, queues, trees, and graphs. Each has specific use cases."),
    "database": ("A database is an organized collection of data. Popular database models include relational databases "
                 "like MySQL and NoSQL databases like MongoDB."),
    "operating system": ("An operating system (OS) is system software that manages computer hardware, software resources, "
                         "and provides services for computer programs. Examples include Windows, macOS, and Linux."),
    "networking": ("Networking refers to the practice of connecting computers and other devices to share resources. "
                   "Key concepts include IP addressing, DNS, HTTP, and protocols like TCP/IP."),
    "artificial intelligence": ("Artificial Intelligence (AI) is the simulation of human intelligence by machines. "
                                "It includes subfields like machine learning, natural language processing, and robotics."),
    "machine learning": ("Machine learning is a subfield of AI that focuses on the development of algorithms that can learn from "
                         "and make decisions based on data. Popular techniques include supervised learning, unsupervised learning, "
                         "and reinforcement learning."),
    "programming": ("Programming involves writing code to perform specific tasks using a programming language such as Python, Java, or C++. "
                    "Programming paradigms include object-oriented, functional, and procedural programming."),
    "web development": ("Web development refers to creating websites and web applications. It involves languages like HTML, CSS, and JavaScript "
                        "on the front end, and technologies like Node.js or Django on the back end."),
    "computer networks": ("Computer networks enable computers to communicate with each other. Types of networks include LAN (Local Area Network), "
                          "WAN (Wide Area Network), and wireless networks."),
    "cybersecurity": ("Cybersecurity involves protecting systems, networks, and data from cyber attacks. Key areas include encryption, firewalls, "
                      "intrusion detection, and prevention systems."),
    "cloud computing": ("Cloud computing delivers computing services over the internet, such as servers, storage, databases, and networking. "
                        "Examples include AWS, Microsoft Azure, and Google Cloud."),
    "software engineering": ("Software engineering is the application of engineering principles to software development. It involves phases such as "
                             "requirement analysis, design, coding, testing, and maintenance."),
    "blockchain": ("Blockchain is a distributed ledger technology that ensures transparency and security. It underpins cryptocurrencies like Bitcoin and Ethereum."),
}

# Function to read all .txt files from the content folder
def load_content_files(folder_path):
    content = {}
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.txt'):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r') as file:
                content[file_name] = file.read()
    return content

# Function to find the most relevant snippet from the content files
def find_relevant_content(question, content_data):
    question_embedding = sentence_model.encode(question, convert_to_tensor=True).to(device)

    best_match = None
    best_score = -1

    for file_name, text in content_data.items():
        text_embedding = sentence_model.encode([text], convert_to_tensor=True).to(device)
        similarity_score = util.pytorch_cos_sim(question_embedding, text_embedding)[0][0].item()

        if similarity_score > best_score:
            best_score = similarity_score
            best_match = text

    # If the best score is high enough, return a snippet from the best match
    if best_score > 0.5:  # Threshold for determining relevance
        return best_match[:500] + '...'  # Return the first 500 characters for conciseness
    else:
        return None  # No sufficiently relevant content found

# Simple math query handler
def handle_math_query(question):
    if re.match(r'^\d+[\+\-\*/]\d+=$', question.strip()):
        try:
            result = eval(question[:-1])  # Remove '=' and evaluate
            return str(result)
        except Exception as e:
            return "Error in evaluating the arithmetic expression."
    return None

# Load the content from files (e.g., lectures or PPTs in text form)
content_folder_path = 'content'
content_data = load_content_files(content_folder_path)

# Define the LLM service using gRPC
class LLMService(lms_pb2_grpc.LLMServiceServicer):
    def getLLMAnswer(self, request, context):
        question = request.question
        print(f'Received question: {question}')
        
        # First, check if it's a simple math query
        math_result = handle_math_query(question)
        if math_result is not None:
            return lms_pb2.LLMQueryResponse(answer=math_result)
        
        # Check if there's relevant content in the files
        relevant_content = find_relevant_content(question, content_data)
        if relevant_content:
            response = f"Based on class content: {relevant_content}"
        else:
            # Check predefined teaching prompts
            for topic, explanation in teaching_prompts.items():
                if topic in question.lower():
                    response = explanation
                    break
            else:
                # Use GPT-2 as a fallback for generating an answer
                try:
                    outputs = generator(question, max_length=150, num_return_sequences=1)
                    response = outputs[0]['generated_text']
                except Exception as e:
                    response = "Sorry, I couldn't generate an answer at the moment."
        
        print(f'Generated answer: {response}')
        return lms_pb2.LLMQueryResponse(answer=response)

# Function to start the gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lms_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    server.add_insecure_port('[::]:50052')  # LLM Server runs on port 50052
    server.start()
    print("Server Started")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
