# Distributed LMS with gRPC

## Prerequisites

Make sure you have the following installed on your system:

- Python 3.x: [Download and install]
- gRPC: Install gRPC and protocol buffers using the following command:

```bash
                 pip install grpcio grpcio-tools


Step 1: Clone the Repository
                 git clone https://github.com/your-repository/distributed-lms.git
                 cd distributed-lms


Step 2: Install Dependencies
                 pip install -r requirements.txt
                 pip install grpcio grpcio-tools protobuf


Step 3: Compile the Protocol Buffers
Run the following command to compile the .proto file:
                  python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. lms.proto


This will generate the necessary lms_pb2.py and lms_pb2_grpc.py files.


Step 4: Ensure Folder Structure
Make sure the following folders and files are present in the root directory:




distributed-lms/
│
├── assignments/ # Directory for storing assignment files
│ ├── questions/ # Directory for assignment question PDFs
│
├── users.json # Stores user information (teachers and students)
├── assignments.json # Stores assignment details
├── submissions.json # Stores submitted assignments
├── doubts.json # Stores doubts and answers




Step 5: Run the Server
To start the gRPC server, run the following command:
                   python server.py
This will start the gRPC server on port 50051.




Step 6: Run the Client
                  python client.py
