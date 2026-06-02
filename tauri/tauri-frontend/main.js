async function start() {
  const status = document.getElementById('status');
  const out = document.getElementById('out');
  status.textContent = 'Ready';

  document.getElementById('ping').addEventListener('click', async () => {
    try {
      const r = await fetch('http://127.0.0.1:8000/api/ping');
      const j = await r.json();
      out.textContent = JSON.stringify(j, null, 2);
    } catch (e) {
      out.textContent = 'Error: ' + e;
    }
  });
}
start();
