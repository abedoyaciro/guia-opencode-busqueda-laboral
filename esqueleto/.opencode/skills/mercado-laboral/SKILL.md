---
name: mercado-laboral
description: Estrategias de búsqueda de vacantes remotas en español para Cloud Support/Junior DevOps — portales soportados, vocabulario, filtros y limitaciones conocidas
---

# Búsqueda de mercado laboral (perfil objetivo)

Perfil: Cloud Support Engineer / Junior DevOps, <CIUDAD> (<PAÍS>), remoto,
español nativo + inglés <NIVEL>.

## Portales y cómo usarlos (vía MCP `empleo`)

| Portal | Herramienta de búsqueda | Filtro región | Particularidades |
|---|---|---|---|
| getonboard | API JSON pública | `pais: "CO"` nativo | LatAm-wide; `idioma_publicacion` (es/en); salario USD/mes; la empresa solo aparece en la página (SPA) |
| remotive | API JSON pública | región en texto | búsqueda en inglés; revisar `candidate_required_location` |
| remoteok | API pública | worldwide | **limitación**: solo ~100 más recientes |
| wwr | RSS (2 categorías) | regiones en descripción | devops-sysadmin + customer-support |
| linkedin | vista **guest** (sin sesión) | `location` por país (CO→Colombia) | **MUY defensivo**: máx 2 requests, delays, cooldown 10 min tras 429/reset; no abusar (riesgo de bloqueo de IP) |
| greenhouse | API pública por board | worldwide suele | para ingesta MANUAL de empresas (Canonical board=canonical: Associate Linux Support Engineer, Cloud Support Engineer, Python Cloud graduate-level...) |

## Ingesta manual (vacantes que el usuario encuentra)

`empleo_agregar_manual(url, notas=...)` detecta greenhouse/linkedin/remotive y
descarga la descripción; para cualquier otro sitio pedir el texto copiado.
Siempre a pendientes — el usuario decide. Ejemplos útiles: carreras de
Canonical (greenhouse, board `canonical`, mucha demanda de Linux), Greenhouse
de otras empresas cloud, páginas de carreras con ATS conocido.

## Recencia

`empleo_listar` ordena por fecha de publicación (la más nueva primero). Los
portales exponen fechas distintas (ISO, RFC2822, epoch) — ya se normalizan.
Priorizar vacantes < 7 días: las juntas de screening suelen revisar en 48-72 h.

## Vocabulario de búsqueda probado

EN: "cloud support", "cloud support engineer", "devops", "infrastructure",
"sre", "technical support engineer", "cloud engineer junior"
ES: "soporte cloud", "soporte tecnico", "ingeniero de soporte", "devops junior",
"infraestructura cloud"

## Estrategia junior (IMPORTANTE — el filtro de seniority)

Los portales devuelven por defecto lo más reciente, que suele ser senior (pagan
más y se publican más). SIEMPRE usar `nivel: "junior"` en `empleo_buscar`: el
servidor filtra señales de rol senior (título: senior/lead/principal/staff/
manager/architect/head/director/expert/vp/chief; descripción: 5+/7+/10+ años).
El campo `filtradas_por_seniority` del resultado indica cuántas se descartaron.

Vocabulario junior efectivo (además del genérico):
- EN: "junior cloud", "technical support", "associate", "graduate",
  "entry level", "L1 support", "linux support", "helpdesk", "support engineer"
- ES: "soporte tecnico", "soporte nivel 1", "practicante", "técnico de soporte",
  "ingeniero de soporte"
- Greenhouse (Canonical): buscar "associate" y "support" — tienen Associate
  Linux Support Engineer, Software Support Engineer, graduate-level roles.

Realidad del mercado: las vacantes junior cloud son escasas en estos portales
(~5-15% del total). Si una búsqueda junior devuelve 0, probar variantes del
vocabulario antes de concluir que no hay nada.

## Señales de buen fit para el perfil (pre-scoring del scout)

Positivas: "junior", "entry level", "associate", "support", "L1/L2", "Latin
America", "worldwide", español requerido, remoto LatAm.
Negativas: "senior", "lead", "principal", "5+ years", onsite obligatorio,
huso horario estricto de otro continente.

## Flujo del ciclo de vida

1. `empleo_buscar` → guarda en `data/vacantes/pendientes/` (dedup por URL)
2. Usuario revisa → `empleo_marcar` aprobada/descartada (SIEMPRE decisión humana)
3. Fase análisis: `empleo_detalle` extrae requisitos → scoring vs inventario real
4. Aprobadas alimentan `data/mercado/` (agregación de requisitos por frecuencia)
   y el tailoring de CV

## Reglas del workspace que aplican aquí

- Toda vacante pasa por aprobación humana antes de análisis profundo o CV.
- Nunca postular automáticamente: el alcance es análisis + CV personalizado.
