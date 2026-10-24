---
name: auditoria-github
description: Cómo ejecutar e interpretar la auditoría de repos GitHub que produce el inventario de stack técnico real (data/audit/stack_inventory.json)
---

# Auditoría de GitHub

## Qué hace
Descubre el stack técnico **real** (evidencia en manifiestos, no autodeclarado)
de todos los repos del usuario, sin clonar: `gh repo list` + árbol vía
`gh api .../git/trees` + descarga selectiva de manifiestos.

## Cómo ejecutar
```
tools/.venv/Scripts/python.exe tools/github_audit/audit.py --salida data/audit
```
Flags: `--usuario <login>` (por defecto, el autenticado en gh),
`--incluir-privados`, `--excluir-forks`, `--incluir-archivados`.

## Esquema de stack_inventory.json
- `repos[]`: por repo — `stack{categoria: [skills]}`, `manifiestos`, `readme{}`,
  `lenguajes_bytes`, `topics`, `ultimo_push`
- Categorías de stack: `lenguajes`, `frameworks`, `cloud`, `iac`, `contenedores`,
  `kubernetes`, `cicd`, `datos`, `calidad`, `build`, `herramientas`, `automatizacion`
- `agregado`: `skills_por_frecuencia`, `cloud_providers`, `repos_sin_readme`

## Cómo interpretar (para decisiones de CV y perfil)
1. **Skills con evidencia** = las que pueden afirmarse en el CV sin exagerar.
2. **Repos con IaC/contenedores/CI** = material para la narrativa Cloud Support.
3. **README débil** (`existe: false` o `caracteres < 300`) = oportunidad de
   mejora del portafolio (proponer, nunca aplicar sin aprobación).
4. Contrasta siempre con `rendercv/CONTEXTO_CARRERA.md`: el CV no debe declarar
   nada que los repos no evidencien, y las brechas detectadas van al backlog
   de proyectos de ese archivo.

## Seguridad
- Solo lectura. Nada de clones salvo solicitud explícita del usuario.
- Nunca descargar/leer: `.env*`, `*.pem`, `*.key`, `id_rsa*`, `*.tfvars`,
  `credentials*`, `service-account*.json`.
