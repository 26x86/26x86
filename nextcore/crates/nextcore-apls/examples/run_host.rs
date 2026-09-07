//! Execute an explicit local JSON request with `cargo run -p nextcore-apls
//! --example run_host -- /path/to/request.json`.
use nextcore_apls::runner::RunnerRequest;

fn main() {
    let result = (|| -> Result<bool, Box<dyn std::error::Error>> {
        let mut args = std::env::args_os().skip(1);
        let path = args.next().ok_or("usage: run_host REQUEST.json")?;
        if args.next().is_some() {
            return Err("usage: run_host REQUEST.json".into());
        }
        let request: RunnerRequest = serde_json::from_slice(&std::fs::read(path)?)?;
        let outcome = request.run()?;
        println!("{}", serde_json::to_string_pretty(&outcome)?);
        Ok(outcome.macos_boot_verified)
    })();
    match result {
        Ok(true) => {}
        Ok(false) => std::process::exit(2),
        Err(error) => {
            eprintln!("{error}");
            std::process::exit(2);
        }
    }
}
