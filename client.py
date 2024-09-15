import grpc
import lms_pb2
import lms_pb2_grpc
import os
import json
import webbrowser

# Global variable to store the token after login
token = ""

def student_menu(stub):
    while True:
        print("\n--- Student Menu ---")
        print("1. View Assignments")
        print("2. Submit Assignment")
        print("3. View Submitted and Pending Assignments")
        print("4. View uploaded Assignments")
        print("5. View Grades")
        print("6. Add Doubt")
        print("7. View Doubts")
        print("8. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            view_assignment(stub)
        elif choice == '2':
            submit_assignment(stub)
        elif choice == '3':
            view_submitted_assignments(stub)
        elif choice == '4':
            view_submission(stub)
        elif choice == '5':
            view_grades(stub)
        elif choice == '6':
            add_doubt(stub)
        elif choice == '7':
            view_doubts(stub)
        elif choice == '8':
            logout(stub)
            break
        else:
            print("Invalid choice. Please try again.")

def teacher_menu(stub):
    while True:
        print("\n--- Teacher Menu ---")
        print("1. Add Assignment")
        print("2. View Uploaded Assignment")
        print("3. Grade Assignment")
        print("4. View Doubts")
        print("5. Answer Doubts")
        print("6. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_assignment(stub)
        elif choice == '2':
            view_uploaded_questions(stub)
        elif choice == '3':
            grade_assignment(stub)
        elif choice == '4':
            view_doubts(stub)
        elif choice == '5':
            answer_doubts(stub)
        elif choice == '6':
            logout(stub)
            break
        else:
            print("Invalid choice. Please try again.")

def add_assignment(stub):
    assignment_id = input("Enter assignment ID: ")
    assignment_name = input("Enter assignment Name: ")
    response = stub.Post(lms_pb2.PostRequest(type="add_assignment", data=f"{assignment_id},{assignment_name}"))
    if response.status:
        print("Assignment created successfully!")
    else:
        print("Failed to create assignment.")
    file_path = input("Enter the file path to upload: ")

    # Read the file content
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    # Create assignment request
    request = lms_pb2.AssignmentRequest(
        id=assignment_id,
        name=assignment_name,
        file_content=file_content
    )
    
    # Call CreateAssignment RPC
    response = stub.CreateAssignment(request)
    # Handle the response status and message
    if response.status == "success":
        print(f"Success: {response.message}")
    else:
        print(f"Error: {response.message}")


def view_assignment(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("Assignments: ", response.data)
    else:
        print("Failed to retrieve assignments.")
    assignment_id = input("Enter assignment ID: ")
    assignment_name = input("Enter assignment Name: ")
    
    # Create GetAssignment request
    request = lms_pb2.AssignmentQuery(
        id=assignment_id,
        name=assignment_name
    )
    
    # Call GetAssignment RPC
    response = stub.GetAssignment(request)
    print(f"Assignment ID: {response.id}")
    print(f"Assignment Name: {response.name}")
    print(f"Download file here: {response.file_path}")


def submit_assignment(stub):
    assignment_id = input("Enter Assignment ID: ")
    file_path = input("Enter file path: ")
    
    # Read file content
    with open(file_path, 'rb') as file:
        file_content = file.read()
    
    file_name = os.path.basename(file_path)
    student_name = token.split('_')[0]  # Assuming token is formatted as "{username}_token"

    # Send file to server
    response = stub.UploadFile(lms_pb2.UploadFileRequest(
        assignment_name=assignment_id,
        student_name=student_name,
        file_content=file_content,
        file_name=file_name
    ))
    
    if response.status:
        print("Assignment submitted successfully.")
    else:
        print("Failed to submit assignment:", response.message)

def view_submitted_assignments(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_submitted_and_pending_assignments"))
    if response.status:
        print("Pending Assignments: ", response.pending_assignments)
        print("Submitted Assignments: ", response.submitted_assignments)
    else:
        print("Failed to retrieve assignments status.")

def view_grades(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_grades"))
    if response.status:
        print("Grades:")
        for grade_info in response.data:
            print(grade_info)  # This will print assignment names with grades
    else:
        print("Failed to retrieve grades.")
def view_submission(stub):
    # Request the student's name
    student_name = User
    print(f"Logged in as: {User}")

    # Requesting the list of assignment submissions
    response = stub.ViewSubmission(lms_pb2.ViewSubmissionRequest(student_name=student_name))

    if not response.assignments:
        print("No assignments found.")
        return

    # Display the assignments with their status
    print("\nYour Assignment Submissions:")
    for assignment in response.assignments:
        print(f"ID: {assignment.assignment_id}, Status: {assignment.file_status}")
        if assignment.file_status == "Uploaded":
            # Print the clickable link to the assignment file
            if assignment.file_url:
                print(f"Assignment File URL: {assignment.file_url}")
            else:
                print("No file URL available.")
        else:
            print("The file has not been uploaded yet.")


def add_doubt(stub):
    doubt_text = input("Enter your doubt: ")
    response = stub.Post(lms_pb2.PostRequest(type="add_doubt", data=doubt_text))
    if response.status:
        print("Doubt added successfully.")
    else:
        print("Failed to add doubt.")

def view_doubts(stub):
    doubt_type = input("Enter doubt type (unanswered/answered): ")
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_doubts", optional_data=doubt_type))
    if response.status:
        print("Doubts: ", response.data)
    else:
        print("Failed to retrieve doubts.")

def answer_doubts(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_doubts", optional_data="unanswered"))
    if response.status:
        print("Unanswered Doubts: ", response.data)
        doubt_index = input("Enter the index of doubt to answer: ")
        answer_text = input("Enter your answer: ")
        response = stub.Post(lms_pb2.PostRequest(type="answer_doubt", data=f"{doubt_index},{answer_text}"))
        if response.status:
            print("Doubt answered successfully.")
        else:
            print("Failed to answer doubt.")

def grade_assignment(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("Assignments: ", response.data)
        assignment_id = input("Enter Assignment ID to grade: ")

        # Fetch all users
        user_response = stub.GetUsers(lms_pb2.GetUsersRequest())
        if user_response:
            all_students = [user.username for user in user_response.users if user.role == "student"]

            # Get submissions for the assignment
            response = stub.Get(lms_pb2.GetRequest(token=token, type="view_submissions", optional_data=assignment_id))
            if response.status:
                submitted_students = [sub.split(",")[0].split(": ")[1] for sub in response.data]
                print("Submitted Students: ", submitted_students)

                # Segregate submitted and non-submitted students
                non_submitted_students = list(set(all_students) - set(submitted_students))
                print("Non-submitted Students: ", non_submitted_students)

                # Grade non-submitted students as "Fail" and update server with the failed submission entry
                for student in non_submitted_students:
                    stub.Post(lms_pb2.PostRequest(type="grade", data=f"{assignment_id},{student},Fail"))

                # Grade submitted students
                for student in submitted_students:
                    print(f"Student: {student}")
                    file_path = next(sub.split(", ")[1].split(": ")[1] for sub in response.data if sub.split(",")[0].split(": ")[1] == student)
                    print(f"File path for student {student}: {file_path}")
                    grade = input("Enter grade (A to E): ")
                    stub.Post(lms_pb2.PostRequest(type="grade", data=f"{assignment_id},{student},{grade}"))
                print("Grades updated successfully.")
            else:
                print("Failed to retrieve submissions.")
        else:
            print("Failed to retrieve users.")
    else:
        print("Failed to retrieve assignments.")

def submit_assignment(stub):
    assignment_id = input("Enter Assignment ID: ")
    file_path = input("Enter file path: ")
    
    # Read file content
    with open(file_path, 'rb') as file:
        file_content = file.read()
    
    file_name = os.path.basename(file_path)
    student_name = token.split('_')[0]  # Assuming token is formatted as "{username}_token"

    # Send file to server
    response = stub.UploadFile(lms_pb2.UploadFileRequest(
        assignment_name=assignment_id,
        student_name=student_name,
        file_content=file_content,
        file_name=file_name
    ))
    
    if response.status:
        print("Assignment submitted successfully.")
    else:
        print("Failed to submit assignment:", response.message)
        
def view_uploaded_questions(stub):
    # Requesting the list of uploaded assignment questions
    response = stub.ViewQuestions(lms_pb2.ViewQuestionsRequest())

    if not response.questions:
        print("No assignment questions found.")
        return

    # Display the assignment questions with their details
    print("\nUploaded Assignment Questions:")
    for question in response.questions:
        print(f"ID: {question.assignment_id}, Name: {question.assignment_name}")
        if question.file_url:
            normalized_url=question.file_url.replace('\\','/')
            print(f"File URL: {normalized_url}")
        else:
            print("No file URL available.")
def logout(stub):
    response = stub.Logout(lms_pb2.LogoutRequest(token=token))
    if response.status:
        print("Logged out successfully.")
    else:
        print("Failed to logout.")

def main():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = lms_pb2_grpc.LMSStub(channel)
        while True:
            print("\n--- Main Menu ---")
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            choice = input("Enter your choice: ")

            if choice == '1':
                username = input("Enter username: ")
                password = input("Enter password: ")
                role = 'student'
                response = stub.RegisterStudent(lms_pb2.RegisterRequest(username=username, password=password))
                if response.status:
                    print("Registration successful.")
                else:
                    print("Failed to register:", response.message)
            elif choice == '2':
                username = input("Enter username: ")
                password = input("Enter password: ")
                response = stub.Login(lms_pb2.LoginRequest(username=username, password=password))
                if response.status:
                    global token
                    global User
                    User=username
                    token = response.token
                    if username == "teacher":
                        teacher_menu(stub)
                    else:
                        student_menu(stub)
                else:
                    print("Failed to login:", response.message)
            elif choice == '3':
                break
            else:
                print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
