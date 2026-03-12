# JoinProject

This project is a web application made with **Django** tries to make a web centralizing streaming platforms for users to look at different content without having to change platform.

## How to start the project with Docker

The project is fully containerized. You just need to have **Docker** and **Docker Compose** installed on your machine.

### 1. Initial preparation
Clone the repository and create the environment variable file:
```bash
git clone <URL_OF_THE_REPOSITORY>
cd <PROJECT_NAME>

# Create the file .env
gedit .env
# Or copy it from yours that already exists
cp /your_directory/.env .env
```
### 2. Start the website
```bash
docker compose up
```
This web is running on **127.0.0.1:8000**


At this moment the web is running in an open server [URL of the web](https://joinproject-23y7.onrender.com)