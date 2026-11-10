# KiranaVoice AI 🛒🎙️

**A voice-powered AI assistant designed to simplify inventory management and everyday operations for Indian kirana stores.**

KiranaVoice AI enables shopkeepers to interact with their store management system using natural-language voice commands in Hindi, Hinglish and English.

Instead of navigating multiple screens or manually entering stock details, shopkeepers can use conversational commands to manage inventory and access store information.

## 💡 Problem Statement

Many small kirana stores in India still depend on manual processes, notebooks and traditional methods to manage inventory.

These processes can be:
- Time-consuming
- Difficult to maintain
- Prone to human errors
- Inconvenient for busy shopkeepers

KiranaVoice AI aims to make store management more accessible through voice-based interactions.

## 🚀 Key Features

- **Voice-Based Interaction:** Interact with the application using spoken commands.
- **Hindi & Hinglish Support:** Designed for natural Indian language interactions.
- **AI-Powered Command Understanding:** Interpret commands and identify the intended store operation.
- **Inventory Management:** Add and remove product stock.
- **Stock Tracking:** Check product availability and quantities.
- **Natural Language Processing:** Extract product names, quantities, units and actions from commands.
- **Store Dashboard:** View inventory and store-related information through a user-friendly interface.

## 🎙️ Example Voice Commands

| Voice command | Expected action |
|---|---|
| Maggi ke 10 packet add karo | Add 10 Maggi packets |
| 5 kilo chawal stock mein add karo | Add 5 kg rice |
| 2 packet biscuit hatao | Remove 2 biscuit packets |
| Maggi ka stock kitna hai? | Check Maggi stock |

## 🏗️ Architecture

KiranaVoice AI follows a frontend-backend architecture.

1. **Frontend:** Captures voice input and displays inventory information.
2. **Speech Recognition:** Gnani Prisma converts spoken input into text.
3. **Command Processing:** Interprets the transcript and extracts the intended action.
4. **Backend:** Processes requests and handles inventory operations.
5. **Inventory Management:** Updates or retrieves relevant stock information.
6. **Response:** Displays the operation result to the user.

## 🛠️ Technology Stack

Update this list according to the actual implementation.

- **Frontend:** React, Vite
- **Backend:** Python, FastAPI
- **Speech-to-Text:** Gnani Prisma STT
- **AI / NLP:** Existing LLM and command-processing integration
- **Development Tools:** Visual Studio Code, Git, GitHub

## 📁 Project Structure

```text
KiranaVoice-AI/
├── backend/
├── frontend/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

## ⚙️ Getting Started

### Prerequisites

- Python 3.10 or compatible project version
- Node.js and npm
- Git
- Gnani API credentials

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd KiranaVoice-AI
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment.

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file inside the backend directory.

Add your credentials:

```env
GNANI_API_KEY=your_gnani_api_key
```

Add other required variables based on `.env.example`.

**Never commit your actual API keys or `.env` file to GitHub.**

### 4. Start the backend

Use the startup command specified by the existing backend configuration.

For a FastAPI application, this may be:

```bash
uvicorn main:app --reload
```

### 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite.

## 🔐 Security

- Store API credentials in environment variables.
- Never expose secret keys in frontend code.
- Keep `.env` excluded through `.gitignore`.
- Use `.env.example` to document required configuration.

## 🧪 Testing

Run the backend and frontend tests using the commands configured in their respective project directories.

Test voice recognition, command interpretation and inventory operations independently.

## 🛣️ Future Improvements

- More robust multilingual command understanding.
- Improved Hindi and regional-language support.
- Conversational inventory analytics.
- Low-stock alerts and intelligent restocking suggestions.
- Sales insights and business analytics.
- Offline or low-connectivity support.
- Integration with WhatsApp and other store-management workflows.

## 🎯 Vision

Our vision is to make AI-powered digital tools accessible to India's small businesses by reducing operational complexity and enabling natural, voice-first interactions.

**Built with the goal of making everyday kirana store operations smarter, simpler and more accessible.**

---

## 👥 Contributors

Built by team ZENITH.
NOOR UL HUDA 
SHIVANSHU SINGH
## 📄 License

Specify your chosen open-source license before publishing.
