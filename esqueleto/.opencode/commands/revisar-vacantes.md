---
description: Revisión interactiva de vacantes pendientes — te las presenta por recencia y decides aceptar/rechazar una por una
---

Modo revisión de vacantes. Trabaja conmigo, vacante por vacante:

1. `empleo_listar` (pendientes) — orden por recencia. Toma el primer lote de 5.
2. POR CADA vacante muéstrame: título, empresa, portal, fecha, región, salario
   si hay, y 2-3 líneas de requisitos clave (de su descripcion_md). Si no tiene
   descripción, usa `empleo_detalle` primero.
3. Pregúntame: ¿aprobar (a) / descartar (d) / saltar (s)? — y ejecuta
   `empleo_marcar` según mi respuesta inmediatamente.
4. Repite con el siguiente lote hasta que yo diga "stop".
5. Al final: resumen de aprobadas/descartadas y sugerencia de las 2 más
   prometedoras para `/analizar-vacante <id>` (con probabilidad estimada según
   la rúbrica de `analisis-fit`).
$ARGUMENTS
