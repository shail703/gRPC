import grpc
from concurrent import futures
import json
import os
import lms_pb2
import lms_pb2_grpc

# File paths for storing users, assignments, submissions, and doubts
USER_FILE = 'users.json'
ASSIGNMENT_FILE = 'assignments.json'
SUBMISSION_FILE = 'submissions.json'
DOUBT_FILE = 'doubts.json'

# Load data from JSON files
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

# Save data to JSON files
def save_data(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# Initialize storage
users = load_data(USER_FILE)
assignments = load_data(ASSIGNMENT_FILE)
submissions = load_data(SUBMISSION_FILE)
doubts = load_data(DOUBT_FILE)

# Hardcoded teacher account
if "teacher" not in users:
    users["teacher"] = {"password": "1234", "role": "teacher"}
    save_data(USER_FILE, users)

class LMSServicer(lms_pb2_grpc.LMSServicer):
    def RegisterStudent(self, request, context):
        if request.username in users:
            return lms_pb2.RegisterResponse(status=False, message="User already exists.")
        users[request.username] = {"password": request.password, "role": "student"}
        save_data(USER_FILE, users)
        return lms_pb2.RegisterResponse(status=True)

    def Login(self, request, context):
        if request.username in users and users[request.username]["password"] == request.password:
            token = f"{request.username}_token"
            return lms_pb2.LoginResponse(status=True, token=token)
        return lms_pb2.LoginResponse(status=False, message="Invalid credentials")

    def Get(self, request, context):
        if request.type == "view_assignments":
            return lms_pb2.GetResponse(status=True, data=list(assignments.keys()))

        elif request.type == "view_submissions":
            assignment_id = request.optional_data
            if assignment_id in submissions:
                indexed_submissions = [f"{i}: {sub['student']} - {sub['file']}" for i, sub in enumerate(submissions[assignment_id])]
                return lms_pb2.GetResponse(status=True, data=indexed_submissions)
            return lms_pb2.GetResponse(status=False)

        elif request.type == "view_grades":
            student = request.optional_data
            student_grades = [sub['grade'] for sub in submissions.values() if sub.get('student') == student]
            return lms_pb2.GetResponse(status=True, data=student_grades)

        elif request.type == "view_doubts":
            if request.optional_data == "unanswered":
                indexed_doubts = [f"{i}: {doubt}" for i, doubt in enumerate(doubts.get("unanswered", []))]
            elif request.optional_data == "answered":
                indexed_doubts = [f"{i}: {doubt}" for i, doubt in enumerate(doubts.get("answered", []))]
            else:
                return lms_pb2.GetResponse(status=False)
            return lms_pb2.GetResponse(status=True, data=indexed_doubts)


    def Post(self, request, context):
        if request.type == "add_assignment":
            assignments[request.data] = []
            save_data(ASSIGNMENT_FILE, assignments)
            return lms_pb2.PostResponse(status=True)

        elif request.type == "submit_assignment":
            assignment_id, file_path = request.data.split(",")
            submissions[assignment_id] = submissions.get(assignment_id, []) + [{"student": request.token.split('_')[0], "file": file_path}]
            save_data(SUBMISSION_FILE, submissions)
            return lms_pb2.PostResponse(status=True)

        elif request.type == "grade":
            assignment_id, student_index, grade = request.data.split(",")
            submissions[assignment_id][int(student_index)]["grade"] = grade
            save_data(SUBMISSION_FILE, submissions)
            return lms_pb2.PostResponse(status=True)

        elif request.type == "add_doubt":
            doubts["unanswered"] = doubts.get("unanswered", []) + [request.data]
            save_data(DOUBT_FILE, doubts)
            return lms_pb2.PostResponse(status=True)

        elif request.type == "answer_doubt":
            doubt_index, answer = request.data.split(",")
            if "answered" not in doubts:
                doubts["answered"] = []
            doubts["answered"].append(doubts["unanswered"].pop(int(doubt_index)))
            save_data(DOUBT_FILE, doubts)
            return lms_pb2.PostResponse(status=True)

        return lms_pb2.PostResponse(status=False)

    def Logout(self, request, context):
        return lms_pb2.LogoutResponse(status=True)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lms_pb2_grpc.add_LMSServicer_to_server(LMSServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()