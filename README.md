# Expense-tracker-AI-Analysis

## Inspiration
I track my expenses in a low-code no-code tool called Quickbase and I thought there may be meaningful and interesting insights that an AI can derive as Gemini is well-versed in Data Analysis of structured data.

## What it does
When dynamically queried expense data is fed to the Gemini model, it becomes capable of answering any questions to gain insights out of it. I created a chatbot to get such insights.

## How it's built
Programming Language: Python
Generative AI Model Used: gemini-1.0-pro
Framework Used: Vertex AI SDK
Web Service Framework: Google Cloud Functions
Dataset Used: Personal Expenses tracked in Quickbase DB
Frontend: Quickbase Dashboard

A web service is created and hosted with Google Cloud Functions making use of the standalone Python code initially created to test the functionalities. It is then used with the Bot interface created using HTML/JS and hosted as a web page in Quickbase. It is embedded in the Quickbase dashboard for quick access.

## Future Work
Creating a fine-tuned model to reduce the tokens that are consumed to use while the chat conversation is made. This helped to understand how the Quickbase data be dynamically queried and analysed using Generative AI opens a lot of possibilities for many business applications created using the platform.
