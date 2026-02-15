# OAuth 2.0 Setup Guide

## Step 1: Install Backend Dependencies

The new OAuth dependencies have been added to `requirements.txt`. Install them by running:

```bash
cd backend
pip install -r requirements.txt
```

Required new packages:
- `authlib` - OAuth client library
- `pyjwt` - JWT token generation/verification  
- `itsdangerous` - Secure token signing
- `httpx` - Async HTTP client for API calls

## Step 2: Create OAuth Applications

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client ID**
5. Configure the OAuth consent screen if prompted
6. For Application Type, select **Web application**
7. Add authorized redirect URI:
   ```
   http://localhost:8000/auth/google/callback
   ```
8. Copy the **Client ID** and **Client Secret**

### GitHub OAuth Setup

1. Go to [GitHub Settings > Developer Settings](https://github.com/settings/developers)
2. Click **New OAuth App**
3. Fill in the application details:
   - **Application name**: Synod (or your preferred name)
   - **Homepage URL**: `http://localhost:5173`
   - **Authorization callback URL**: `http://localhost:8000/auth/github/callback`
4. Click **Register application**
5. Copy the **Client ID**
6. Generate a new **Client Secret** and copy it

## Step 3: Configure Environment Variables

Edit the `backend/.env` file and add your OAuth credentials:

```env
# OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GITHUB_CLIENT_ID=your_github_client_id_here
GITHUB_CLIENT_SECRET=your_github_client_secret_here

# JWT Configuration (already set with a default, but you should change it)
JWT_SECRET=your_random_secret_key_here_use_at_least_32_characters

# Application URLs (already configured for local development)
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000
```

## Step 4: Restart the Backend Server

After installing dependencies and configuring the `.env` file, restart your backend server:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
uvicorn main:app --reload
```

## Step 5: Test OAuth Flow

1. Open your browser to `http://localhost:5173/login`
2. Click the **Google** or **GitHub** sign-in button
3. You should be redirected to the OAuth provider's login page
4. After authorizing, you'll be redirected back and logged in
5. You should land on the dashboard with your user info

## Troubleshooting

### "Invalid redirect_uri" error
- Make sure the redirect URI in your OAuth app settings exactly matches:
  - Google: `http://localhost:8000/auth/google/callback`
  - GitHub: `http://localhost:8000/auth/github/callback`

### "Token verification failed" error
- Check that your `.env` file has the correct Client ID and Secret
- Ensure the backend server restarted after updating `.env`

### Backend errors on startup
- Run `pip install -r requirements.txt` to ensure all dependencies are installed
- Check that the `.env` file exists and is properly formatted

## What Changed

### Backend
- Added OAuth routes: `/auth/google/login`, `/auth/google/callback`, `/auth/github/login`, `/auth/github/callback`
- Implemented JWT token generation and verification
- Added session middleware for OAuth state management

### Frontend
- Created `AuthCallback.jsx` component to handle OAuth redirects
- Updated `AuthContext` to use JWT tokens instead of localStorage mock data
- Login/Signup pages now redirect to backend OAuth endpoints
- Added `/auth/callback` route for OAuth flow completion
