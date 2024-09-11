import os
import grpc
import lms_pb2
import lms_pb2_grpc
# Global variable to store the token after login
token = ""

def student_menu(stub):
    while True:
        print("\n--- Student Menu ---")
        print("1. View Assignments")
        print("2. Submit Assignment")
        print("3. View Submitted and Pending Assignments")
        print("4. View Grades")
        print("5. Add Doubt")
        print("6. View Doubts")
        print("7. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            view_assignments(stub)
        elif choice == '2':
            submit_assignment(stub)
        elif choice == '3':
            view_submitted_assignments(stub)
        elif choice == '4':
            view_grades(stub)
        elif choice == '5':
            add_doubt(stub)
        elif choice == '6':
            view_doubts(stub)
        elif choice == '7':
            logout(stub)
            break
        else:
            print("Invalid choice. Please try again.")

def teacher_menu(stub):
    while True:
        print("\n--- Teacher Menu ---")
        print("1. Add Assignment")
        print("2. View Submissions")
        print("3. Grade Assignment")
        print("4. View Doubts")
        print("5. Answer Doubts")
        print("6. Logout")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_assignment(stub)
        elif choice == '2':
            view_submissions(stub)
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

# Student Functions
def view_assignments(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("\nAssignments:")
        for idx, assignment in enumerate(response.data):
            print(f"{idx + 1}. {assignment}")
    else:
        print("Failed to retrieve assignments.")

def submit_assignment(stub):
    # Fetch assignments and display them with index
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        pending_assignments = response.data  # List of assignments
        if not pending_assignments:
            print("No pending assignments to submit.")
            return

        print("\nPending Assignments:")
        for idx, assignment in enumerate(pending_assignments):
            print(f"{idx + 1}. {assignment}")

        assignment_index = int(input("Enter the assignment number to submit: ")) - 1
        if 0 <= assignment_index < len(pending_assignments):
            assignment_id = pending_assignments[assignment_index]

            file_path = input("Drag and drop your file here: ").strip().replace("'", "")
            if os.path.exists(file_path):
                response = stub.Post(lms_pb2.PostRequest(token=token, type="submit_assignment", data=f"{assignment_id},{file_path}"))
                if response.status:
                    print("Assignment submitted successfully!")
                else:
                    print("Failed to submit assignment.")
            else:
                print("File does not exist.")
        else:
            print("Invalid selection.")
    else:
        print("Failed to retrieve assignments.")

def view_submitted_assignments(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("\nYour Assignments:")
        for idx, assignment in enumerate(response.data):
            print(f"{idx + 1}. {assignment}")
    else:
        print("Failed to retrieve assignments.")

def view_grades(stub):
    assignment_id = input("Enter assignment ID to view grades: ")
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_grades", optional_data=assignment_id))
    if response.status:
        print("\nGrades:")
        for idx, grade in enumerate(response.data):
            print(f"{idx + 1}. {grade}")
    else:
        print("Failed to retrieve grades.")

def add_doubt(stub):
    doubt = input("Enter your doubt: ")
    response = stub.Post(lms_pb2.PostRequest(token=token, type="add_doubt", data=doubt))
    if response.status:
        print("Doubt added successfully!")
    else:
        print("Failed to add doubt.")



def view_doubts(stub):
    # Retrieve both solved and unsolved doubts
    response_unsolved = stub.Get(lms_pb2.GetRequest(token=token, type="view_doubts", optional_data="unanswered"))
    response_solved = stub.Get(lms_pb2.GetRequest(token=token, type="view_doubts", optional_data="answered"))

    if response_unsolved.status or response_solved.status:
        print("\nDoubts:")

        # Display unsolved doubts
        if response_unsolved.status and response_unsolved.data:
            print("\nUnanswered Doubts:")
            for idx, doubt in enumerate(response_unsolved.data):
                print(f" {doubt}")
        else:
            print("No unanswered doubts.")

        # Display solved doubts
        if response_solved.status and response_solved.data:
            print("\nAnswered Doubts:")
            for idx, doubt in enumerate(response_solved.data):
                print(f" {doubt}")
        else:
            print("No answered doubts.")
    else:
        print("Failed to retrieve doubts.")

# Teacher Functions
def add_assignment(stub):
    assignment_title = input("Enter the assignment title: ")
    response = stub.Post(lms_pb2.PostRequest(token=token, type="add_assignment", data=assignment_title))
    if response.status:
        print("Assignment added successfully!")
    else:
        print("Failed to add assignment.")

def view_submissions(stub):
    # View assignments with indexes for selection
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("\nAvailable Assignments:")
        for idx, assignment in enumerate(response.data):
            print(f"{idx + 1}. {assignment}")
        assignment_index = int(input("Enter the assignment index: ")) - 1

        # Fetch submissions for the selected assignment
        response = stub.Get(lms_pb2.GetRequest(token=token, type="view_submissions", optional_data=str(assignment_index)))
        if response.status:
            print("\nSubmissions:")
            for idx, submission in enumerate(response.data):
                print(f"{idx + 1}. {submission}")
        else:
            print("Failed to retrieve submissions.")
    else:
        print("Failed to retrieve assignments.")

def grade_assignment(stub):
    # Show list of assignments
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("\nAvailable Assignments:")
        for idx, assignment in enumerate(response.data):
            print(f"{idx + 1}. {assignment}")
        assignment_index = int(input("Enter the assignment index: ")) - 1

        # Show list of students in the selected assignment
        response = stub.Get(lms_pb2.GetRequest(token=token, type="view_submissions", optional_data=str(assignment_index)))
        if response.status:
            print("\nStudents in Assignment:")
            for student_idx, submission in enumerate(response.data):
                print(f"{student_idx + 1}. {submission}")

            student_index = int(input("Enter the student index: ")) - 1
            grade = input("Enter the grade (0-10): ")
            response = stub.Post(lms_pb2.PostRequest(token=token, type="grade", data=f"{assignment_index},{student_index},{grade}"))
            if response.status:
                print("Assignment graded successfully.")
            else:
                print("Failed to grade assignment.")
        else:
            print("Failed to retrieve students.")
    else:
        print("Failed to retrieve assignments.")


def answer_doubts(stub):
    # Fetch unanswered doubts
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_doubts", optional_data="unanswered"))
    if response.status and response.data:
        print("\nUnanswered Doubts:")
        for idx, doubt in enumerate(response.data):
            print(f" {doubt}")

        doubt_index = input("Enter the doubt index to answer: ")
        answer = input("Enter your answer: ")

        # Send the answer to the server
        response = stub.Post(lms_pb2.PostRequest(token=token, type="answer_doubt", data=f"{doubt_index},{answer}"))
        if response.status:
            print("Doubt answered successfully!")
        else:
            print("Failed to answer doubt.")
    else:
        print("Failed to retrieve doubts or no unanswered doubts available.")


def logout(stub):
    response = stub.Logout(lms_pb2.LogoutRequest(token=token))
    if response.status:
        print("Logged out successfully!")
    else:
        print("Failed to log out.")

def main():
    channel = grpc.insecure_channel('localhost:50051')
    stub = lms_pb2_grpc.LMSStub(channel)

    while True:
        print("\n--- Main Menu ---")
        print("1. Register")
        print("2. Login")
        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            response = stub.RegisterStudent(lms_pb2.RegisterRequest(username=username, password=password))
            if response.status:
                print("Registration successful!")
            else:
                print(f"Registration failed: {response.message}")
        elif choice == '2':
            global token
            username = input("Enter username: ")
            password = input("Enter password: ")
            response = stub.Login(lms_pb2.LoginRequest(username=username, password=password))
            if response.status:
                token = response.token
                print("Login successful!")
                if username == "teacher":
                    teacher_menu(stub)
                else:
                    student_menu(stub)
            else:
                print(f"Login failed: {response.message}")
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()