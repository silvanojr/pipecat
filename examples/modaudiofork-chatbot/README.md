# mod_audio_fork Chatbot

This project is a FastAPI-based chatbot that integrates with FreeSwitch via mod_audio_fork to handle WebSocket connections and provide real-time communication. The project includes endpoints for handling WebSocket connections.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configure Twilio URLs](#configure-twilio-urls)
- [Running the Application](#running-the-application)
- [Usage](#usage)

## Features

- **FastAPI**: A modern, fast (high-performance), web framework for building APIs with Python 3.6+.
- **WebSocket Support**: Real-time communication using WebSockets.
- **CORS Middleware**: Allowing cross-origin requests for testing.
- **Dockerized**: Easily deployable using Docker.

## Requirements

- Python 3.10
- Docker (for containerized deployment)
- ngrok (for tunneling)
- FreeSwitch with the latest version of mod_audio_fork for bidirectional audio streaming

## Installation

1. **Set up a virtual environment** (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Create .env**:
    create .env based on env.example

4. **Install ngrok**:
    Follow the instructions on the [ngrok website](https://ngrok.com/download) to download and install ngrok.

## Running the Application

### Using Python

1. **Run the FastAPI application**:
    ```sh
    python server.py
    ```

2. **Start ngrok**:
    In a new terminal, start ngrok to tunnel the local server:
    ```sh
    ngrok http 8765
    ```
### Using Docker

1. **Build the Docker image**:
    ```sh
    docker build -t modaudiofork-chatbot .
    ```

2. **Run the Docker container**:
    ```sh
    docker run -it --rm -p 8765:8765 modaudiofork-chatbot
    ```
## Usage

To start a call, simply make a call to your Twilio phone number. The webhook URL will direct the call to your FastAPI application, which will handle it accordingly.
