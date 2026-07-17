#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use futures_util::StreamExt;
use reqwest::blocking::Client as BlockingClient;
use reqwest::Client;
use serde::Serialize;
use serde_json::Value;
use std::env;
use std::net::TcpListener;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

const DEFAULT_BACKEND_HOST: &str = "127.0.0.1";
const DEFAULT_BACKEND_PORT: u16 = 8000;

#[derive(Clone, Serialize)]
struct BackendStreamEventPayload {
    request_id: String,
    event: String,
    data: Value,
}

fn backend_host() -> String {
    env::var("COMMODITY_LAB_BACKEND_HOST")
        .ok()
        .map(|value| value.trim().to_string())
        .filter(|value| !value.is_empty())
        .unwrap_or_else(|| DEFAULT_BACKEND_HOST.to_string())
}

fn backend_port() -> u16 {
    env::var("COMMODITY_LAB_BACKEND_PORT")
        .ok()
        .and_then(|value| value.trim().parse::<u16>().ok())
        .filter(|port| *port > 0)
        .unwrap_or(DEFAULT_BACKEND_PORT)
}

fn backend_base_url() -> String {
    format!("http://{}:{}", backend_host(), backend_port())
}

fn configure_backend_port() {
    if env::var("COMMODITY_LAB_BACKEND_PORT")
        .ok()
        .and_then(|value| value.trim().parse::<u16>().ok())
        .filter(|port| *port > 0)
        .is_some()
    {
        return;
    }

    let host = backend_host();
    if let Ok(listener) = TcpListener::bind((host.as_str(), 0)) {
        if let Ok(addr) = listener.local_addr() {
            env::set_var("COMMODITY_LAB_BACKEND_PORT", addr.port().to_string());
        }
    }
}

fn backend_url(path: &str) -> String {
    let normalized_path = if path.starts_with('/') {
        path.to_string()
    } else {
        format!("/{}", path)
    };
    format!("{}{}", backend_base_url(), normalized_path)
}

#[tauri::command]
fn ping_backend() -> Result<Value, String> {
    let client = BlockingClient::new();
    client
        .get(backend_url("/api/ping"))
        .send()
        .map_err(|e| format!("request failed: {}", e))?
        .json()
        .map_err(|e| format!("json decode failed: {}", e))
}

#[tauri::command]
fn simulate_backend(payload: Value) -> Result<Value, String> {
    let client = BlockingClient::new();
    client
        .post(backend_url("/api/simulate"))
        .json(&payload)
        .send()
        .map_err(|e| format!("request failed: {}", e))?
        .json()
        .map_err(|e| format!("json decode failed: {}", e))
}

#[tauri::command]
async fn backend_request(method: String, path: String, body: Option<Value>) -> Result<Value, String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| format!("http client init failed: {}", e))?;
    let url = backend_url(&path);
    let method_upper = method.to_uppercase();

    let response = match method_upper.as_str() {
        "GET" => client.get(&url).send().await,
        "POST" => client.post(&url).json(&body.unwrap_or(Value::Null)).send().await,
        _ => return Err(format!("unsupported method: {}", method)),
    }
    .map_err(|e| format!("request failed: {}", e))?;

    let status = response.status();
    let json: Value = response
        .json()
        .await
        .map_err(|e| format!("json decode failed: {}", e))?;

    if !status.is_success() {
        return Err(format!("backend status {}: {}", status.as_u16(), json));
    }

    Ok(json)
}

fn decode_sse_block(block: &[u8]) -> Option<(String, Value)> {
    let text = String::from_utf8_lossy(block).replace("\r\n", "\n");
    let mut event = "message".to_string();
    let mut data_lines: Vec<&str> = Vec::new();
    for line in text.lines() {
        if let Some(value) = line.strip_prefix("event:") {
            event = value.trim().to_string();
        } else if let Some(value) = line.strip_prefix("data:") {
            data_lines.push(value.trim_start());
        }
    }
    if data_lines.is_empty() {
        return None;
    }
    let raw = data_lines.join("\n");
    let data = serde_json::from_str(&raw).unwrap_or_else(|_| serde_json::json!({ "text": raw }));
    Some((event, data))
}

#[tauri::command]
async fn backend_stream(
    window: tauri::Window,
    path: String,
    body: Value,
    request_id: String,
) -> Result<(), String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(120))
        .build()
        .map_err(|e| format!("http client init failed: {}", e))?;
    let response = client
        .post(backend_url(&path))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("stream request failed: {}", e))?;
    let status = response.status();
    if !status.is_success() {
        let detail = response.text().await.unwrap_or_default();
        return Err(format!("backend status {}: {}", status.as_u16(), detail));
    }

    let mut stream = response.bytes_stream();
    let mut buffer: Vec<u8> = Vec::new();
    while let Some(chunk) = stream.next().await {
        let chunk = chunk.map_err(|e| format!("stream read failed: {}", e))?;
        buffer.extend_from_slice(&chunk);
        while let Some(index) = buffer.windows(2).position(|window| window == b"\n\n") {
            let block: Vec<u8> = buffer.drain(..index + 2).collect();
            if let Some((event, data)) = decode_sse_block(&block) {
                window
                    .emit(
                        "backend-stream-event",
                        BackendStreamEventPayload {
                            request_id: request_id.clone(),
                            event,
                            data,
                        },
                    )
                    .map_err(|e| format!("stream event emit failed: {}", e))?;
            }
        }
    }
    if !buffer.is_empty() {
        if let Some((event, data)) = decode_sse_block(&buffer) {
            window
                .emit(
                    "backend-stream-event",
                    BackendStreamEventPayload {
                        request_id,
                        event,
                        data,
                    },
                )
                .map_err(|e| format!("stream event emit failed: {}", e))?;
        }
    }
    Ok(())
}

