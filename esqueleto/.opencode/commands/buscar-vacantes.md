---
description: Barrido de búsqueda de vacantes en los 4 portales (queda en data/vacantes/pendientes para tu aprobación)
agent: scout-vacantes
subtask: true
---

Ejecuta un barrido de búsqueda de vacantes para el perfil Cloud Support Engineer /
Junior DevOps (Colombia, remoto). Usa SIEMPRE `nivel: "junior"`:

1. `empleo_buscar` con portal "todos", texto "cloud support", pais "CO", nivel "junior"
2. `empleo_buscar` con portal "getonboard", texto "soporte tecnico", pais "CO", nivel "junior"
3. `empleo_buscar` con portal "remotive", texto "technical support", nivel "junior"
4. `empleo_buscar` con portal "greenhouse", texto "associate support", nivel "junior"
5. `empleo_listar` estado "pendientes"

Presenta el resultado así:
- **Nuevas guardadas** por portal (con errores y cuántas filtró por seniority)
- **Top 10 candidatas** por afinidad con la narrativa (Cloud Support > DevOps
  junior > infraestructura > afines), con id, título, empresa, región y URL
- Recordatorio: el usuario decide cuáles marcar (aprobada/descartada)
$ARGUMENTS
