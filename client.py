import grpc
import lms_pb2
import lms_pb2_grpc
import os
import json

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

def add_assignment(stub):
    assignment_id = input("Enter Assignment ID: ")
    assignment_name = input("Enter Assignment Name: ")
    response = stub.Post(lms_pb2.PostRequest(type="add_assignment", data=f"{assignment_id},{assignment_name}"))
    if response.status:
        print("Assignment added successfully.")
    else:
        print("Failed to add assignment.")

def view_assignments(stub):
    response = stub.Get(lms_pb2.GetRequest(token=token, type="view_assignments"))
    if response.status:
        print("Assignments: ", response.data)
    else:
        print("Failed to retrieve assignments.")

def submit_assignment(stub):
    assignment_id = input("Enter Assignment ID: ")
    file_path = input("Enter file path: ")
    response = stub.Post(lms_pb2.PostRequest(type="submit_assignment", data=f"{assignment_id},{file_path}", token=token))
    if response.status:
        print("Assignment submitted successfully.")
    else:
        print("Failed to submit assignment.")

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
                role = input("Enter role (student/teacher): ")
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
