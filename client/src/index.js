import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import reportWebVitals from "./reportWebVitals";

import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://068431a7f1d4b25d48014f759db6d5ca@o4507733909766144.ingest.us.sentry.io/4507733911994368",
  integrations: [Sentry.replayIntegration()],
  // Session Replay
  replaysSessionSampleRate: 1.0, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
  replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  tracePropagationTargets: [
    "https://6a1a-74-192-181-8.ngrok-free.app",
    // Pattern to match all routes in your React app
    /^https:\/\/6a1a-74-192-181-8\.ngrok-free\.app\//,
    "https://strongly-talented-troll.ngrok-free.app",
    // Pattern to match all routes on your server
    /^https:\/\/strongly-talented-troll\.ngrok-free\.app\//,
  ],
  environment: process.env.REACT_APP_ENVIRONMENT,
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
