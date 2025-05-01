<p align="center">
  <img src="static/mailmatrix-logo.png" width="300" alt="MailMatrix Logo">
</p>

# 📬 MailMatrix

MailMatrix is a cloud-native serverless web application to automate bulk email notifications using AWS services like Lambda, SES, S3, EventBridge, and CloudWatch. It features a Flask frontend for user registration, login, and file uploads.

---

## 🌟 Features
- Register/Login System (Flask + SQLite)
- Upload recipient CSVs and offer letter PDFs
- Send conditional offer/rejection emails using SES
- Uses AWS Lambda + EventBridge for automation
- Tracks upload and email history per user

---

## 💻 Tech Stack

| Frontend | Backend | Cloud | DB |
|----------|---------|--------|----|
| HTML/CSS | Python, Flask | AWS (Lambda, SES, S3, EventBridge, Aurora and RDS, IAM, CloudWatch) | MySQL |

---

## 📁 Project Structure
MailMatrix/ ├── app.py ├── controllers/ ├── static/ │ ├── css/ │ └── images/ ├── templates/ │ ├── login.html │ ├── register.html │ ├── home.html │ ├── profile.html │ └── history.html ├── lambda/ │ └── email_handler.py ├── assets/ │ └── logo.png └── README.md


---

## 🔧 Step-by-Step Implementation

### 1️⃣ Set Up AWS Resources
- Create an **S3 Bucket** (e.g., `mailmatrix-uploads`)
- Create an **IAM Role** for Lambda:
- Permissions: S3 Read, SES SendEmail, CloudWatch Logs
- Enable **Amazon SES** (Sandbox or Production)
- Create verified identities (emails)

### 2️⃣ Deploy Lambda Function
- Navigate to AWS Lambda → Create Function
- Choose: Author from scratch
- Runtime: Python 3.9+
- Upload or paste `email_handler.py`
- Set environment variables:
  - `SENDER_EMAIL`, `BUCKET_NAME`
- Set trigger: **S3 PUT Object** on the bucket

### 3️⃣ Configure Flask App (Local UI)
- Clone the repo
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  
### 4️⃣ Upload Offer Letter + Recipient CSV
- Upload recipients.csv (sample provided in /sample-data)
- Upload the offer letter (PDF)

### 5️⃣ Lambda Execution
- Once the CSV is uploaded, Lambda is triggered
- For each row:
- If status = selected: Send offer letter as attachment
- If status = rejected: Send rejection email (no attachment)
- Emails are sent using Amazon SES

### 6️⃣ Track History
- Login → Go to History page
- View past uploads and email actions taken

## 📦 Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ganeshbrahma/MailMatrix.git
   cd MailMatrix

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt


## 👥 Contributors

Thanks to these awesome people:

<table>
  <tr>
    <td align="center"><a href="https://github.com/ganeshbrahma"><img src="https://avatars.githubusercontent.com/u/ganeshbrahma?v=4" width="100px;" alt=""/><br /> <sub> <b> ganesh brahma </b> </sub> </a> </td>
  </tr>
</table>

