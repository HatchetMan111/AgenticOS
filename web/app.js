async function send(e){e.preventDefault();
 const agent=document.getElementById('agent').value, prompt=document.getElementById('prompt').value;
 const r=await fetch('http://localhost:8000/tasks',{method:'POST',headers:{'Content-Type':'application/json','Authorization':'Basic '+btoa('admin:change-me')},body:JSON.stringify({title:prompt.slice(0,40),agent,prompt})});
 alert(r.ok?'Task '+ (await r.json()).id :'Fehler '+r.status);}
document.getElementById('f').addEventListener('submit',send);
