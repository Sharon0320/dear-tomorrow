# Weekend Creative Agent Challenge: Dear Tomorrow

#agents

### Architecture Preview
<img width="1632" height="809" alt="제목 없는 다이어그램 drawio" src="https://github.com/user-attachments/assets/c5025611-5d3d-4749-95a5-8b7314628a01" />


## 🌅 Vision

**Dear Tomorrow** was created from a simple idea:

**What if we could send a message to the person we are going to become?**

There are many moments when we want to say something to our future selves.

Maybe we want to encourage ourselves after going through a difficult time.
Maybe we want to celebrate a future milestone, such as graduation.
Maybe we simply want to imagine who we will become and leave a message for that future version of ourselves.

Dear Tomorrow turns those thoughts into a real experience.

Users write a message today, choose a date and time in the future, and send it to their future selves or someone they care about. When the chosen moment arrives, the message is delivered by email.

With the help of Amazon Bedrock, the original message can also be transformed into a warmer, third-person message—as if someone who has been watching over the journey is speaking directly to the future recipient.

### 💭 Why I Built It

The main motivation behind this project was to create a small but meaningful way to encourage ourselves across time.

A time capsule can be used to:

* encourage yourself when you are going through a difficult period
* celebrate a future achievement such as graduation
* congratulate your future self
* remind yourself of the goals and dreams you have today
* imagine your future life and leave a message for that version of yourself
* send a meaningful message to someone you want to remember

The goal is not simply to store a message.

It is to create a moment in the future when someone opens their inbox and unexpectedly receives a message from the person they used to be.


---

## ✨ How It Works

```text
                    ┌─────────────────────────┐
                    │        User             │
                    │                         │
                    │  Write a time capsule   │
                    │  Choose delivery time   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     CloudFront + S3      │
                    │     Static Website       │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │       API Gateway        │
                    │      POST /capsules      │
                    └────────────┬────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │         Create Capsule Lambda       │
              │                                     │
              │  Validate input                     │
              │  Validate future delivery time      │
              │  Generate capsule ID                │
              └───────────────┬─────────────────────┘
                              │
                              ▼
                    ┌─────────────────────────┐
                    │      Amazon Bedrock     │
                    │      Nova Micro         │
                    │                         │
                    │  AI message rewriting   │
                    │  Third-person style     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │        DynamoDB         │
                    │                         │
                    │  original_message       │
                    │  AI-generated message   │
                    │  recipient              │
                    │  send_date              │
                    │  status                 │
                    └────────────┬────────────┘
                                 │
                          Scheduled time
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    Send Lambda          │
                    │                         │
                    │  Find pending capsules  │
                    │  Send scheduled email   │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │      Amazon SES         │
                    │                         │
                    │   Email delivery        │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Future Recipient    │
                    │                         │
                    │   "Your message from   │
                    │      the past..."      │
                    └─────────────────────────┘
```

---

## 🤖 AI Agent Behavior

The core AI feature uses **Amazon Bedrock** to transform the user's original text.

For example, a user might write:

> "Today was really difficult. I kept going anyway. I hope future me is happier when I read this."

The AI transforms the message into a more natural and emotional third-person message while preserving the original meaning.

The prompt is designed to:

* preserve the original meaning and emotions
* avoid inventing specific events or facts
* speak to the future recipient naturally
* expand the message when appropriate
* avoid repetitive or overly dramatic expressions
* produce a complete, personal message

The application keeps both versions:

```text
original_message
        +
AI-generated message
```

This prevents the AI from permanently replacing the user's original writing.

Amazon Bedrock's Converse API provides a unified interface for supported models, which made it a good fit for integrating the AI generation step into the Lambda workflow.

---

## 🛠️ How We Built It

### 1. Started with a serverless architecture

The project was designed around AWS managed services instead of maintaining a traditional backend server.

The initial flow was:

```text
Frontend
   ↓
API Gateway
   ↓
Lambda
   ↓
DynamoDB
```

This kept the architecture lightweight and suitable for a small personal project.

### 2. Added AI message transformation

Amazon Bedrock was integrated into the capsule creation Lambda.

The Lambda now:

1. receives the user's message
2. validates the delivery date
3. sends the message to Bedrock
4. receives the AI-generated version
5. stores both the original and transformed messages in DynamoDB

