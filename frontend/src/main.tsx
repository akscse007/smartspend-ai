import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { Toaster } from "react-hot-toast";

import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 3200,
          style: {
            background: "rgba(15, 23, 42, 0.92)",
            color: "#e5eefb",
            border: "1px solid rgba(129, 140, 248, 0.18)",
            borderRadius: "18px",
            boxShadow: "0 24px 60px rgba(2, 8, 23, 0.4)",
          },
          success: {
            iconTheme: {
              primary: "#22c55e",
              secondary: "#06121c",
            },
          },
          error: {
            iconTheme: {
              primary: "#fb7185",
              secondary: "#06121c",
            },
          },
        }}
      />
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
