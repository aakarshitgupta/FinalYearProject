import cors from "cors";
import dotenv from "dotenv";
import express from "express";
import fs from "node:fs";
import mongoose from "mongoose";
import path from "node:path";

import { Analysis } from "./models/Analysis.js";
import { runPythonBridge } from "./services/pythonBridge.js";

dotenv.config();

const app = express();
const port = Number(process.env.PORT || 5000);

function normalizeOrigin(origin) {
  return origin.replace(/\/$/, "");
}

const clientOrigins = (process.env.CLIENT_ORIGIN || "http://localhost:5173")
  .split(",")
  .map((origin) => origin.trim())
  .map(normalizeOrigin)
  .filter(Boolean);
const allowAnyOrigin = clientOrigins.includes("*");

app.use(
  cors({
    origin(origin, callback) {
      if (allowAnyOrigin || !origin || clientOrigins.includes(normalizeOrigin(origin))) {
        callback(null, true);
        return;
      }

      callback(new Error("Not allowed by CORS"));
    },
  })
);
app.use(express.json({ limit: "1mb" }));

let mongoEnabled = false;

async function connectMongo() {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    return;
  }

  try {
    await mongoose.connect(uri);
    mongoEnabled = true;
    console.log("MongoDB connected");
  } catch (error) {
    console.warn(`MongoDB connection failed: ${error.message}`);
  }
}

app.get("/api/health", async (_request, response) => {
  response.json({
    ok: true,
    service: "fake-news-xai-api",
    mongoEnabled,
  });
});

app.get("/api/diagnostics", async (_request, response) => {
  const modelDir = process.env.MODEL_DIR || "";
  const dataPath = process.env.DATA_PATH || "";
  const pythonPath = process.env.PYTHON_PATH || "";
  const modelFile = modelDir ? path.join(modelDir, "model.safetensors") : "";

  response.json({
    ok: true,
    env: {
      port,
      clientOrigins,
      pythonPath,
      modelDir,
      dataPath,
    },
    exists: {
      pythonPath: Boolean(pythonPath && fs.existsSync(pythonPath)),
      modelDir: Boolean(modelDir && fs.existsSync(modelDir)),
      modelFile: Boolean(modelFile && fs.existsSync(modelFile)),
      dataPath: Boolean(dataPath && fs.existsSync(dataPath)),
    },
    sizes: {
      modelFile:
        modelFile && fs.existsSync(modelFile) ? fs.statSync(modelFile).size : 0,
    },
  });
});

app.get("/api/config", async (_request, response) => {
  try {
    const result = await runPythonBridge({
      command: "config",
      modelDir: process.env.MODEL_DIR,
      dataPath: process.env.DATA_PATH,
    });
    response.json({
      ...result,
      mongoEnabled,
    });
  } catch (error) {
    response.status(500).json({
      error: error.message,
    });
  }
});

app.post("/api/analyze", async (request, response) => {
  const { text, method = "lime", topK = 10, saveHistory = true } = request.body;

  if (!text || !String(text).trim()) {
    response.status(400).json({
      error: "Text is required.",
    });
    return;
  }

  try {
    const result = await runPythonBridge({
      command: "analyze",
      modelDir: process.env.MODEL_DIR,
      text: String(text),
      method,
      topK,
    });

    let savedRecord = null;
    if (mongoEnabled && saveHistory) {
      savedRecord = await Analysis.create({
        inputText: String(text),
        method,
        topK,
        prediction: result.prediction,
        explanation: result.explanation,
      });
    }

    response.json({
      ...result,
      savedRecord,
    });
  } catch (error) {
    response.status(500).json({
      error: error.message,
    });
  }
});

app.post("/api/batch", async (request, response) => {
  const { texts } = request.body;

  if (!Array.isArray(texts) || texts.length === 0) {
    response.status(400).json({
      error: "texts must be a non-empty array.",
    });
    return;
  }

  try {
    const result = await runPythonBridge({
      command: "batch",
      modelDir: process.env.MODEL_DIR,
      texts,
    });
    response.json(result);
  } catch (error) {
    response.status(500).json({
      error: error.message,
    });
  }
});

app.get("/api/history", async (_request, response) => {
  if (!mongoEnabled) {
    response.json({
      enabled: false,
      items: [],
    });
    return;
  }

  const items = await Analysis.find().sort({ createdAt: -1 }).limit(20).lean();
  response.json({
    enabled: true,
    items,
  });
});

connectMongo().finally(() => {
  app.listen(port, () => {
    console.log(`API server listening on http://localhost:${port}`);
  });
});
