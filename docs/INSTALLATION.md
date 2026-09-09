# Instalación y ejecución

Esta guía prepara el paquete ejecutable `rag_final` para uso local. El corpus privado real no se distribuye con el proyecto; la versión pública incluye `demo_corpus/`, creado desde cero con contenido ficticio.

## Requisitos previos

- Python 3 con soporte para entornos virtuales.
- PowerShell en Windows.
- El corpus ficticio incluido o acceso autorizado a otro corpus Markdown propio.
- Una clave de Anthropic para la ruta de generación narrativa.
- Conectividad sólo cuando sea necesaria para instalar dependencias, obtener modelos por primera vez o invocar Anthropic durante una consulta narrativa.

## 1. Abrir el proyecto

En PowerShell, cambia al directorio raíz del repositorio:

```powershell
Set-Location ruta\al\proyecto\rag-lab-moises
```

## 2. Crear y activar el entorno virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell bloquea el script de activación, revisa la política de ejecución aplicable a tu equipo antes de cambiarla.

## 3. Instalar dependencias

```powershell
python -m pip install -r requirements.txt
```

Los modelos de `sentence-transformers` usados por el proyecto pueden requerir una descarga en el primer uso si no están ya presentes en la caché local.

## 4. Crear la configuración privada

Copia el archivo de ejemplo:

```powershell
Copy-Item .env.example .env
```

Edita `.env` localmente y define estas variables:

```dotenv
ANTHROPIC_API_KEY=coloca_aqui_tu_clave_local
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
RAG_DOCS_DIR=demo_corpus
```

`ANTHROPIC_API_KEY` es obligatoria para preguntas narrativas y debe pertenecer al usuario que ejecuta el proyecto. `ANTHROPIC_MODEL` es opcional; si se omite, el código usa `claude-haiku-4-5-20251001`. Nunca confirmes `.env` en Git ni expongas su contenido en el navegador, capturas, logs o documentación.

## 5. Seleccionar el corpus

`RAG_DOCS_DIR` acepta una ruta absoluta o una ruta relativa a la raíz del proyecto. La configuración recomendada para la versión pública es:

```dotenv
RAG_DOCS_DIR=demo_corpus
```

`demo_corpus/` contiene únicamente documentos ficticios de demostración y permite probar listas, tablas, preguntas narrativas y permisos estructurados.

Si `RAG_DOCS_DIR` no está definida, la resolución sigue este orden:

1. usar el corpus privado hermano de la instalación original si está disponible localmente;
2. en cualquier otra instalación, usar `demo_corpus/`.

El corpus privado nunca debe copiarse a este repositorio. Para usar otro corpus propio, apunta `RAG_DOCS_DIR` a una carpeta que contenga archivos Markdown; el cargador los busca recursivamente.

## 6. Ejecutar la interfaz web

Con el entorno virtual activo y desde la raíz del proyecto:

```powershell
python -m rag_final.webapp
```

Abre en el navegador:

```text
http://127.0.0.1:5000
```

El servidor escucha sólo en la interfaz local `127.0.0.1`, puerto `5000`, con modo debug desactivado. Para detener Flask, vuelve a la terminal y presiona `Ctrl+C`.

## 7. Ejecutar la consola

Como alternativa a la web:

```powershell
python -m rag_final.main
```

Escribe una pregunta y presiona Enter. Usa `salir` o `Ctrl+C` para terminar.

## Consideraciones de arranque

Al primer uso del proceso, el servicio lee el corpus, crea los chunks, calcula los embeddings y construye BM25 y el reranker en memoria. Por ello, el arranque puede tardar y consumir memoria según el tamaño del corpus. Cada proceso nuevo reconstruye el índice; no hay persistencia ni base vectorial.

Las preguntas narrativas realizan una llamada a Anthropic. Las respuestas estructuradas de permisos se generan en Python cuando el routing, la tabla y la acción cumplen las validaciones; aun así, el retrieval local debe inicializarse primero.
