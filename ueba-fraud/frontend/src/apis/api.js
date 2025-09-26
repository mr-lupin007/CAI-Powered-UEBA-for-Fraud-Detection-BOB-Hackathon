import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: { "x-api-key": "hackathon-secret" },
  timeout: 10000,
});

export const getHealth       = () => API.get("/health").then(r => r.data);
export const getTransactions = (limit=50) =>
  API.get(`/transactions?limit=${limit}`).then(r => r.data.transactions);
export const getAnomalies    = (min=0.2, limit=50) =>
  API.get(`/anomalies?min_risk=${min}&limit=${limit}`).then(r => r.data.anomalies);

export default API;
