#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::process::{Child, Command};
use std::sync::{Arc, Mutex};
use std::env;
use serde_json::Value;
use reqwest::blocking::Client;

#[tauri::command]
fn ping_backend() -> Result<Value, String> {
    let client = Client::new();
    let url = "http://127.0.0.1:8000/api/ping";
    client
        .get(url)
        .send()
        .map_err(|e| format!("request failed: {}", e))?
        .json()
        .map_err(|e| format!("json decode failed: {}", e))
}

#[tauri::command]
fn simulate_backend(payload: Value) -> Result<Value, String> {
    let client = Client::new();
    let url = "http://127.0.0.1:8000/api/simulate";
    client
        .post(url)
        .json(&payload)
        .send()
        .map_err(|e| format!("request failed: {}", e))?
        .json()
        .map_err(|e| format!("json decode failed: {}", e))
}

#[tauri::command]
fn backend_request(method: String, path: String, body: Option<Value>) -> Result<Value, String> {
    let client = Client::new();
    let normalized_path = if path.starts_with('/') {
        path
    } else {
        format!("/{}", path)
    };
    let url = format!("http://127.0.0.1:8000{}", normalized_path);
    let method_upper = method.to_uppercase();

    let response = match method_upper.as_str() {
        "GET" => client.get(&url).send(),
        "POST" => client.post(&url).json(&body.unwrap_or(Value::Null)).send(),
        _ => return Err(format!("unsupported method: {}", method)),
    }
    .map_err(|e| format!("request failed: {}", e))?;

    let status = response.status();
    let json: Value = response
        .json()
        .map_err(|e| format!("json decode failed: {}", e))?;

    if !status.is_success() {
        return Err(format!("backend status {}: {}", status.as_u16(), json));
    }

    Ok(json)
}

fn start_python_backend() -> Option<Child> {
    // Prefer a bundled backend executable if present (commodity_lab_backend or .exe),
    // otherwise fall back to invoking the Python script using system python.
    if let Ok(exe_path) = env::current_exe() {
        if let Some(parent) = exe_path.parent() {
            let candidate_unix = parent.join("commodity_lab_backend");
            let candidate_win = parent.join("commodity_lab_backend.exe");
            if candidate_unix.exists() {
                return Command::new(candidate_unix).spawn().ok();
            }
            if candidate_win.exists() {
                return Command::new(candidate_win).spawn().ok();
            }
            // also check for bundled path in a `bundled/backend` subdir
            let bundled = parent.join("bundled").join("backend");
            let b_unix = bundled.join("commodity_lab_backend");
            let b_win = bundled.join("commodity_lab_backend.exe");
            if b_unix.exists() {
                return Command::new(b_unix).spawn().ok();
            }
            if b_win.exists() {
                return Command::new(b_win).spawn().ok();
            }
        }
    }

    // Fallback to system python script
    Command::new("python").arg("tauri/backend/main.py").spawn().ok()
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

    {
        let mut lock = backend_handle.lock().unwrap();
        *lock = start_python_backend();
    }

    let bh = backend_handle.clone();

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![ping_backend, simulate_backend, backend_request])
        .setup(move |_app| {
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri")
        .run(move |_app_handle, event| match event {
            tauri::RunEvent::Exit => {
                if let Ok(mut lock) = bh.lock() {
                    kill_child(&mut *lock);
                }
            }
            _ => {}
        });
}
