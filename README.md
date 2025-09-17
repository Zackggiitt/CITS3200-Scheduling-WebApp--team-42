# CITS3200 Scheduling WebApp - Team 42

A comprehensive school scheduling web application designed for teaching teams, including facilitators, administrators, and unit coordinators, to manage course timetables and teacher assignments. This application streamlines scheduling tasks and improves administrative efficiency.

## Features

- **Multi-role Authentication**: Support for Admin, Unit Coordinator, and Facilitator roles
- **Google OAuth Integration**: Secure login with Google accounts
- **Intelligent Scheduling**: Automated facilitator assignment based on skills and availability
- **Availability Management**: Facilitators can set their availability and unavailability periods
- **Session Swapping**: Request and manage session swaps between facilitators
- **Module & Unit Management**: Create and manage academic units and modules
- **Skills-based Matching**: Match facilitators to sessions based on their expertise levels
- **Rate Limiting & Security**: Built-in CSRF protection and request rate limiting

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite (development) / PostgreSQL (production)
- **Authentication**: Flask-Login + Google OAuth 2.0
- **Frontend**: HTML/CSS/JavaScript with Jinja2 templates
- **Security**: CSRF protection, rate limiting, secure session management

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-repo/CITS3200-Scheduling-WebApp--team-42.git
cd CITS3200-Scheduling-WebApp--team-42-main
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///dev.db

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Admin User Configuration
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-admin-password
```

### 5. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google OAuth2 API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:5006/auth/google/callback`
   - `http://127.0.0.1:5006/auth/google/callback`
   - For production: `https://yourdomain.com/auth/google/callback`
7. Copy the Client ID and Client Secret to your `.env` file

### 6. Database Initialization

```bash
# Initialize the database and create tables
python application.py

# Or manually initialize with sample data
python init_sample_data.py
```

### 7. Create Sample Data (Optional)

```bash
# Create sample facilitators
python create_sample_facilitators.py create

# Create sample modules
python create_modules.py

# Create sample sessions
python add_sample_sessions.py
```

## Running the Application

### Development Mode

```bash
python application.py
```

The application will be available at `http://localhost:5006`

### Production Mode

For production deployment, consider using a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 application:app
```

## Default Users

After initial setup, a default admin user is created:
- **Email**: admin@example.com (or value from ADMIN_EMAIL env var)
- **Password**: admin123 (or value from ADMIN_PASSWORD env var)

## User Roles & Permissions

### Admin
- Full system access
- Manage all users, units, modules, and sessions
- View and generate schedules
- System configuration

### Unit Coordinator
- Manage their assigned units and modules
- Create and manage sessions
- Assign facilitators to sessions
- View schedules for their units

### Facilitator
- Set availability and unavailability
- View assigned sessions
- Request session swaps
- Update personal profile

## API Endpoints

### Authentication
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /auth/google` - Google OAuth login
- `GET /auth/google/callback` - Google OAuth callback

### Admin Routes
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/generate-schedule` - Schedule generation interface
- `POST /admin/generate-schedule` - Generate optimized schedule

### Facilitator Routes
- `GET /facilitator/dashboard` - Facilitator dashboard
- `GET /facilitator/availability` - Manage availability
- `POST /facilitator/set-availability` - Set availability periods

### Unit Coordinator Routes
- `GET /uc/dashboard` - Unit coordinator dashboard
- `GET /uc/manage-units` - Manage units
- `POST /uc/create-session` - Create new session

## Database Management

### Reset Database
```bash
python reset_db.py
```

### Run Migrations
```bash
flask db upgrade
```

### Create Admin User
```bash
python add_admin_user.py
```

## Testing

Run the test suite:

```bash
python -m pytest test/
```

Individual test files:
```bash
python test/login_integration_test.py
python test/session_test.py
python test/privilege_escalation_test.py
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure DATABASE_URL is correctly set in `.env`
   - Check database file permissions

2. **Google OAuth Not Working**
   - Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in `.env`
   - Check redirect URIs in Google Cloud Console

3. **Port Already in Use**
   - The app runs on port 5006 by default
   - Change port in `application.py` if needed

4. **Module Import Errors**
   - Ensure virtual environment is activated
   - Reinstall requirements: `pip install -r requirements.txt`

### Debug Mode

Enable debug mode for detailed error messages:
```bash
export FLASK_DEBUG=1
python application.py
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit your changes: `git commit -m 'Add feature description'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Team

CITS3200 Team 42 - University of Western Australia

## Support

For issues and questions, please create an issue in the GitHub repository or contact the development team.
