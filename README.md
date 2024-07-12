# News-to-Video Automation Script

This Python script automates the process of creating videos from news articles, incorporating AI-generated images, subtitles, and synthesized audio to produce engaging multimedia content.

## Features

- **Keyword Extraction**: Extracts key phrases from news articles using ChatGPT.
- **AI Image Generation**: Generates relevant images for each keyword using DALL-E.
- **Subtitle Creation**: Splits the article into manageable parts for subtitles based on its length.
- **Audio Synthesis**: Utilizes ElevenLabs API to create natural-sounding voiceovers timed with subtitles.

## Getting Started

### Prerequisites

Before running the script, make sure you have Python installed on your system. Then, install the following packages:

```bash
pip install openai moviepy instabot python-dotenv gtts
