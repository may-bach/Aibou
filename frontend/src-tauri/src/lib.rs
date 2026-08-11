use std::process::{Command, Child};
use std::sync::Mutex;
use std::net::TcpStream;
use std::path::PathBuf;
use tauri::Manager;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

struct BackendProcess(Mutex<Option<Child>>);

fn find_workspace_root() -> PathBuf {
    let cur = std::env::current_dir().unwrap_or_default();
    if cur.join("main.py").exists() { return cur; }
    if let Some(p) = cur.parent() { if p.join("main.py").exists() { return p.to_path_buf(); } }
    if let Some(p) = cur.parent().and_then(|p| p.parent()) { if p.join("main.py").exists() { return p.to_path_buf(); } }

    if let Ok(exe_path) = std::env::current_exe() {
        if let Some(exe_dir) = exe_path.parent() {
            if exe_dir.join("main.py").exists() { return exe_dir.to_path_buf(); }
            if let Some(p) = exe_dir.parent() { if p.join("main.py").exists() { return p.to_path_buf(); } }
            if let Some(p) = exe_dir.parent().and_then(|p| p.parent()) { if p.join("main.py").exists() { return p.to_path_buf(); } }
            if let Some(p) = exe_dir.parent().and_then(|p| p.parent()).and_then(|p| p.parent()) { if p.join("main.py").exists() { return p.to_path_buf(); } }
        }
    }

    PathBuf::from(r"d:\Aibou")
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .manage(BackendProcess(Mutex::new(None)))
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }

      // Check if backend is already active on port 8000
      let is_running = TcpStream::connect("127.0.0.1:8000").is_ok();
      if !is_running {
        let root_dir = find_workspace_root();

        let mut cmd = Command::new("python");
        cmd.args(["-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]);
        cmd.current_dir(&root_dir);

        #[cfg(target_os = "windows")]
        {
            // 0x08000000 = CREATE_NO_WINDOW (runs silently with zero black pop-up box)
            cmd.creation_flags(0x08000000);
        }

        if let Ok(child) = cmd.spawn() {
            let state = app.state::<BackendProcess>();
            let mut guard = state.0.lock().unwrap();
            *guard = Some(child);
        }
      }

      Ok(())
    })
    .on_window_event(|window, event| {
        if let tauri::WindowEvent::Destroyed = event {
            let state = window.state::<BackendProcess>();
            let mut guard = state.0.lock().unwrap();
            if let Some(mut child) = guard.take() {
                let _ = child.kill();
            }
        }
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
