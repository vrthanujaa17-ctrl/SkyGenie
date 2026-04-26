✈️ SkyGenie – Smart Flight Search & Travel Assistant

 📌 Overview

SkyGenie is a web-based flight search application that allows users to compare flight options across multiple airlines and receive AI-powered travel assistance. The platform integrates real-time flight data, intelligent filtering, and a conversational chatbot to enhance the travel planning experience.



🚀 Features

 🔍 Flight Search

* Search for **one-way and round-trip flights**
* Compare flights based on:

  * Price
  * Duration
  * Stops
  * Layover time

🤖 AI Travel Assistant

* Chatbot powered by **Google Gemini API**
* Provides:

  * Travel itineraries
  * Destination suggestions
  * Budget & transport tips

🌍 Destination Preview

* Visual previews of selected destinations
* Improves user experience and engagement

### ⚙️ Smart Filtering & Sorting

* Max price filter
* Max stops & layover filters
* Sorting by price or duration

### 🛠️ Robust System Design

* Handles API failures gracefully using **fallback mock data**
* Ensures uninterrupted user experience

---

## 🏗️ Architecture

The system follows a **Client-Server + Layered Architecture**:

* **Frontend**: React (UI, user interaction)
* **Backend**: Flask (API handling, business logic)
* **API Layer**: Handles communication between frontend and backend
* **External APIs**:

  * SkyScanner Rapid API (flight data)
  * Google Gemini API (chatbot)

---

## 🧰 Tech Stack

| Layer    | Technology                          |
| -------- | ----------------------------------- |
| Frontend | React, JavaScript, HTML, CSS        |
| Backend  | Python (Flask)                      |
| APIs     | SkyScanner Rapid API, Google Gemini |
| Tools    | VS Code, Git, GitHub                |

---

## 📂 Project Structure

```bash
Flight_Cost_Finder/
│
├── frontend/        # React frontend
├── backend/         # Flask backend
├── .venv/           # Virtual environment
├── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/Flight_Cost_Finder.git
cd Flight_Cost_Finder
```

---

### 2️⃣ Backend Setup

```bash
cd backend
source ../.venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

### 3️⃣ Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

---

### 4️⃣ Open Application

```text
http://localhost:5173
```

---

## 🔐 Environment Variables

Create a `.env` file inside `backend/`:

```env
GEMINI_API_KEY=your_gemini_api_key
SKYSCANNER_API_KEY=your_rapidapi_key
SKYSCANNER_API_HOST=flights-sky.p.rapidapi.com
```

---

## ⚠️ Notes

* Flight API may have **rate limits or restrictions**
* Mock data is used as a fallback when API fails
* Round-trip API requires correct **entity IDs**

---

## 🚧 Challenges

* Limited availability of free real-time flight APIs
* Handling API rate limits and failures
* Integrating AI chatbot with frontend and backend

---

## 🔮 Future Improvements

* Flight booking integration
* User authentication & saved trips
* Personalized recommendations
* Voice assistant integration
* Improved chatbot UI (cards, maps)

---

## 👥 Team

* Thanujaa Vudayagiri Ravindra Babu
* Shree Jhagen
* Shreyanka Saggidi

---

## 🙌 Acknowledgements

* SkyScanner Rapid API
* Google Gemini API

---

## 📌 Conclusion

SkyGenie demonstrates a scalable and user-friendly approach to flight search by combining real-time data, intelligent filtering, and AI-powered assistance, providing a seamless travel planning experience.
