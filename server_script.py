import grpc
from concurrent import futures
import lms_pb2
import lms_pb2_grpc
import json
import os
import subprocess
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
# File paths for storing users, assignments, submissions, and doubts
USER_FILE = 'users.json'
ASSIGNMENT_FILE = 'assignments.json'
SUBMISSION_FILE = 'submissions.json'
DOUBT_FILE = 'doubts.json'
ASSIGNMENT_FOLDER = 'assignments'  # Folder to store assignment submissions
QUESTIONS_FOLDER = os.path.join(ASSIGNMENT_FOLDER, 'questions')
MATERIAL_FOLDER='content'
LOG_FILE = 'log.txt'  # Log file to record file changes
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

# Create assignments directory if it doesn't exist
if not os.path.exists(ASSIGNMENT_FOLDER):
    os.makedirs(ASSIGNMENT_FOLDER)
# Ensure folder structure exists
if not os.path.exists(QUESTIONS_FOLDER):
    os.makedirs(QUESTIONS_FOLDER)
# Create content directory if it doesn't exist
if not os.path.exists(MATERIAL_FOLDER):
    os.makedirs(MATERIAL_FOLDER)
# Hardcoded teacher account
if "teacher" not in users:
    users["teacher"] = {"password": "1234", "role": "teacher"}
    save_data(USER_FILE, users)

# LogHandler class to handle directory events
class LogHandler(FileSystemEventHandler):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.serial_no = 1 if not os.path.exists(log_file) else self._get_last_serial()

    def _get_last_serial(self):
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                return int(lines[-1].split()[0]) + 1 if lines else 1
        except Exception:
            return 1

    def log_event(self, event, event_type):
        # Ignore log.txt file and "__pycache__" subfolder
        if self.log_file in event.src_path or "__pycache__" in event.src_path:
            return
        relative_path = os.path.relpath(event.src_path)
        with open(self.log_file, 'a') as log:
            log.write(f"{self.serial_no}. {event_type}: {relative_path}\n")
        self.serial_no += 1

    def on_created(self, event):
        if not event.is_directory:
            self.log_event(event, "Created")

    def on_modified(self, event):
        if not event.is_directory:
            self.log_event(event, "Modified")

# LogFileObserver class to observe changes to log.txt itself
class LogFileObserver(FileSystemEventHandler):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file

    def on_modified(self, event):
        if event.src_path == os.path.abspath(self.log_file):
            subprocess.Popen([sys.executable, "leader_sync.py"])

# Initialize logging of file changes in a directory and observe log.txt itself
def start_logging():
    # Set up directory observer
    observer = Observer()
    log_handler = LogHandler(LOG_FILE)
    observer.schedule(log_handler, path=os.getcwd(), recursive=True)
    
    # Set up observer for log.txt itself
    log_file_observer = Observer()
    log_file_handler = LogFileObserver(LOG_FILE)
    log_file_observer.schedule(log_file_handler, path=os.path.dirname(os.path.abspath(LOG_FILE)), recursive=False)

    # Start both observers
    observer.start()
    log_file_observer.start()

    return observer, log_file_observer


