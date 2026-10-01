# Hugging Face Flashcard Generator

## Objective

This project uses the Hugging Face Inference API to generate five study flashcards for any topic. The goal is to compare two text-generation models and observe how the output changes while keeping the prompt, system instructions, temperature, and formatting the same.

## Requirements

- Python 3.10+
- VS Code
- Hugging Face account
- Hugging Face access token

## Project Structure

```text
huggingface_flashcards/
├── app.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── README.md
└── .venv/   # created locally during setup
```

## Installation

Open PowerShell in the project folder and run:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, use the safe command below for the current user/session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Then continue with:

```powershell
pip install -r requirements.txt
```

## Environment Setup

Create a local `.env` file in the project folder. Do not add a real token to GitHub, screenshots, chats, or shared files.

Use this exact content:

```env
HF_TOKEN=your_token_here
```

The `.env.example` file contains the same placeholder value:

```env
HF_TOKEN=your_token_here
```

Important: Do not upload your HF_TOKEN to GitHub, screenshots, chats, or shared files.

## Create a Hugging Face token

1. Sign in to Hugging Face.
2. Open your account settings.
3. Go to Access Tokens.
4. Create a new token.
5. Copy it into your local `.env` file.
6. Keep it only on your machine.

Do not print the token or paste it in code comments.

## Run

```powershell
python app.py
```

## Example Topic

```text
Machine Learning
```

## Model 1

The project uses the first model ID in `app.py`:

```python
MODEL_1 = "openai/gpt-oss-120b"
```

Run the app as-is to test Model 1. It will ask for a topic and generate five flashcards.

## Model 2

To compare a second model, change only the model value:

```python
# ==================================================
# CHANGE ONLY THIS VALUE FOR MODEL COMPARISON
# ==================================================
MODEL_ID = MODEL_1
```

Replace it with:

```python
MODEL_ID = MODEL_2
```

Keep the prompt, system instruction, temperature, max tokens, and formatting the same. Only the model ID changes.

## Latency Measurement

The application measures time using `time.perf_counter()`. It records the start time before the API request and the end time after the response is received.

```python
start_time = time.perf_counter()
# API request here
end_time = time.perf_counter()
latency = end_time - start_time
```

This gives a reliable elapsed time in seconds and is printed as:

```text
Response time: X.XX seconds
```

## Comparison Table

Use the table below after running both models.

| Observation | Model 1 | Model 2 |
|------------|---------|---------|
| Model ID | ... | ... |
| Response time | ... | ... |
| Tone | ... | ... |
| Answer length | ... | ... |
| Format adherence | ... | ... |
| Other observations | ... | ... |

The terminal output is kept simple so you can copy the model ID and response time values into the table.

## Quick Reflection

1. What is a Hugging Face Model ID?
   - A model ID is the name of the model on the Hugging Face Hub, such as `openai/gpt-oss-120b`.

2. What does InferenceClient do?
   - It sends requests to a Hugging Face hosted inference endpoint and returns the model output.

3. What changed when you switched models?
   - The model ID changed, so the response quality, tone, and wording often changed.

4. What stayed the same?
   - The topic, prompt, system instruction, temperature, output format, and flashcard structure stayed the same.

5. What did you observe about token usage and latency?
   - Larger or more complex models may take longer and use more tokens, while smaller models can respond faster.

## Troubleshooting

### HF_TOKEN missing

- Make sure a local `.env` file exists.
- The file should contain:

```env
HF_TOKEN=your_token_here
```

- Restart the app after saving the file.

### Invalid token

- Check that the token is copied correctly.
- Confirm the token is active in your Hugging Face account.
- Generate a new token if needed.

### Model unavailable

- Check the model ID in `app.py`.
- Make sure the model is currently supported by Hugging Face Inference Providers.
- Try another valid model if the selected one is not available.

### Provider unavailable

- Retry the request later.
- Check your network connection.
- Try a different model or provider if needed.

### Network error

- Ensure you are connected to the internet.
- Confirm your VPN or firewall is not blocking Hugging Face.

### PowerShell virtual environment activation error

- Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Package not installed

- Run:

```powershell
pip install -r requirements.txt
```

---

## Security Reminder

Do not upload your HF_TOKEN to GitHub, screenshots, chats, or shared files.

The token should stay only in your local `.env` file.
