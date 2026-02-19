---
name: issue-templates
description: "Generar templates de issues para bug reports y feature requests"
---

# Generar templates de issues

## Resumen

Este skill genera plantillas de issues en formato YAML para GitHub, listas para colocar en `.github/ISSUE_TEMPLATE/`. Las plantillas estandarizan la informacion que reciben los mantenedores, lo que reduce el ir y venir de preguntas y acelera la resolucion de bugs y la evaluacion de nuevas funcionalidades.

Se generan dos plantillas: una para reportes de errores y otra para solicitudes de funcionalidad. Ambas usan el formato YAML nativo de GitHub, que permite campos estructurados con validacion.

## Proceso

1. **Crear la estructura de directorios.** Verificar que existe `.github/ISSUE_TEMPLATE/`. Si no existe, crearla. Si ya hay plantillas previas, revisarlas con el usuario antes de sobreescribir.

2. **Generar la plantilla de bug report.** Crear `.github/ISSUE_TEMPLATE/bug_report.yml` con los siguientes campos:

   - **name**: "Reporte de error"
   - **description**: descripcion breve del proposito de la plantilla.
   - **title**: prefijo `[Bug]: ` para facilitar el filtrado.
   - **labels**: asignar automaticamente la etiqueta `bug`.
   - **body**: formulario con los campos:
     - Descripcion del error (textarea, obligatorio).
     - Pasos para reproducir (textarea, obligatorio): instrucciones numeradas que permitan replicar el problema de forma consistente.
     - Resultado esperado (textarea, obligatorio).
     - Resultado actual (textarea, obligatorio).
     - Entorno (dropdown o campos de texto): sistema operativo, navegador/runtime, version de la aplicacion.
     - Capturas de pantalla o logs (textarea, opcional).

3. **Generar la plantilla de feature request.** Crear `.github/ISSUE_TEMPLATE/feature_request.yml` con los siguientes campos:

   - **name**: "Solicitud de funcionalidad"
   - **description**: descripcion breve del proposito de la plantilla.
   - **title**: prefijo `[Feature]: `.
   - **labels**: asignar automaticamente la etiqueta `feature`.
   - **body**: formulario con los campos:
     - Descripcion del problema (textarea, obligatorio): que situacion motiva esta solicitud.
     - Solucion propuesta (textarea, obligatorio): como deberia funcionar la funcionalidad deseada.
     - Alternativas consideradas (textarea, opcional): otras opciones que se han valorado y por que no son suficientes.
     - Contexto adicional (textarea, opcional): capturas, mockups, enlaces o cualquier informacion complementaria.

4. **Crear el fichero de configuracion.** Opcionalmente, crear `.github/ISSUE_TEMPLATE/config.yml` para controlar el comportamiento del selector de plantillas:

   - Desactivar issues en blanco si se quiere forzar el uso de plantillas.
   - Anadir enlaces externos (foro, documentacion) como opciones de contacto alternativas.

5. **Verificar el resultado.** Comprobar que las plantillas se renderizan correctamente navegando a la pagina de creacion de issues del repositorio. Verificar que los campos obligatorios impiden enviar el formulario incompleto.

## Que NO hacer

- No generar plantillas excesivamente largas: cuantos mas campos obligatorios, menos probable es que el usuario reporte un bug.
- No usar el formato Markdown antiguo (.md) si el repositorio soporta el formato YAML (.yml), ya que este ultimo ofrece validacion de campos.
- No incluir campos que no se vayan a usar para tomar decisiones.
- No olvidar asignar labels automaticas: ahorran tiempo en el triaje.
