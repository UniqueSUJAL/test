import sqlite3
import streamlit as st
import google.generativeai as genai

# Set up your API key
api_key = "AIzaSyAPJK8mjGNw08IwLvoyxY2NrLO1HbFISK0"  # Replace with your actual API key
genai.configure(api_key=api_key)

# Database connection function
def get_db_connection():
    return sqlite3.connect('question_builder_testing.db')

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Drop the table if it exists to recreate it without the 'options' column
    # cursor.execute("DROP TABLE IF EXISTS questions1")
    
    # Create a new table without 'options' column
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS questions1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            description TEXT,
            question_type TEXT,
            difficulty_level TEXT,
            subject TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_question(question, description, question_type, difficulty_level, subject):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Convert subject to lowercase for consistent storage
    subject = subject.lower()  # Store subject as lowercase

    # Check for existing duplicate before insertion based on question and subject only
    cursor.execute(""" 
        SELECT * FROM questions1 
        WHERE question = ? AND LOWER(subject) = LOWER(?)
    """, (question, subject))

    existing_question = cursor.fetchone()  # Fetch one record

    if existing_question:
        # If the subject matches and question type and difficulty level are the same, notify user
        if (existing_question[3] == question_type) and (existing_question[4] == difficulty_level):
            print(f"Duplicate question found: {existing_question[1]} (Type: {question_type}, Level: {difficulty_level})")
        else:
            # If they are different, allow insertion
            cursor.execute(""" 
                INSERT INTO questions1 (question, description, question_type, difficulty_level, subject)
                VALUES (?, ?, ?, ?, ?)
            """, (question, description, question_type, difficulty_level, subject))
            conn.commit()
            print("Question inserted successfully, as it has a different type or difficulty level.")
    else:
        # If no duplicate is found, insert the new question
        cursor.execute(""" 
            INSERT INTO questions1 (question, description, question_type, difficulty_level, subject)
            VALUES (?, ?, ?, ?, ?)
        """, (question, description, question_type, difficulty_level, subject))
        conn.commit()
        print("Question inserted successfully.")

    conn.close()

def generate_questions(description, num_questions, question_type, difficulty_level):
    questions = []
    
    for _ in range(num_questions):
        # Constructing a detailed prompt for the AI model
        if question_type == "Multiple Choice":
            prompt = (f"Generate a unique multiple-choice question at a {difficulty_level} level based on the following description: {description}. "
                      "Provide the question and four options, without answers or explanations.")
        else:
            prompt = (f"Generate a unique {question_type} question at a {difficulty_level} level based on the following description: {description}. "
                      "Provide only the question, without answers or explanations.")
        
        model = genai.GenerativeModel("gemini-1.5-flash")  # Ensure this model exists in your library version
        response = model.generate_content(prompt)  # Adjusted method for generating content
        questions.append((response.text.strip(), ["Option A", "Option B", "Option C", "Option D"]))  # Dummy options for non-MCQ types
    
    return questions

# Streamlit UI
if __name__ == "__main__":
    create_table()   # Create the table when the app starts

    if "questions" not in st.session_state:
        st.session_state.questions = []

    st.title("Automated Question Builder Application")
    
    description = st.text_area("Enter the question description:")
    num_questions = st.number_input("Number of questions to generate:", min_value=1, max_value=100, value=1)

    # Adding options for question type, difficulty level, and subject
    question_type = st.selectbox("Select question type:", ["Multiple Choice", "Coding", "Short Answer", "Case Study"])
    difficulty_level = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"])
    subject = st.text_input("Enter the subject:")

    if st.button("Generate Questions"):
        if description:
            st.session_state.questions = generate_questions(description, num_questions, question_type, difficulty_level)
            st.subheader("Generated Questions:")
            for idx, (question, options) in enumerate(st.session_state.questions, start=1):
                st.write(f"{idx}. {question}")
                if question_type == "Multiple Choice":
                    st.write("**Options**: " + ", ".join(options))
        else:
            st.error("Please enter a description to generate questions.")

    if st.button("Save Questions"):
        if st.session_state.questions:
            for question, options in st.session_state.questions:
                insert_question(question, description, question_type, difficulty_level, subject)
                st.success(f"Question '{question}' saved to the database successfully!")
            # Clear the questions list after saving
            st.session_state.questions = []
        else:
            st.error("No questions generated to save. Please generate questions first.")
