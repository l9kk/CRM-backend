# CRM System API Documentation

This document describes the API endpoints for the CRM system backend. The API uses **JWT-based authentication** and serves data over RESTful endpoints.

## Base URL
All API requests should be sent to the following base URL:
```
https://your-app-name.onrender.com/api/
```

---

## Authentication

### 1. Obtain a JWT Token
**Endpoint**: `/token/`

**Method**: `POST`

**Request Body**:
```json
{
  "username": "admin",
  "password": "password"
}
```

**Response**:
```json
{
  "access": "ACCESS_TOKEN",
  "refresh": "REFRESH_TOKEN"
}
```

**Usage**:
- Use the `access` token in the `Authorization` header for all subsequent requests:
  ```
  Authorization: Bearer ACCESS_TOKEN
  ```

---

## Endpoints

### 1. Projects

#### **Get All Projects**
**Endpoint**: `/projects/`

**Method**: `GET`

**Authorization**: **Required**

**Response**:
```json
[
  {
    "id": 1,
    "title": "Project Title",
    "description": "Detailed description of the project",
    "status": "NEW",
    "created_at": "2025-01-04T10:00:00Z"
  },
  {
    "id": 2,
    "title": "Another Project",
    "description": "Another detailed description",
    "status": "ACCEPTED",
    "created_at": "2025-01-05T15:00:00Z"
  }
]
```

---

#### **Get a Single Project**
**Endpoint**: `/projects/<id>/`

**Method**: `GET`

**Authorization**: **Required**

**Response**:
```json
{
  "id": 1,
  "title": "Project Title",
  "description": "Detailed description of the project",
  "status": "NEW",
  "created_at": "2025-01-04T10:00:00Z"
}
```

---

#### **Submit a New Project**
**Endpoint**: `/projects/`

**Method**: `POST`

**Authorization**: Not required (Public endpoint)

**Request Body**:
```json
{
  "title": "New Project",
  "description": "This is a new project proposal.",
  "contact_email": "user@example.com"
}
```

**Response**:
```json
{
  "id": 3,
  "title": "New Project",
  "description": "This is a new project proposal.",
  "status": "NEW",
  "created_at": "2025-01-06T12:00:00Z"
}
```

---

### 2. Attachments

#### **Upload an Attachment**
**Endpoint**: `/attachments/`

**Method**: `POST`

**Authorization**: **Required**

**Request Body**:
- Use `multipart/form-data` to upload files:
  - `file`: The file to upload (e.g., `example.pdf`).
  - `project`: The project ID this attachment belongs to.

**Example** (using `curl`):
```bash
curl -X POST \
-H "Authorization: Bearer ACCESS_TOKEN" \
-F "file=@example.pdf" \
-F "project=1" \
https://your-app-name.onrender.com/api/attachments/
```

**Response**:
```json
{
  "id": 1,
  "file": "https://your-app-name.onrender.com/media/attachments/example.pdf",
  "uploaded_at": "2025-01-06T15:00:00Z",
  "project": 1
}
```

---

#### **Download an Attachment**
**Endpoint**: `/attachments/<id>/download/`

**Method**: `GET`

**Authorization**: **Required**

**Response**:
- Returns the file as a download.

---

### 3. Project Comments

#### **Add a Comment to a Project**
**Endpoint**: `/comments/`

**Method**: `POST`

**Authorization**: **Required**

**Request Body**:
```json
{
  "project": 1,
  "content": "This project looks great!"
}
```

**Response**:
```json
{
  "id": 1,
  "project": 1,
  "content": "This project looks great!",
  "created_at": "2025-01-06T15:00:00Z"
}
```

---

### HTTP Status Codes
- `200 OK`: Request was successful.
- `201 Created`: Resource was successfully created.
- `400 Bad Request`: There was an error with the request.
- `401 Unauthorized`: Authentication is required or invalid.
- `403 Forbidden`: You do not have permission to perform this action.
- `404 Not Found`: The requested resource does not exist.

---

## Development Notes for Frontend Integration
1. **Authentication**:
   - Obtain the `access` token and store it securely (e.g., local storage).
   - Add the `Authorization: Bearer <ACCESS_TOKEN>` header to all authenticated requests.

2. **Error Handling**:
   - Handle common errors like `401 Unauthorized` and `403 Forbidden` to prompt the user for login or show an appropriate error message.

3. **File Uploads**:
   - Use `multipart/form-data` for attachment uploads.
   - Provide meaningful feedback during the upload process.

---

Let me know if you need further clarification or additions! 🚀
