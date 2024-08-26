# Your Repo Name

## Setup

1. Clone this repo.
2. Make sure you've got npm and python3 installed on your machine.
3. Run these commands:
   ```
   cd client && npm i --legacy-peer-deps
   cd ../server && pip3 install -r requirements.txt
   ```

## Run the app

This section assumes you're using VSCode.

1. Fire up ngrok:
   ```
   bash ./scripts/start_ngrok.sh
   ```
2. Create `.env` files in both `client` and `server` directories.
3. In `client/.env`, add these keys:
   - REACT_APP_API_URL
   - REACT_APP_BASE_URL
   - REACT_APP_CLIENT_ID
   - REACT_APP_CLIENT_SECRET
   - REACT_APP_STRIPE_PUBLISHABLE_KEY
4. In `server/.env`, add these keys:
   - SERVER_URL
   - REACT_APP_URL
   - DATABASE_URL
   - SECRET_KEY
   - CLIENT_ID
   - CLIENT_SECRET
   - SUPABASE_URL
   - SUPABASE_KEY
   - SUPABASE_PROJECT_ID
   - SUPABASE_JWT_SECRET
   - SUPABASE_ALL_USERS_PASSWORD
   - ENVIRONMENT
5. Update `client/.env` REACT_APP_BASE_URL to the ngrok forwarding address for localhost:3000.
6. Update `server/.env` REACT_APP_URL to the same ngrok forwarding address.
7. Start the client:
   ```
   cd client && npm run start
   ```
8. Add this launch.json entry to run the Flask app:
   ```json
   {
     "name": "Python: Flask",
     "type": "debugpy",
     "request": "launch",
     "module": "flask",
     "console": "integratedTerminal",
     "env": {
       "FLASK_APP": "server/app.py",
       "FLASK_ENV": "development"
     },
     "args": ["run", "--host=localhost", "--port=8000", "--debug"],
     "jinja": true
   }
   ```

## Login

Before you can login, you need to set up a Salesforce DevHub.

### Setting up a Salesforce Devhub and Creating a Scratch Org

1-4 are one-time steps. 

1. Sign up for a Salesforce Developer Account:
   - Go to https://developer.salesforce.com/signup
   - Fill out the form with your details
   - Click "Sign me up"
   - Check your email and verify your account

2. Enable DevHub in your org:
   - Log in to your new Salesforce org
   - Click on the gear icon (Setup) in the top right
   - In the Quick Find box, type "Dev Hub"
   - Click on "Dev Hub" under Setup
   - Toggle the switch to enable Dev Hub
   - Click "Enable" on the confirmation popup

3. Install Salesforce CLI:
   - Go to https://developer.salesforce.com/tools/sfdxcli
   - Download and install the appropriate version for your OS

4. Authenticate with your DevHub:
   - Open your terminal
   - Run: `sf org login web -d -a DevHub`
   - A browser window will open. Log in with your Salesforce credentials
   - Grant access to the Salesforce CLI

5. Create a Scratch Org:
   - In your terminal, navigate to your project directory
   - Create a project-scratch-def.json file with the following content:
     ```json
     {
       "orgName": "Your Org Name",
       "edition": "Developer",
       "features": ["EnableSetPasswordInApi"],
       "settings": {
         "lightningExperienceSettings": {
           "enableS1DesktopEnabled": true
         },
         "mobileSettings": {
           "enableS1EncryptedStoragePref2": false
         }
       }
     }
     ```
   - Run: `sf org create scratch -f config/project-scratch-def.json -a YourScratchOrgAlias -d 30`

6. Set a password for your Scratch Org:
   - Run: `sf org generate password -o YourScratchOrgAlias`
   - Note down the username and password

7. Open your Scratch Org:
   - Run: `sf org open -o YourScratchOrgAlias`

## Logging In to InsideOutbound

1. Go to the forwarding url for localhost:3000 in your browser. You should see a Login page.

2. Click "Login to Sandbox".

3. Use credentials from your sandbox `sf org display -u <alias>`

4. Click Login.

5. You'll land on the "Prospecting" tab.

## Creating PRs

1. You can quickly create a PR against `main`:
   ```
   python3 /Users/nzozaya/Salesforce/io-webapp/scripts/create_pr.py
   ```

2. PRs should only have 1 commit on them. The suggested workflow is 
   - Make many commits during development
   - When opening a PR, do `git reset HEAD <commit-hash-before-your-work-started>` or `git reset HEAD~<number-of-commits-you-added>`
   - When making changes in response to PR comments, do `git commit --amend --no-edit && git push --force`