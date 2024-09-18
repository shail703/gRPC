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
STUDENT_FILE = 'studentInfo.json'
ASSIGNMENT_FOLDER = 'assignments'  # Folder to store assignment submissions
QUESTIONS_FOLDER = os.path.join(ASSIGNMENT_FOLDER, 'questions')

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
studentInfo = load_data(STUDENT_FILE)

# Create assignments directory if it doesn't exist
if not os.path.exists(ASSIGNMENT_FOLDER):
    os.makedirs(ASSIGNMENT_FOLDER)

# Ensure folder structure exists
if not os.path.exists(QUESTIONS_FOLDER):
    os.makedirs(QUESTIONS_FOLDER)

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

    def ViewQuestions(self, request, context):
        questions = []
        questions_folder = os.path.join(ASSIGNMENT_FOLDER, "questions")

        with open(ASSIGNMENT_FILE, 'r') as file:
            assignments_info = json.load(file)

        if not os.path.exists(questions_folder):
            error_msg = f"Questions folder does not exist: {questions_folder}"
            print(error_msg)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.UNKNOWN)
            return lms_pb2.ViewQuestionsResponse(questions=[])

        for assignment_id, info in assignments_info.items():
            assignment_name = info["name"]
            pdf_file_path = os.path.join(questions_folder, f"{assignment_name}.pdf")

            if os.path.isfile(pdf_file_path):
                file_url = f"file://{pdf_file_path}"
                questions.append(lms_pb2.AssignmentQuestion(
                    assignment_id=assignment_id,
                    assignment_name=assignment_name,
                    file_url=file_url
                ))

        return lms_pb2.ViewQuestionsResponse(questions=questions)

    def UploadFile(self, request, context):
        assignment_name = request.assignment_name
        student_name = request.student_name
        file_content = request.file_content
        file_name = request.file_name

        assignment_path = os.path.join(ASSIGNMENT_FOLDER, assignment_name)
        if not os.path.exists(assignment_path):
            os.makedirs(assignment_path)

        file_path = os.path.join(assignment_path, f"{student_name}_{file_name}")
        with open(file_path, 'wb') as file:
            file.write(file_content)

        submissions[assignment_name] = submissions.get(assignment_name, []) + [{"student": student_name, "file": file_path}]
        save_data(SUBMISSION_FILE, submissions)
        return lms_pb2.UploadFileResponse(status=True, message="File uploaded successfully.")

    def DownloadFile(self, request, context):
        assignment_name = request.assignment_name
        student_name = request.student_name

        assignment_submissions = submissions.get(assignment_name, [])
        for sub in assignment_submissions:
            if sub['student'] == student_name:
                file_path = sub['file']
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                    file_name = os.path.basename(file_path)
                    return lms_pb2.DownloadFileResponse(status=True, file_content=file_content, file_name=file_name)
        
        return lms_pb2.DownloadFileResponse(status=False, message="File not found.")

    def CreateAssignment(self, request, context):
        try:
            assignment_name = request.name
            file_content = request.file_content
            file_path = os.path.join(QUESTIONS_FOLDER, f"{assignment_name}.pdf")
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            return lms_pb2.AssignmentResponse(status="success", message="Assignment created and file uploaded successfully!")
        except Exception as e:
            return lms_pb2.AssignmentResponse(status="error", message=str(e))

    def GetAssignment(self, request, context):
        assignment_id = request.id
        assignment_name = request.name
        file_path = os.path.join(QUESTIONS_FOLDER, f"{assignment_name}.pdf")
        
        return lms_pb2.AssignmentDetails(
            id=assignment_id,
            name=assignment_name,
            file_path=file_path
        )

    def ViewSubmission(self, request, context):
        student_name = request.student_name
        assignments1 = []

        if not os.path.exists(ASSIGNMENT_FOLDER):
            context.set_details(f"Assignment folder does not exist: {ASSIGNMENT_FOLDER}")
            context.set_code(grpc.StatusCode.UNKNOWN)
            return lms_pb2.ViewSubmissionResponse(assignments=[])

        for assignment_id in os.listdir(ASSIGNMENT_FOLDER):
            assignment_path = os.path.join(ASSIGNMENT_FOLDER, assignment_id)
            if os.path.isdir(assignment_path) and assignment_id != "questions":
                student_file = None
                for file_name in os.listdir(assignment_path):
                    if file_name.startswith(student_name):
                        student_file = file_name
                        break

                file_url = f"file://{assignment_path}/{student_file}" if student_file else ""

                assignments1.append(lms_pb2.Assignment(
                    assignment_id=assignment_id,
                    assignment_name=f"Assignment {assignment_id}",
                    file_status="Uploaded" if student_file else "Not Uploaded",
                    file_url=file_url
                ))

        return lms_pb2.ViewSubmissionResponse(assignments=assignments1)

    def Get(self, request, context):
        student = request.token.split('_')[0]  
        
        if request.type == "view_assignments":
            pending_assignments = []
            all_assignments = []
            for assignment_id, assignment in assignments.items():
                all_assignments.append(f"{assignment_id}: {assignment['name']}")
                if assignment_id not in submissions or \
                        not any(sub['student'] == student for sub in submissions[assignment_id]):
                    pending_assignments.append(f"{assignment_id}: {assignment['name']}")
            
            return lms_pb2.GetResponse(status=True, data=all_assignments)

        elif request.type == "view_submissions":
            assignment_id = request.optional_data
            if assignment_id in submissions:
                assignment_submissions = submissions[assignment_id]
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
            return lms_pb2.GetResponse(
                status=True,
                pending_assignments=pending_assignments,
                submitted_assignments=submitted_assignments,
                message="Successfully fetched assignments"
            )
        
        elif request.type == "view_grades":
            student_grades = []
            for assignment_id, assignment_submissions in submissions.items():
                for sub in assignment_submissions:
                    if student == sub.get('student') and 'grade' in sub:
                        student_grades.append(f"Assignment: {assignment_id}, Grade: {sub['grade']}")
            return lms_pb2.GetResponse(status=True, data=student_grades)
        
        elif request.type == "view_doubts":
            if request.optional_data in doubts:
                return lms_pb2.GetResponse(status=True, data=doubts[request.optional_data])
            return lms_pb2.GetResponse(status=False, message="No doubts found for the assignment.")

        return lms_pb2.GetResponse(status=False, message="Unknown request type")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lms_pb2_grpc.add_LMSServicer_to_server(LMSServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
