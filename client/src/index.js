import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://068431a7f1d4b25d48014f759db6d5ca@o4507733909766144.ingest.us.sentry.io/4507733911994368",
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 1.0,
  environment: process.env.REACT_APP_ENVIRONMENT,
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
      <App />
    </Sentry.ErrorBoundary>
  </React.StrictMode>
);

function ErrorFallback({error}) {
  return (
    <div>
      <h1>Oops! Something went wrong.</h1>
      <pre>{error.message}</pre>
    </div>
  );
}
