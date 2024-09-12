import grpc
from concurrent import futures
import lms_pb2
import lms_pb2_grpc
import json
import os

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
    
    def GetUsers(self, request, context):
        user_list = []
        for username, details in users.items():
            user_list.append({"username": username, "role": details["role"]})
        return lms_pb2.GetUsersResponse(users=user_list)

    def Get(self, request, context):

        student = request.token.split('_')[0]  # Extract student name from the token
       # print(student)
        
        if request.type == "view_assignments":
            # Show assignments that the student hasn't submitted yet
            pending_assignments = []
            all_assignments=[]
            for assignment_id in assignments:
                all_assignments.append(assignment_id)
                if assignment_id not in submissions or \
                        not any(sub['student'] == student for sub in submissions[assignment_id]):
                    pending_assignments.append(assignment_id)
            
            return lms_pb2.GetResponse(status=True, data=all_assignments)

        elif request.type == "view_submissions":
            assignment_id = request.optional_data
            if assignment_id in submissions:
                # Only show the submissions for this assignment
                assignment_submissions = submissions[assignment_id]
                # Prepare a list to return submission details
                submission_list = [
                    f"Student: {sub['student']}, File: {sub['file']}" 
                    for sub in assignment_submissions
                ]
                return lms_pb2.GetResponse(status=True, data=submission_list)
            else:
                return lms_pb2.GetResponse(status=False, message="No submissions found for the assignment.")

        elif request.type == "view_submitted_and_pending_assignments":
            pending_assignments = []
            submitted_assignments = []

            # Loop through all assignments to classify them for this student
            for assignment_id in assignments:
                if assignment_id in submissions:
                    student_submitted = any(sub['student'] == student for sub in submissions[assignment_id])
                    if student_submitted:
                        submitted_assignments.append(assignment_id)
                    else:
                        pending_assignments.append(assignment_id)
                else:
                    pending_assignments.append(assignment_id)

            response_data = {
                "pending_assignments": pending_assignments,
                "submitted_assignments": submitted_assignments
            }
            print(response_data)
            # Return the response including the "data" field
            return lms_pb2.GetResponse(
                status=True,
                pending_assignments=pending_assignments,
                submitted_assignments=submitted_assignments,
                message="Successfully fetched assignments"  # This ensures the data field is populated
            )
        
        elif request.type == "view_grades":
            # View student's grades along with assignment names
            student_grades = []
            for assignment_id, assignment_submissions in submissions.items():
                for sub in assignment_submissions:
                    if sub.get('student') == student and 'grade' in sub:
                        # Include the assignment name with the grade
                        student_grades.append(f"Assignment: {assignment_id}, Grade: {sub['grade']}")
            return lms_pb2.GetResponse(status=True, data=student_grades)
        
        elif request.type == "view_doubts":
            if request.optional_data == "unanswered":
                indexed_doubts = [f"{i}: {doubt}" for i, doubt in enumerate(doubts.get("unanswered", []))]
            elif request.optional_data == "answered":
                # Return both doubt and answer for answered doubts
                indexed_doubts = [f"{i}: {doubt['doubt']} (Answer: {doubt['answer']})" for i, doubt in enumerate(doubts.get("answered", []))]
            else:
                return lms_pb2.GetResponse(status=False)
            return lms_pb2.GetResponse(status=True, data=indexed_doubts)


    def Post(self, request, context):
        if request.type == "add_assignment":
            assignment_id, assignment_name = request.data.split(",", 1)
            assignments[assignment_id] = {"name": assignment_name}
            save_data(ASSIGNMENT_FILE, assignments)
            return lms_pb2.PostResponse(status=True)

        elif request.type == "submit_assignment":
            assignment_id, file_path = request.data.split(",")
            submissions[assignment_id] = submissions.get(assignment_id, []) + [{"student": request.token.split('_')[0], "file": file_path}]
            save_data(SUBMISSION_FILE, submissions)
            return lms_pb2.PostResponse(status=True)

        elif request.type == "grade":
            assignment_id, student_username, grade = request.data.split(",")
            # Handle the case where the grade is "Fail" and there is no existing submission
            if grade.lower() == "fail" and student_username not in [sub['student'] for sub in submissions.get(assignment_id, [])]:
                # Add a failed submission entry with path set to None
                if assignment_id not in submissions:
                    submissions[assignment_id] = []
                submissions[assignment_id].append({"student": student_username, "file": None, "grade": "Fail"})
            else:
                # Update existing submission with the grade
                for submission in submissions.get(assignment_id, []):
                    if submission['student'] == student_username:
                        submission["grade"] = grade
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
            
            # Store both doubt and answer as a dictionary
            answered_doubt = {"doubt": doubts["unanswered"].pop(int(doubt_index)), "answer": answer}
            doubts["answered"].append(answered_doubt)
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