fn executable_names() -> [&'static str; 2] {
    ["commodity_lab_backend.exe", "commodity_lab_backend"]
}

fn push_backend_candidates(base: &Path, candidates: &mut Vec<PathBuf>) {
    for name in executable_names() {
        candidates.push(base.join(name));
        candidates.push(base.join("bundled").join("backend").join(name));
        candidates.push(base.join("_up_").join("bundled").join("backend").join(name));
    }
}

fn backend_executable_candidates(resource_dir: Option<PathBuf>) -> Vec<PathBuf> {
    let mut candidates = Vec::new();

    if let Some(dir) = resource_dir {
        push_backend_candidates(&dir, &mut candidates);
    }

    if let Ok(exe_path) = env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            push_backend_candidates(parent, &mut candidates);
        }
    }

    candidates
}

#[cfg(debug_assertions)]
fn source_backend_script() -> Option<PathBuf> {
    let current_dir = env::current_dir().ok()?;
    let candidates = [
        current_dir.join("tauri").join("backend").join("main.py"),
        current_dir.join("backend").join("main.py"),
        current_dir.join("..").join("tauri").join("backend").join("main.py"),
    ];
    candidates.into_iter().find(|path| path.exists())
}

#[cfg(not(debug_assertions))]
fn source_backend_script() -> Option<PathBuf> {
    None
}

fn spawn_backend_command(command: &mut Command) -> Option<Child> {
    command
        .env("COMMODITY_LAB_BACKEND_HOST", backend_host())
        .env("COMMODITY_LAB_BACKEND_PORT", backend_port().to_string())
        .env("COMMODITY_LAB_PARENT_PID", std::process::id().to_string())
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .ok()
}

fn start_python_backend(resource_dir: Option<PathBuf>) -> Option<Child> {
    for candidate in backend_executable_candidates(resource_dir) {
        if candidate.exists() {
            let mut command = Command::new(candidate);
            if let Some(child) = spawn_backend_command(&mut command) {
                return Some(child);
            }
        }
    }

    if let Some(script) = source_backend_script() {
        let mut command = Command::new("python");
        command.arg(script);
        return spawn_backend_command(&mut command);
    }

    None
}

fn wait_for_backend(timeout: Duration) -> Result<(), String> {
    let client = BlockingClient::builder()
        .timeout(Duration::from_secs(2))
        .build()
        .map_err(|e| format!("http client init failed: {}", e))?;
    let deadline = Instant::now() + timeout;
    let health_url = backend_url("/api/health");

    while Instant::now() < deadline {
        if let Ok(response) = client.get(&health_url).send() {
            if response.status().is_success() {
                return Ok(());
            }
        }
        thread::sleep(Duration::from_millis(250));
    }

    Err(format!("backend did not become ready at {}", health_url))
}

fn kill_child(child_opt: &mut Option<Child>) {
    if let Some(child) = child_opt {
        let _ = child.kill();
        let _ = child.wait();
    }
    *child_opt = None;
}

fn main() {
    let backend_handle: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let setup_backend_handle = backend_handle.clone();
    let window_backend_handle = backend_handle.clone();
    let run_backend_handle = backend_handle.clone();

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![ping_backend, simulate_backend, backend_request, backend_stream])
        .on_window_event(move |event| {
            if matches!(event.event(), tauri::WindowEvent::CloseRequested { .. }) {
                if let Ok(mut lock) = window_backend_handle.lock() {
                    kill_child(&mut *lock);
                }
            }
        })
        .setup(move |app| {
            configure_backend_port();
            let child = start_python_backend(app.path_resolver().resource_dir());
            if let Ok(mut lock) = setup_backend_handle.lock() {
                *lock = child;
            }
            thread::spawn(move || {
                if let Err(error) = wait_for_backend(Duration::from_secs(20)) {
                    eprintln!("{}", error);
                }
            });
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri")
        .run(move |_app_handle, event| match event {
            tauri::RunEvent::WindowEvent {
                event: tauri::WindowEvent::CloseRequested { .. },
                ..
            }
            | tauri::RunEvent::ExitRequested { .. }
            | tauri::RunEvent::Exit => {
                if let Ok(mut lock) = run_backend_handle.lock() {
                    kill_child(&mut *lock);
                }
            }
            _ => {}
        });
}
