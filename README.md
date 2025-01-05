# Backend API Documentation

This document provides the necessary details for integrating the backend API with your React frontend application.
The base URL for the deployed API is:

```
https://crm-backend-b0bv.onrender.com/api/
```

## Authentication
- **Admin-only endpoints require JWT tokens** for authentication.
- For endpoints requiring a token, include the following header:
  ```
  Authorization: Bearer <JWT_TOKEN>
  ```

## Endpoints Overview

### 1. **Projects**
#### **Get All Projects (Admin Only)**
- **URL:** `GET /projects/`
- **Headers:** Requires authentication.
- **Response Example:**
  ```json
  [
    {
      "id": 1,
      "title": "New CRM System",
      "description": "A CRM system to manage customer relations.",
      "budget": "5000.00",
      "deadline": "2025-02-01",
      "sender_name": "John Doe",
      "contact_email": "john@example.com",
      "category": 1,
      "status": "NEW",
      "created_at": "2025-01-05T12:00:00Z",
      "updated_at": "2025-01-05T12:00:00Z",
      "attachments": [],
      "comments": []
    }
  ]
  ```

#### **Create a New Project (Public Access)**
- **URL:** `POST /projects/`
- **Body:**
  ```json
  {
    "title": "New CRM System",
    "description": "A CRM system to manage customer relations.",
    "budget": 5000,
    "deadline": "2025-02-01",
    "sender_name": "John Doe",
    "contact_email": "john@example.com",
    "category": 1
  }
  ```
- **Response Example:**
  ```json
  {
    "id": 1,
    "title": "New CRM System",
    "description": "A CRM system to manage customer relations.",
    "budget": "5000.00",
    "deadline": "2025-02-01",
    "sender_name": "John Doe",
    "contact_email": "john@example.com",
    "category": 1,
    "status": "NEW",
    "created_at": "2025-01-05T12:00:00Z",
    "updated_at": "2025-01-05T12:00:00Z",
    "attachments": [],
    "comments": []
  }
  ```

#### **Accept or Reject a Project (Admin Only)**
- **URL to Accept:** `POST /projects/{id}/accept/`
- **URL to Reject:** `POST /projects/{id}/reject/`
- **Headers:** Requires authentication.
- **Response Example:**
  ```json
  {
    "detail": "Project accepted",
    "status": "ACCEPTED"
  }
  ```

### 2. **Attachments**
#### **Upload an Attachment (Public Access)**
- **URL:** `POST /attachments/`
- **Body (form-data):**
  - **file:** (Choose a file to upload)
  - **project:** (Project ID for the attachment)
- **Response Example:**
  ```json
  {
    "id": 1,
    "file": "http://127.0.0.1:8000/media/attachments/sample_file.pdf",
    "uploaded_at": "2025-01-05T12:05:00Z",
    "project": 1
  }
  ```

#### **Download an Attachment (Admin Only)**
- **URL:** `GET /attachments/{id}/download/`
- **Headers:** Requires authentication.
- **Behavior:** Downloads the file.

### 3. **Comments**
#### **Create a Comment (Admin Only)**
- **URL:** `POST /comments/`
- **Body:**
  ```json
  {
    "project": 1,
    "comment_text": "This is a comment."
  }
  ```
- **Response Example:**
  ```json
  {
    "id": 1,
    "project": 1,
    "comment_text": "This is a comment.",
    "author_name": "Admin",
    "created_at": "2025-01-05T12:10:00Z"
  }
  ```

### 4. **Categories**
#### **Get All Categories**
- **URL:** `GET /categories/`
- **Response Example:**
  ```json
  [
    {
      "id": 1,
      "name": "Web Development"
    },
    {
      "id": 2,
      "name": "Mobile Development"
    },
    {
      "id": 3,
      "name": "Data Science"
    }
  ]
  ```

