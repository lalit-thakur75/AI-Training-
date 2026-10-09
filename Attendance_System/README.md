# AI-Powered Attendance Management System

A Python-based attendance management system that uses an AI model to understand natural-language queries and manage student attendance stored in a JSON file.

## Features

- Manage attendance for multiple students.
- Check whether a student was present on a particular date.
- Mark students present or absent.
- Remove attendance records.
- Calculate individual attendance percentages.
- Find students with the highest and lowest attendance.
- Calculate the class attendance average.
- Update attendance data in a JSON file.
- Interact with the system through the terminal.
- Validate attendance dates and student records.

## Tech Stack

- Python
- Hugging Face Inference API
- JSON
- python-dotenv
- huggingface_hub

## Project Structure

```text
Attendance_generator/
├── app.py
├── attendance.json
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Installation

Clone the repository:

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd Attendance_generator
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Environment Setup

Create a `.env` file in the project root:

```env
HF_TOKEN=your_huggingface_token_here
```

Replace the placeholder with your own Hugging Face token. Never upload `.env` or expose your API token publicly.

## Run the Application

```bash
python app.py
```

Enter attendance-related queries in the terminal and type `exit` to quit.

## Attendance Calculation

Individual attendance percentage:

`(Present Days / Total Days) * 100`

The class attendance average is calculated in Python using the individual student attendance percentages.

## Important Notes

- The application requires a valid AI provider configuration and available API access.
- AI interprets the user's request; Python should validate and perform attendance changes.
- Attendance changes should be validated before saving them to JSON.
- The included student data should be sample data only.

## Future Improvements

- Web-based dashboard
- Student and administrator authentication
- Database integration
- Attendance reports and visualizations
- Automated testing