The Bedrock Runtime Converse API is specifically designed to provide a consistent model interface and supports system prompts and inference configuration.

### 3. Added scheduled delivery

A separate Lambda periodically scans DynamoDB for capsules that have:

```text
send_date <= current_time
status = pending
```

When a capsule is ready, the function sends an HTML email through Amazon SES and updates the DynamoDB item to:

```text
status = sent
```

### 4. Built the email experience

The delivery Lambda generates an HTML email instead of sending plain text.

The email includes:

* Time Capsule branding
* subject
* AI-generated message
* creation date
* scheduled date
* delivery timestamp

### 5. Added custom domain support

The web application is deployed through CloudFront and S3.

A custom domain was also configured:

```text
dear-tomorrow.kro.kr
```

with an AWS Certificate Manager certificate for HTTPS.

### 6. Email authentication

Amazon SES was configured in the Sydney region using:

```text
dear-tomorrow.kro.kr
```

as the sending domain.

Easy DKIM and DMARC records were configured to establish domain authentication.

The final production email flow depends on completing the SES domain/DKIM DNS verification and account sending configuration.

---

## ☁️ AWS Services Used

| AWS Service                 | Purpose                                                     |
| --------------------------- | ----------------------------------------------------------- |
| **Amazon S3**               | Hosts the static frontend and stores application assets     |
| **Amazon CloudFront**       | Global CDN and HTTPS delivery for the website               |
| **Amazon API Gateway**      | HTTP API endpoint for capsule creation                      |
| **AWS Lambda**              | Serverless application logic                                |
| **Amazon DynamoDB**         | Stores time capsules and their delivery state               |
| **Amazon Bedrock**          | AI-powered message transformation                           |
| **Amazon SES**              | Scheduled email delivery                                    |
| **AWS Certificate Manager** | HTTPS certificate for the custom domain                     |
| **Route 53**                | Hosted zone/DNS experimentation during domain configuration |

Amazon Bedrock's runtime APIs are available through the `bedrock-runtime` endpoint, with Converse providing a unified interface for supported models.

---

## 🏗️ Architecture Overview

<img width="1632" height="809" alt="제목 없는 다이어그램 drawio" src="https://github.com/user-attachments/assets/01a5514c-d6cb-4d03-945c-6d08ca1d02dd" />


```text
                         INTERNET
                            │
                            ▼
                ┌──────────────────────┐
                │   Custom Domain      │
                │ dear-tomorrow.kro.kr │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │     CloudFront       │
                │      HTTPS/CDN       │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │      S3 Bucket       │
                │   Static Frontend    │
                └──────────────────────┘


User creates capsule
        │
        ▼
┌───────────────────┐
│   API Gateway     │
└─────────┬─────────┘
          │
          ▼
┌────────────────────────────┐
│ Create Capsule Lambda      │
│                            │
│ - Validation               │
│ - UUID generation          │
│ - Bedrock invocation       │
│ - DynamoDB write           │
└───────────┬────────────────┘
            │
            ├──────────────────────┐
            │                      │
            ▼                      ▼
┌─────────────────────┐   ┌─────────────────────┐
│   Amazon Bedrock    │   │      DynamoDB       │
│                     │   │                     │
│ Nova Micro          │   │ Original message    │
│ Message rewriting   │   │ AI message          │
└─────────────────────┘   │ Delivery timestamp  │
                          │ Status              │
                          └──────────┬──────────┘
                                     │
                                     │ Scheduled time
                                     ▼
                          ┌─────────────────────┐
                          │   Send Lambda       │
                          │                     │
                          │ Find pending items  │
                          │ Send email          │
                          │ Update status       │
                          └──────────┬──────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │     Amazon SES      │
                          │                     │
                          │   Email delivery    │
                          └─────────────────────┘
```

---

## 🧩 DynamoDB Data Model

Each time capsule is stored approximately as:

```json
{
  "capsule_id": "uuid",
  "recipient_email": "user@example.com",
  "subject": "A message from the past",
  "original_message": "The user's original text",
  "message": "AI-generated message",
  "send_date": "2026-12-31T12:00:00+00:00",
  "timezone": "UTC",
  "created_at": "2026-08-23T00:00:00+00:00",
  "status": "pending",
  "attachment_url": null
}
```

Keeping `original_message` separately from `message` was an important design decision because AI should enhance the user's writing without destroying the original content.

---

