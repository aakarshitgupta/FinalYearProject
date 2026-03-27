import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..", "..");
const defaultPythonPath = path.join(projectRoot, ".venv", "Scripts", "python.exe");
const scriptPath = path.join(projectRoot, "scripts", "api_predict.py");

export function runPythonBridge(payload) {
  const pythonPath = process.env.PYTHON_PATH || defaultPythonPath;

  return new Promise((resolve, reject) => {
    const child = spawn(pythonPath, [scriptPath], {
      cwd: projectRoot,
      env: {
        ...process.env,
      },
      stdio: ["pipe", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });

    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      reject(new Error(`Failed to start Python bridge: ${error.message}`));
    });

    child.on("close", (code) => {
      if (code !== 0) {
        reject(new Error(stderr.trim() || `Python bridge exited with code ${code}`));
        return;
      }

      try {
        resolve(JSON.parse(stdout));
      } catch (error) {
        reject(new Error(`Invalid JSON from Python bridge: ${error.message}`));
      }
    });

    child.stdin.write(JSON.stringify(payload));
    child.stdin.end();
  });
}
