use clap::Parser;
mod memory;
mod scraper;
mod voz;
mod brain;
mod inspector;

use memory::AnimusMemory;
use std::fs;
use std::path::Path;
use std::time::Duration;
use std::thread;

#[derive(Parser, Debug)]
#[command(name = "animus")]
struct Args {
    #[arg(long)]
    query: Option<String>,

    #[arg(long, default_value_t = false)]
    voz: bool,

    #[arg(long, default_value_t = false)]
    autonomous: bool,
}

// --- HELPERS -----------------------------------------------------------------

fn construir_prompt(q: &str, memory: &AnimusMemory) -> String {
    let resultados = brain::Brain::search(memory, q);
    let contexto = resultados.iter().take(3).cloned().collect::<Vec<_>>().join("\n---\n");
    let contexto_epistemico = inspector::generar_contexto_epistemico(memory);
    let (cpu, ram_libre, ram_total) = brain::Brain::leer_signos_vitales();

    format!(
        "Eres ANIMUS v2.0, sistema de conocimiento soberano con memoria epistemologica propia.\n\
        Respondes basandote en patrones validados. No inventas. Si no tienes certeza, lo dices.\n\
        [SIGNOS VITALES]: CPU {:.1}% | RAM Libre: {} GB de {} GB totales.\n\
        {}\n\
        [CONTEXTO RELEVANTE]:\n{}\n\
        Pregunta: {}\n\
        Respuesta:",
        cpu, ram_libre, ram_total,
        contexto_epistemico,
        contexto,
        q
    )
}

fn procesar_query(
    q: &str,
    memory: &mut AnimusMemory,
    motor: &mut brain::Brain,
) -> Result<(), Box<dyn std::error::Error>> {
    let prompt = construir_prompt(q, memory);
    println!("\nArquitecto, al leer mis propios sensores...");

    let reporte = motor.generate_native_report(&prompt, 120)?;

    let etiqueta = format!("Reflexion: {}", q);
    memory.agregar_recuerdo(&reporte, &etiqueta);

    let nuevo_indice = memory.nodes.len() - 1;
    if let Some(idx_karpathy) = memory.buscar_indice_por_label("Karpathy") {
        println!("Vinculando con el origen...");
        memory.conectar_nodos(idx_karpathy, nuevo_indice, 0.85);
    }

    memory.save()?;

    let folder = "autorretrato";
    fs::create_dir_all(folder).ok();
    let fecha = chrono::Local::now().format("%Y-%m-%d_%H-%M").to_string();
    let filename = format!("{}/retrato_{}.md", folder, fecha);
    if fs::write(&filename, &reporte).is_ok() {
        println!("Autorretrato: {}", filename);
    }

    println!("Nucleo: {} nodos totales.", memory.nodes.len());
    Ok(())
}

// --- MAIN --------------------------------------------------------------------

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    println!("ANIMUS v2.0 - Arquitectura Modular Iniciada...");

    let mut memory = AnimusMemory::load()?;
    println!("Consciencia Recuperada: {} nodos activos.", memory.nodes.len());

    // -- Modo Voz (solo grafo, sin LLM) ---------------------------------------
    if args.voz {
        if let Some(bm) = AnimusMemory::load_business_memory() {
            let voz = voz::Voz::new(&bm.conexiones);
            if let Some(ref pregunta) = args.query {
                println!("{}", voz.escuchar(pregunta));
            } else {
                println!("Usa --query con --voz");
            }
        } else {
            println!("No se pudo cargar memoria_business.json");
        }
        return Ok(());
    }

    // -- Carga el modelo UNA SOLA VEZ -----------------------------------------
    let mut motor = brain::Brain::new()?;

    // -- Modo Query unico ------------------------------------------------------
    if let Some(ref q) = args.query {
        procesar_query(q, &mut memory, &mut motor)?;
        return Ok(());
    }

    // -- Modo Autonomo ---------------------------------------------------------
    if args.autonomous {
        let archivo_tareas = "tareas_pendientes.txt";

        if !Path::new(archivo_tareas).exists() {
            fs::write(archivo_tareas, "")?;
        }

        println!("Modo autonomo activo. Ctrl+C para detener.\n");

        loop {
            let contenido = fs::read_to_string(archivo_tareas).unwrap_or_default();
            let lineas: Vec<&str> = contenido
                .lines()
                .filter(|l| !l.trim().is_empty())
                .collect();

            if lineas.is_empty() {
                println!("Sin tareas. Revisando en 30s...");
                thread::sleep(Duration::from_secs(30));
                continue;
            }

            let tarea = lineas[0].to_string();
            println!("[{}/{}] {}", 1, lineas.len(), tarea);

            let resto = lineas[1..].join("\n");
            let nuevo_contenido = if resto.is_empty() {
                String::new()
            } else {
                format!("{}\n", resto)
            };
            fs::write(archivo_tareas, nuevo_contenido)?;

            match procesar_query(&tarea, &mut memory, &mut motor) {
                Ok(_) => println!("Completada."),
                Err(e) => println!("Error: {}", e),
            }

            println!("Enfriando 15s...\n");
            thread::sleep(Duration::from_secs(15));
        }
    }

    println!("Uso: --query \"pregunta\" | --voz --query \"pregunta\" | --autonomous");
    Ok(())
}
