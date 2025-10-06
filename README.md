# CITS3200-Scheduling-WebApp--team-42
School scheduling web app designed for teaching teams, including facilitators and administrators, to manage course timetables, teacher assignments. Aiming to streamline scheduling tasks and improve administrative efficiency

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:5000/auth/google/callback`
   - `http://127.0.0.1:5000/auth/google/callback`
7. Copy the Client ID and Client Secret
8. Create a `.env` file in the project root:
