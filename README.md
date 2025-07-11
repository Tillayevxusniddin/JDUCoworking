# JDU Coworking System API

<p align="center">
  <img src="https://i.imgur.com/your-logo-image-url.png" alt="Project Logo" width="150"/>
</p>

<p align="center">
  A comprehensive backend system designed for the <b>Digital University Coworking System</b>. This API manages student activities, project collaboration, task assignments, reporting, and payroll, providing a robust foundation for the coworking platform.
</p>

<p align="center">
  <a href="https://github.com/Tillayevxusniddin/JDUCoworking/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Tillayevxusniddin/JDUCoworking?style=for-the-badge" alt="License">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python" alt="Python Version">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Django-5.2-green?style=for-the-badge&logo=django" alt="Django Version">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/Docker-Ready-blueviolet?style=for-the-badge&logo=docker" alt="Docker Ready">
  </a>
</p>

---

## ✨ Key Features

* **👥 User Management:** Multi-role system (`STUDENT`, `STAFF`, `TEAMLEADER`, `RECRUITER`, `ADMIN`) with dedicated user profiles.
* **🔐 Secure Authentication:** Robust authentication using `Simple-JWT` with `access` and `refresh` tokens.
* **🏢 Workspace Collaboration:** Dedicated workspaces for projects with a complete membership management system.
* **💼 Jobs & Vacancies:** A full-cycle system for creating projects (`Jobs`), posting vacancies, and handling student applications.
* **📋 Task Management:** Create, assign, and comment on tasks within project workspaces.
* **📊 Automated Reporting & Payroll:** Daily reports, automatic monthly report generation (in Excel), and salary calculation.
* **📹 Meeting Integration:** Seamless integration with `Google Calendar API` to schedule meetings and invite attendees.
* **🔔 Notification System:** Real-time notifications for all important events within the system.
* **📄 API Documentation:** Auto-generated, interactive API documentation using `drf-spectacular` (Swagger UI).

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Backend** | Python, Django, Django Rest Framework |
| **Database** | PostgreSQL |
| **Authentication** | JWT (Django Rest Framework Simple JWT) |
| **Scheduled Tasks** | APScheduler |
| **Containerization** | Docker, Docker Compose |
| **API Documentation** | drf-spectacular (Swagger UI) |

---

## 🚀 Getting Started

You can get the project up and running in two ways. The **Docker** method is highly recommended for a quick and consistent setup.

### 1. Running with Docker (Recommended)

This is the easiest and most reliable way to start the project.

#### **Prerequisites**
> * [Docker](https://www.docker.com/products/docker-desktop/) must be installed on your machine.

#### **Step-by-Step Guide**

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Tillayevxusniddin/JDUCoworking.git](https://github.com/Tillayevxusniddin/JDUCoworking.git)
    cd JDUCoworking
    ```

2.  **Create the environment file:**
    Copy the example environment file `.env.example` to a new file named `.env`.
    ```bash
    cp .env.example .env
    ```
    > **Important:** Open the `.env` file and update the variables, especially `SECRET_KEY` and `DB_PASSWORD`.

3.  **Build and Run the Containers:**
    This command will build the Docker images and start the Django (`web`) and PostgreSQL (`db`) services.
    ```bash
    docker-compose up --build
    ```
    > Wait for the logs to indicate that the database is ready and the Django server has started.

4.  **Set up the Database (First Time Only):**
    > Open a **new terminal window** (leave the previous one running).

    * Run the database migrations:
        ```bash
        docker-compose exec web python manage.py migrate
        ```
    * Create a superuser to access the admin panel:
        ```bash
        docker-compose exec web python manage.py createsuperuser
        ```

5.  **You're all set!**
    The application is now running.
    * **API Server:** [http://localhost:8000/](http://localhost:8000/)
    * **API Documentation (Swagger UI):** [http://localhost:8000/docs/](http://localhost:8000/docs/)

---

### 2. Manual Local Setup (Without Docker)

#### **Prerequisites**
> * Python 3.10+
> * PostgreSQL

#### **Step-by-Step Guide**

1.  **Clone the repository and create a virtual environment:**
    ```bash
    git clone [https://github.com/Tillayevxusniddin/JDUCoworking.git](https://github.com/Tillayevxusniddin/JDUCoworking.git)
    cd JDUCoworking
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up the database:**
    Create a new PostgreSQL database manually (e.g., `coworking`).

4.  **Configure environment variables:**
    Create a `.env` file. For a local setup, `DB_HOST` must be `localhost`.
    ```dotenv
    # .env
    SECRET_KEY=your-strong-secret-key
    DEBUG=True
    DB_NAME=coworking
    DB_USER=your_postgres_user
    DB_PASSWORD=your_postgres_password
    DB_HOST=localhost
    DB_PORT=5432
    ```

5.  **Run migrations and create a superuser:**
    ```bash
    python manage.py migrate
    python manage.py createsuperuser
    ```

6.  **Start the development server:**
    ```bash
    python manage.py runserver
    ```
    The application will be available at `http://localhost:8000/`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Tillayevxusniddin/JDUCoworking/blob/main/LICENSE) file for details.

---

## 📬 Contact

Xusniddin Tillayev - [tillayevx1@gmail.com](mailto:tillayevx1@gmail.com)

Project Link: [https://github.com/Tillayevxusniddin/JDUCoworking](https://github.com/Tillayevxusniddin/JDUCoworking)