## 🚧 Challenges

### DNS and Custom Domains

One of the most challenging parts was connecting a custom domain registered through a third-party Korean domain provider to AWS services.

The project required:

```text
Domain registration
       ↓
DNS configuration
       ↓
ACM certificate validation
       ↓
CloudFront custom domain
       ↓
HTTPS
```

DNS management limitations from the domain provider required experimenting with Route 53, ACM DNS validation, and direct DNS records.

### SES Verification

Another challenge was setting up Amazon SES for production email delivery.

SES requires proper identity verification and domain authentication, including DKIM DNS records. Understanding the difference between:

```text
domain ownership
DKIM
DMARC
SES sandbox
production access
```

was an important part of the deployment process.

### AI Output Quality

The first AI-generated messages were sometimes too creative and introduced facts that the user never mentioned.

For example, a simple statement like:

> "Today was difficult."

could cause the model to invent reasons such as illness or personal problems.

The prompt was therefore refined to explicitly prevent:

* invented events
* invented people
* invented memories
* unsupported assumptions

This made the AI behave more like a thoughtful editor than a free-form storyteller.

---

## 📚 What I Learned

This project taught me how to connect multiple AWS services into a complete serverless application rather than treating each service independently.

The biggest lessons were:

**1. Serverless architecture can still require significant system design.**

Lambda, DynamoDB, API Gateway, S3, CloudFront, Bedrock, and SES are individually simple, but connecting them correctly requires careful decisions about permissions, regions, data flow, and failure handling.

**2. DNS is often harder than application code.**

The actual application logic was relatively straightforward compared with custom-domain, certificate, and DNS configuration.

**3. AI needs constraints.**

A good prompt is not only about telling a model what to do. It is equally important to tell it what it must not invent.

**4. Preserve user data before transforming it.**

AI-generated output should not overwrite the original user content. Keeping both versions provides a safer and more flexible architecture.

**5. AWS regions matter.**

Different AWS services and identities are often region-specific. Lambda, Bedrock, and SES therefore need to be configured with their regional behavior in mind.

**6. Small projects can become real distributed systems.**

Even a simple "send a message to the future" application involves:

```text
Frontend
+
API
+
Compute
+
Database
+
AI
+
Scheduling
+
Email
+
Authentication
+
DNS
+
HTTPS
```

That made this project a valuable hands-on experience with cloud architecture.

---

## 🚀 Current Status

### Completed

* [x] Static frontend
* [x] S3 hosting
* [x] CloudFront deployment
* [x] API Gateway integration
* [x] Capsule creation Lambda
* [x] DynamoDB storage
* [x] Amazon Bedrock integration
* [x] AI message rewriting
* [x] Original + AI message storage
* [x] Scheduled delivery Lambda
* [x] HTML email template
* [x] ACM HTTPS certificate
* [x] Custom domain configuration
* [x] SES domain identity configuration
* [x] DKIM and DMARC configuration work

### In Progress

* [ ] Final SES DNS verification
* [ ] SES production access
* [ ] Final end-to-end production email test
* [ ] AI message preview before saving
* [ ] Attachment upload integration
* [ ] Improved scheduling/query strategy

---

## 🌐 App

**Live application:**

https://d3lmmoix9rftvv.cloudfront.net/

Custom domain:

`https://dear-tomorrow.kro.kr/`

---

## 📂 Project Structure

A simplified project structure:

```text
dear-tomorrow/
│
├── frontend/
│   └── index.html
│
├── lambda/
│   ├── create_capsule.py
│   └── send_capsules.py
│
└── README.md
```

---

## 🎯 Future Improvements

The next version of Dear Tomorrow could include:

* AI preview before saving a capsule
* Multiple AI writing styles
* User accounts and authentication
* Better delivery scheduling with EventBridge
* Secure attachment uploads through S3
* Capsule history
* Retry handling and dead-letter queues
* Email delivery analytics
* Improved DynamoDB indexing instead of table scans
* Stronger content moderation and prompt safety
* Mobile-first UI

---

## Built With

**AWS · Amazon Bedrock · Lambda · DynamoDB · S3 · CloudFront · API Gateway · SES · ACM · Python · JavaScript**

---

## #agents

This project was built for the **Weekend Creative Agent Challenge** as an exploration of how AI can transform a simple cloud application into a more personal and meaningful user experience.
