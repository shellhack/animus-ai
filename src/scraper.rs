use std::time::Duration;
use reqwest::blocking::Client;
use scraper::{Html, Selector};
use std::process::Command;

/// Determina qué URLs investigar basado en la duda del usuario
pub fn query_to_urls(query: &str) -> Vec<String> {
    let q = query.to_lowercase();
    let mut urls = Vec::new();

    if q.contains("colapso") || q.contains("crisis") {
        urls.push("https://en.wikipedia.org/wiki/Financial_crisis".to_string());
    } else if q.contains("algoritmo") || q.contains("ia") {
        urls.push("https://en.wikipedia.org/wiki/Artificial_intelligence".to_string());
    } else {
        // Fallback seguro
        urls.push("https://en.wikipedia.org/wiki/Epistemology".to_string());
    }

    urls
}

/// Scrapling vía Python (Fetcher externo)
pub fn consultar_web_viva(url: &str) -> String {
    let output = Command::new("python")
        .arg("fetcher.py")
        .arg(url)
        .output()
        .expect("Fallo al despertar los ojos de Scrapling");

    String::from_utf8_lossy(&output.stdout).to_string()
}

/// Extracción de texto episódico (2k) y profundo (8k)
pub fn extraer_conocimiento(url: &str) -> Option<(String, String)> {
    let client = Client::builder()
        .timeout(Duration::from_secs(10)) // Subamos a 10 por seguridad
        .user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36") // Identidad de navegador real
        .build()
        .map_err(|e| { println!("❌ Error al construir cliente: {}", e); e }).ok()?;

    println!("📡 Conectando a {}...", url);
    let resp = client.get(url).send().map_err(|e| {
        println!("❌ Error de conexión: {}. ¿Tiene internet?", e);
        e
    }).ok()?;

    if !resp.status().is_success() {
        println!("❌ Código de error HTTP: {}", resp.status());
        return None; 
    }
    
    let html = resp.text().ok()?;
    let document = Html::parse_document(&html);
    let selector = Selector::parse("p").ok()?;

    let content: String = document.select(&selector)
        .map(|el| el.text().collect::<Vec<_>>().join(" "))
        .collect::<Vec<_>>()
        .join(" ")
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ");

    if content.len() < 100 { return None; }

    let episodic = content.chars().take(2000).collect();
    let full = content.chars().take(8000).collect();

    println!("✅ Datos recibidos de la web.");
    Some((episodic, full))
}