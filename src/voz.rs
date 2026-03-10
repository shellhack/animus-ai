use std::collections::HashMap;

pub struct Voz {
    patrones: Vec<PatronVoz>,
}

struct PatronVoz {
    tension: String,
    resolucion: String,
    fuentes: usize,
    fuerza: f64,
    certeza: Certeza,
}

#[derive(Debug, PartialEq, Clone)]
enum Certeza {
    Alta,
    Media,
    Baja,
}

fn traducir(palabra: &str) -> &str {
    match palabra {
        "fracaso" | "fallo" | "colapso" => "failure",
        "regulación" | "regulacion" => "regulation",
        "desarrollo" | "desarrollado" => "developed",
        "algoritmo" => "algorithm",
        "brecha" => "gap",
        "crisis" => "crisis",
        "educación" | "educacion" => "education",
        "arquitectura" => "framework",
        "descubrimiento" => "discovered",
        "solución" | "solucion" => "solution",
        "innovación" | "innovacion" => "innovation",
        "desigualdad" => "inequality",
        "deuda" => "debt",
        "crédito" | "credito" => "credit",
        "política" | "politica" => "policy",
        "prevención" | "prevencion" => "prevention",
        "vulnerabilidad" => "vulnerability",
        "inflación" | "inflacion" => "inflation",
        "red" | "redes" => "networks",
        "modelo" | "modelado" => "modeled",
        "optimizado" => "optimized",
        "escala" => "scaled",
        "neural" => "neural",
        "inteligencia" => "artificial",
        _ => palabra,
    }
}

impl Voz {
    pub fn new(conexiones: &HashMap<String, f64>) -> Self {
        let mut mapa: HashMap<String, PatronVoz> = HashMap::new();

        for (clave, &fuerza) in conexiones {
            let partes: Vec<&str> = clave.splitn(2, "__>").collect();
            if partes.len() < 2 { continue; }

            let tension = partes[0].split('_').last().unwrap_or("").to_string();
            let resolucion = partes[1].split('_').last().unwrap_or("").to_string();

            if tension.is_empty() || resolucion.is_empty() { continue; }

            let llave = format!("{}>{}", tension, resolucion);
            let entry = mapa.entry(llave).or_insert(PatronVoz {
                tension: tension.clone(),
                resolucion: resolucion.clone(),
                fuentes: 0,
                fuerza: 0.0,
                certeza: Certeza::Baja,
            });
            entry.fuentes += 1;
            entry.fuerza += fuerza;
            entry.certeza = match entry.fuentes {
                n if n >= 30 => Certeza::Alta,
                n if n >= 10 => Certeza::Media,
                _            => Certeza::Baja,
            };
        }

        let mut patrones: Vec<PatronVoz> = mapa.into_values().collect();
        patrones.sort_by(|a, b| {
            let ord = |c: &Certeza| match c {
                Certeza::Alta => 0, Certeza::Media => 1, Certeza::Baja => 2
            };
            ord(&a.certeza).cmp(&ord(&b.certeza))
                .then(b.fuerza.partial_cmp(&a.fuerza).unwrap())
        });

        Voz { patrones }
    }

    pub fn escuchar(&self, filtro: &str) -> String {
        let filtro_norm = filtro.to_lowercase();

        // Traducir cada token al inglés antes de buscar
        let tokens_en: Vec<String> = filtro_norm
            .split_whitespace()
            .map(|t| traducir(t).to_string())
            .collect();

        let relevantes: Vec<&PatronVoz> = self.patrones.iter()
            .filter(|p| {
                let t = p.tension.to_lowercase();
                let r = p.resolucion.to_lowercase();
                tokens_en.iter().any(|tok| t.contains(tok.as_str()) || r.contains(tok.as_str()))
            })
            .take(8)
            .collect();

        if relevantes.is_empty() {
            return format!(
                "No tengo patrones validados para '{}'\nBrecha activa — lo que no puedo probar, no lo digo.",
                filtro
            );
        }

        let mut out = format!("🎙️ ANIMUS VOZ — '{}'\n{}\n", filtro, "─".repeat(45));

        let altas: Vec<_> = relevantes.iter().filter(|p| p.certeza == Certeza::Alta).collect();
        if !altas.is_empty() {
            out.push_str("▶ ALTA CERTEZA (30+ fuentes):\n");
            for p in altas {
                out.push_str(&format!("  {} → {} | {} fuentes | fuerza {:.0}\n",
                    p.tension, p.resolucion, p.fuentes, p.fuerza));
            }
            out.push('\n');
        }

        let medias: Vec<_> = relevantes.iter().filter(|p| p.certeza == Certeza::Media).collect();
        if !medias.is_empty() {
            out.push_str("◆ MEDIA CERTEZA (10-29 fuentes):\n");
            for p in medias {
                out.push_str(&format!("  {} → {} | {} fuentes | fuerza {:.0}\n",
                    p.tension, p.resolucion, p.fuentes, p.fuerza));
            }
            out.push('\n');
        }

        let bajas: Vec<_> = relevantes.iter().filter(|p| p.certeza == Certeza::Baja).collect();
        if !bajas.is_empty() {
            out.push_str("⚠ BRECHAS (menos de 10 fuentes):\n");
            for p in bajas {
                out.push_str(&format!("  {} → {} | {} fuentes\n",
                    p.tension, p.resolucion, p.fuentes));
            }
            out.push('\n');
        }

        out.push_str("─────────────────────────────────────────────\n");
        out.push_str("Duda activa: ¿mapa de lo recordado, o de lo que ocurre?\n");
        out
    }
}