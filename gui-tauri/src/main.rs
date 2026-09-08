#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

//! 26x86 Tauri wizard shell — WKWebView (macOS) / WebView2 (Windows).
//! Loads the Python HTTP bridge URL when provided via ``--url`` or ``X86_WIZARD_URL``.

use std::env;
use std::process;

use tauri::{Manager, Url};

fn parse_args() -> (Option<String>, String) {
    let mut url: Option<String> = None;
    let mut title = "NextCore".to_string();
    let args: Vec<String> = env::args().skip(1).collect();
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--url" if i + 1 < args.len() => {
                url = Some(args[i + 1].clone());
                i += 2;
                continue;
            }
            "--title" if i + 1 < args.len() => {
                title = args[i + 1].clone();
                i += 2;
                continue;
            }
            other if other.starts_with("http://") || other.starts_with("https://") => {
                url = Some(other.to_string());
            }
            _ => {}
        }
        i += 1;
    }
    if url.is_none() {
        if let Ok(env_url) = env::var("X86_WIZARD_URL") {
            if !env_url.trim().is_empty() {
                url = Some(env_url);
            }
        }
    }
    (url, title)
}

fn main() {
    let (url, title) = parse_args();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(move |app| {
            let window = app
                .get_webview_window("main")
                .expect("missing main webview window");
            let _ = window.set_title(&title);

            if let Some(ref raw) = url {
                match Url::parse(raw) {
                    Ok(parsed) => {
                        if let Err(err) = window.navigate(parsed) {
                            eprintln!("navigate to {raw} failed: {err}");
                        }
                    }
                    Err(err) => eprintln!("invalid X86_WIZARD_URL {raw}: {err}"),
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .unwrap_or_else(|err| {
            eprintln!("NextCore Tauri shell failed: {err}");
            process::exit(1);
        });
}