class LLMService(lms_pb2_grpc.LLMServiceServicer):
    # Existing methods

    def getLLMAnswer(self, request, context):
        question = request.question  # Take the student's question
        
        try:
            # Here you would normally forward the request to an LLM server or process it
            # For now, we'll return a simple placeholder response
            llm_response = "This is a response to: " + question
            
            # Create and return the LLMQueryResponse message
            return lms_pb2.LLMQueryResponse(answer=llm_response)
        
        except Exception as e:
            # Handle exceptions and provide a meaningful error message
            context.set_details(f"An error occurred: {str(e)}")
            context.set_code(grpc.StatusCode.INTERNAL)
            return lms_pb2.LLMQueryResponse(answer="An internal error occurred.")


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

        # Define paths
        questions_folder = os.path.join(ASSIGNMENT_FOLDER, "questions")

        try:
            # Try reading assignments information from JSON file
            with open(ASSIGNMENT_FILE, 'r') as file:
                assignments_info = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return message if the JSON file is missing or corrupted
            error_msg = "No assignments found."
            print(error_msg)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return lms_pb2.ViewQuestionsResponse(questions=[])

            # Check if questions folder exists and contains files
        if not os.path.exists(questions_folder) or not os.listdir(questions_folder):
            error_msg = "No assignments found."
            print(error_msg)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return lms_pb2.ViewQuestionsResponse(questions=[])

        for assignment_id, info in assignments_info.items():
            assignment_name = info["name"]
            # Construct the file path for the PDF
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

        # Create assignment folder
        assignment_path = os.path.join(ASSIGNMENT_FOLDER, assignment_name)
        if not os.path.exists(assignment_path):
            os.makedirs(assignment_path)

        # Save file with student's name to avoid conflicts
        file_path = os.path.join(assignment_path, f"{student_name}_{file_name}")
        with open(file_path, 'wb') as file:
            file.write(file_content)

        # Log submission in the JSON file
        submissions[assignment_name] = submissions.get(assignment_name, []) + [{"student": student_name, "file": file_path}]
        save_data(SUBMISSION_FILE, submissions)
        return lms_pb2.UploadFileResponse(status=True, message="File uploaded successfully.")

    def DownloadFile(self, request, context):
        assignment_name = request.assignment_name
        student_name = request.student_name

        # Fetch the submission details
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
        # Save the uploaded file in the assignment folder
        try:
            assignment_name = request.name
            file_content = request.file_content
            file_path = os.path.join(QUESTIONS_FOLDER, f"{assignment_name}.pdf")  # assuming a PDF, change extension as necessary
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Respond with success message
            return lms_pb2.AssignmentResponse(status="success", message="Assignment created and file uploaded successfully!")
        except Exception as e:
            return lms_pb2.AssignmentResponse(status="error", message=str(e))

    def CreateMaterial(self, request, context):
        # Save the uploaded file in the assignment folder
        try:
            material_name = request.name
            file_content = request.file_content
            file_path = os.path.join(MATERIAL_FOLDER, f"{material_name}.txt")  # assuming a PDF, change extension as necessary
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Respond with success message
            return lms_pb2.MaterialResponse(status="success", message="Study material created and file uploaded successfully!")
        except Exception as e:
            return lms_pb2.MaterialResponse(status="error", message=str(e))
    def GetAssignment(self, request, context):
        # Fetch assignment details and provide file link
        assignment_id = request.id
        assignment_name = request.name
        
        # Construct file path
        file_path = os.path.join(QUESTIONS_FOLDER, f"{assignment_name}.pdf")
        
            # Check if the file exists
        if not os.path.isfile(file_path):
            # Return error if the file does not exist
            error_msg = f"No assignment found with name '{assignment_name}'."
            print(error_msg)
            context.set_details(error_msg)
            context.set_code(grpc.StatusCode.NOT_FOUND)
            return lms_pb2.AssignmentDetails()  # Return empty response
        
        # Return assignment details along with file path
        return lms_pb2.AssignmentDetails(
            id=assignment_id,
            name=assignment_name,
            file_path=file_path
        )
    def ViewSubmission(self, request, context):
        student_name = request.student_name
        assignments1 = []  # List to store the assignment objects

        if not os.path.exists(ASSIGNMENT_FOLDER):
            context.set_details(f"Assignment folder does not exist: {ASSIGNMENT_FOLDER}")
            context.set_code(grpc.StatusCode.UNKNOWN)
            return lms_pb2.ViewSubmissionResponse(assignments=[])

        # Iterate through each assignment directory to check if a submission exists for the student
        for assignment_id in os.listdir(ASSIGNMENT_FOLDER):
            assignment_path = os.path.join(ASSIGNMENT_FOLDER, assignment_id)
            # Skip the 'questions' folder
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

        # Return the response with the list of assignments
        return lms_pb2.ViewSubmissionResponse(assignments=assignments1)
    
    
    def Get(self, request, context):

        student = request.token.split('_')[0]  # Extract student name from the token
       # print(student)
        
        if request.type == "view_assignments":
            # Show assignments that the student hasn't submitted yet
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
                    if student == sub.get('student') and 'grade' in sub:
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

def serve(port):
    # Start file logging in the background
    observer, log_file_observer = start_logging()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lms_pb2_grpc.add_LMSServicer_to_server(LMSServicer(), server)
    lms_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    server.add_insecure_port(f'[::]:' + port)
    print("Server started on port " + port )
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        observer.stop()
        log_file_observer.stop()
        observer.join()
        log_file_observer.join()

if __name__ == "__main__":
    serve(str(int(sys.argv[1])+1))
