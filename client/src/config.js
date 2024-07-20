const useLocalApi = false; // Set this to true when you want to use the local API

const config = {
  apiBaseUrl: useLocalApi
    ? process.env.REACT_APP_LOCAL_API_BASE_URL || "http://127.0.0.1:5000"
    : process.env.REACT_APP_API_BASE_URL || "http://localhost:8000",
  clientId: process.env.REACT_APP_CLIENT_ID,
  clientSecret: process.env.REACT_APP_CLIENT_SECRET,
};

export default config;
