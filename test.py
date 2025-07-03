import grpc
import lms_pb2
import lms_pb2_grpc

def test_connection(stub):
    response = stub.getLLMAnswer(lms_pb2.LLMQueryRequest(question="Test"))
    print("Test connection response:", response.answer)

def run():
    with grpc.insecure_channel('localhost:50055') as channel:
        stub = lms_pb2_grpc.LLMServiceStub(channel)
        test_connection(stub)

if __name__ == '__main__':
    run()

    openai.api_key = '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'

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