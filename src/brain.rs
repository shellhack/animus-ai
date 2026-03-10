use chrono::Utc;
use crate::memory::{AnimusMemory, SerializableNode, SerializableEdge};
use sysinfo::System;
use std::process::{Command, Child, Stdio};
use std::time::Duration;

pub struct Brain {
    pub model_path: String,
    pub llama_exe: String,
    server_process: Option<Child>,
}

impl Brain {
    pub fn new() -> Result<Self, Box<dyn std::error::Error>> {
        let mut exe_path = std::env::current_exe()?;
        exe_path.pop();
        if exe_path.ends_with("release") || exe_path.ends_with("debug") {
            exe_path.pop();
            exe_path.pop();
        }

        let model_path = exe_path
            .join("model_gguf")
            .join("animus_3b_q4.gguf")
            .to_string_lossy()
            .to_string();

        let llama_exe = r"C:\llama\llama-server.exe".to_string();

        println!("🧠 Motor ANIMUS: llama-server IceLake");
        println!("📦 Cargando modelo en memoria...");

        // Lanzar servidor
        let child = Command::new(&llama_exe)
            .args([
                "-m", &model_path,
                "--port", "8080",
                "--host", "127.0.0.1",
                "-n", "300",
                "--log-disable",
            ])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|e| format!("Error lanzando llama-server: {}", e))?;

        // Esperar hasta que el servidor esté listo
        print!("⏳ Inicializando servidor");
        let client = reqwest::blocking::Client::new();
        let mut listo = false;
        for _ in 0..60 {
            std::thread::sleep(Duration::from_secs(2));
            print!(".");
            if let Ok(resp) = client.get("http://127.0.0.1:8080/health").send() {
                if let Ok(json) = resp.json::<serde_json::Value>() {
                    if json["status"].as_str() == Some("ok") {
                        listo = true;
                        break;
                    }
                }
            }
        }
        if listo {
            println!(" ✅");
        } else {
            println!(" ⚠️ Timeout — servidor puede no estar listo");
        }

        Ok(Brain {
            model_path,
            llama_exe,
            server_process: Some(child),
        })
    }

    pub fn generate_native_report(
        &mut self,
        prompt: &str,
        max_tokens: usize,
    ) -> Result<String, Box<dyn std::error::Error>> {

        println!("\n🎭 LA VOZ DE ANIMUS:");
        println!("-------------------------------------------");

        let client = reqwest::blocking::Client::new();

        let body = serde_json::json!({
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": 0.7,
            "top_p": 0.9,
            "repeat_penalty": 1.2,
            "seed": 42,
            "stop": ["Pregunta:", "Usuario:", "[SIGNOS", "<|eot_id|>"]
        });

        let resp = client
            .post("http://127.0.0.1:8080/completion")
            .json(&body)
            .timeout(Duration::from_secs(120))
            .send()?
            .json::<serde_json::Value>()?;
        
       
        let texto = resp["content"]
            .as_str()
            .unwrap_or("Sin respuesta.")
            .lines()
            .filter(|l| !l.trim().starts_with("Exploración interna:"))
            .collect::<Vec<_>>()
            .join("\n")
            .trim()
            .to_string();

        println!("{}", texto);
        println!("-------------------------------------------");

        Ok(texto)
    }

    pub fn leer_signos_vitales() -> (f32, u64, u64) {
        let mut sys = System::new_all();
        sys.refresh_cpu_usage();
        std::thread::sleep(sysinfo::MINIMUM_CPU_UPDATE_INTERVAL);
        sys.refresh_cpu_usage();
        let cpu = sys.global_cpu_usage();
        let ram_total = sys.total_memory() / 1024 / 1024 / 1024;
        let ram_libre = sys.available_memory() / 1024 / 1024 / 1024;
        (cpu, ram_libre, ram_total)
    }

    pub fn search(memory: &AnimusMemory, query: &str) -> Vec<String> {
        let palabras_query: Vec<String> = query
            .split_whitespace()
            .filter(|&w| w.len() >= 4)
            .map(|w| w.to_lowercase())
            .collect();

        memory
            .nodes
            .iter()
            .filter(|n| {
                if n.label.starts_with("Origen:") || n.label.starts_with("nacimiento") {
                    return false;
                }
                let c = n.content.to_lowercase();
                palabras_query.iter().any(|pq| c.contains(pq))
            })
            .take(3)
            .map(|n| n.content.clone())
            .collect()
    }

    pub fn integrate_knowledge(
        memory: &mut AnimusMemory,
        label: &str,
        content: &str,
    ) -> usize {
        let era = Utc::now().to_string();
        if let Some(pos) = memory.nodes.iter().position(|n| n.label == label) {
            memory.nodes[pos].weight += 2.0;
            memory.nodes[pos].connections += 1;
            pos
        } else {
            let new_idx = memory.nodes.len();
            memory.nodes.push(SerializableNode {
                label: label.to_string(),
                content: content.to_string(),
                era,
                weight: 10.0,
                connections: 1,
            });
            new_idx
        }
    }

    pub fn integrate_realtime_knowledge(
        memory: &mut AnimusMemory,
        label: &str,
        content: &str,
    ) {
        let node_idx = Self::integrate_knowledge(memory, label, content);
        if node_idx != 0 {
            memory.edges.push(SerializableEdge {
                from: 0,
                to: node_idx,
                weight: 1.0,
            });
        }
    }
}

impl Drop for Brain {
    fn drop(&mut self) {
        if let Some(mut child) = self.server_process.take() {
            let _ = child.kill();
            println!("🔴 Servidor ANIMUS detenido.");
        }
    }
}