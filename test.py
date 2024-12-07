import requests

url = "http://localhost:8000/api/v1/generate-quiz"
files = {"file": open("document.pdf", "rb")}
response = requests.post(url, files=files)
print(response.json())