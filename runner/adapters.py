import shutil, subprocess, os, urllib.request, json
class AdapterMissing(Exception): pass
def run(agent, prompt):
    if agent == "mock": return f"mock-ok: {prompt[:80]}"
    if agent == "ollama":
        host = os.getenv("OLLAMA_HOST","http://host.docker.internal:11434")
        model = os.getenv("OLLAMA_MODEL","llama3.1:8b")
        req = urllib.request.Request(host+"/api/generate",
            data=json.dumps({"model":model,"prompt":prompt,"stream":False}).encode(),
            headers={"Content-Type":"application/json"})
        try: return json.load(urllib.request.urlopen(req, timeout=600)).get("response","")
        except Exception as e: raise AdapterMissing(f"ollama: {e}")
    cli = {"claude-code":"claude","hermes":"hermes","codex":"codex","opencode":"opencode"}.get(agent)
    if agent == "openclaw":
        return "openclaw-stub: verbinde API-Key, siehe .env"
    if cli and shutil.which(cli) is None:
        raise AdapterMissing(f"CLI '{cli}' fehlt im Runner-Image")
    out = subprocess.run([cli, prompt], capture_output=True, text=True, timeout=600)
    if out.returncode != 0: raise AdapterMissing(out.stderr[-500:])
    return out.stdout[-4000:]
