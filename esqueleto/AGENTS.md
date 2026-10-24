# Reglas del workspace búsqueda-laboral

Sistema de agente para búsqueda de empleo: auditoría de repositorios, credenciales
profesionales, análisis de mercado y generación de CVs con RenderCV.

> Plantilla. Reemplaza los placeholders (`<...>`) antes de usarla. Este archivo lo
> lee OpenCode al iniciar la sesión: es el contrato que el agente no puede romper.

## Reglas inquebrantables

1. Lee y respeta `rendercv/CONTEXTO_CARRERA.md`: **NUNCA inventar experiencia,
   métricas, certificaciones ni tecnologías**. Separar hechos confirmados de
   hipótesis. Antes de usar una afirmación en una postulación, verificarla con el
   usuario y con el CV.
2. Narrativa principal: **<TU_ROL_OBJETIVO_PRINCIPAL>**. Narrativa secundaria:
   **<TU_ROL_OBJETIVO_SECUNDARIO>**.
3. Toda postulación pasa por aprobación humana: (a) la vacante, (b) cada CV
   generado, (c) cualquier cambio público en GitHub (descripciones, topics,
   README). El agente propone, el usuario decide.
4. Los datos persistentes van en `data/` con los esquemas JSON definidos.
   `data/` está versionado en git; los builds temporales no.
5. Nunca leer archivos que parezcan secretos (`.env`, `*.pem`, `id_rsa*`,
   `*.tfvars`, `credentials*`, `service-account*.json`). El plugin
   `proteccion-secretos` bloquea la lectura, pero no dependas de él.
6. Mantener las versiones es/en del CV consistentes (ver `rendercv/manual.md`).
7. Entorno: <TU_SISTEMA_OPERATIVO>. Dos venvs, no mezclarlos:
   - `rendercv/rendercv-env/` → RenderCV 2.8 (ejecutar con `PYTHONUTF8=1`)
   - `tools/.venv/` → dependencias del agente (mcp, playwright, requests)
8. Estructura de datos:
   - `data/audit/` → inventario técnico real (fuente de verdad del stack)
   - `data/credenciales/` → Credly, Skills Boost, LinkedIn consolidados
   - `data/perfil/` → entrevista del reclutador, reporte de prácticas, plan de brechas
   - `data/vacantes/pendientes|aprobadas|descartadas/` → ciclo de vida de vacantes
   - `data/mercado/` → requisitos agregados del mercado por frecuencia
   - `rendercv/tailored/` → variantes de CV por vacante aprobada
