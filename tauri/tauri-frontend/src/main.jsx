import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { installAiKeyFileCompatibility } from "./aiKeyFileCompat";
import "./styles.css";

installAiKeyFileCompatibility();

createRoot(document.getElementById("root")).render(<App />);