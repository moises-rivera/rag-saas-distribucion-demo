# RAG · SaaS Distribución Perú

**Asistente documental híbrido con recuperación semántica, BM25, RRF, reranking y generación grounded.**

Este proyecto implementa un sistema de *Retrieval-Augmented Generation* (RAG) para consultar la documentación técnica de un proyecto real. Su propósito es recuperar evidencia relevante antes de responder, mostrar las fuentes utilizadas y ofrecer una alternativa más verificable que una conversación basada únicamente en el conocimiento paramétrico de un modelo.

El corpus del proyecto real es privado y **no forma parte de este repositorio ni debe publicarse**. Para que la demostración sea reproducible, `demo_corpus/` incluye documentación totalmente ficticia creada desde cero. Cada usuario también puede conectar su propio corpus Markdown mediante `RAG_DOCS_DIR`.

RAG ayuda a reducir las alucinaciones al limitar la generación a evidencia recuperada, pero no garantiza matemáticamente cero errores. Las respuestas narrativas aplican *grounding* estricto y citas numeradas; determinadas consultas estructuradas —actualmente, preguntas de permisos basadas en tablas válidas— se resuelven de forma determinista en Python, sin usar un LLM.

## Arquitectura

```text
Markdown
  → chunking jerárquico
  → embeddings multilingües
  → BM25
  → Reciprocal Rank Fusion (RRF)
  → CrossEncoder reranking
  → Top K
  → routing
      → Python determinista
      → Claude Haiku grounded
  → respuesta + fuentes
```

El índice se construye en memoria al iniciar cada proceso. La búsqueda semántica y BM25 generan candidatos, RRF combina sus posiciones y un CrossEncoder reordena los mejores fragmentos antes de seleccionar los cinco resultados finales.

## Características principales

- Ingesta recursiva de documentos Markdown con metadata de fuente, estructura e identificador de chunk.
- Chunking consciente de encabezados H1–H6, párrafos, listas y tablas.
- División de tablas en un chunk por fila, conservando encabezados y contexto jerárquico.
- Recuperación híbrida semántica y léxica con fusión RRF.
- Reranking en CPU mediante CrossEncoder sobre la pregunta y el contexto completo del chunk.
- Enrutamiento determinista de consultas de permisos cuando existe una tabla compatible y la acción coincide.
- Generación narrativa con Claude, restringida a la evidencia recuperada y con citas `[1]`, `[2]`, etc.
- Interfaz web local y consola sobre el mismo servicio de aplicación.
- Respuestas web con fuentes, scores y modo de resolución.

## Tecnologías

- Python
- Flask
- NumPy
- sentence-transformers
- embeddings multilingües
- BM25 mediante rank-bm25
- Reciprocal Rank Fusion (RRF)
- CrossEncoder
- Anthropic Claude
- python-dotenv
- HTML, CSS y JavaScript

## Estructura del proyecto

```text
.
├── rag_final/
│   ├── chunking.py       # carga Markdown y crea chunks estructurales
│   ├── retrieval.py      # embeddings, BM25, RRF y reranking
│   ├── structured.py     # parser y respuesta determinista de permisos
│   ├── generation.py     # generación grounded con Anthropic
│   ├── service.py        # inicialización, routing y contrato de respuesta
│   ├── main.py           # interfaz de consola
│   ├── webapp.py         # aplicación y endpoints Flask
│   ├── templates/        # plantilla HTML
│   └── static/           # CSS y JavaScript del frontend
├── demo_corpus/          # documentación ficticia para la demo pública
├── docs/
│   ├── ARCHITECTURE.md   # detalle técnico de la implementación
│   └── INSTALLATION.md   # instalación y ejecución local
├── .env.example          # variables esperadas, sin secretos
├── .gitignore
└── requirements.txt
```

## Instalación y ejecución

Consulta la guía completa en [docs/INSTALLATION.md](docs/INSTALLATION.md). En resumen:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env` localmente y reemplaza el placeholder de `ANTHROPIC_API_KEY`. No compartas ni confirmes ese archivo en control de versiones.

Por defecto, `.env.example` configura `RAG_DOCS_DIR=demo_corpus`, de modo que la versión pública funciona con el corpus ficticio incluido. Puedes indicar otra carpeta absoluta o relativa con `RAG_DOCS_DIR`. Si la variable no existe, el código conserva compatibilidad con el corpus privado hermano de la instalación original cuando está disponible y, en caso contrario, usa `demo_corpus/`.

Interfaz web:

```powershell
python -m rag_final.webapp
```

Abre `http://127.0.0.1:5000` en el navegador. Para usar la consola:

```powershell
python -m rag_final.main
```

## Ejemplos de preguntas

- ¿Qué roles tienen permiso para realizar una acción documentada?
- ¿Qué evidencia existe sobre una funcionalidad concreta?
- ¿Qué restricciones describe la documentación para un flujo determinado?

Las respuestas dependen exclusivamente del corpus seleccionado. Los ejemplos públicos producen resultados sobre información ficticia; ninguna conclusión debe interpretarse como información del sistema privado real.

## Seguridad

- Las credenciales se leen desde `.env` en el backend; nunca se incorporan al frontend.
- `.env`, el entorno virtual, cachés y artefactos locales están excluidos mediante `.gitignore`.
- El corpus se trata como datos no confiables: el prompt ordena ignorar cualquier instrucción contenida en los documentos.
- La interfaz construye el contenido con nodos DOM y `textContent`; no inserta la respuesta mediante `innerHTML`.
- Los endpoints validan las entradas y devuelven mensajes sanitizados ante errores internos.
- Las fuentes públicas de la respuesta contienen metadata y scores, no el texto completo del chunk.

## Limitaciones conocidas

- El índice vive en memoria y se reconstruye una vez por proceso al primer uso.
- El corpus admitido actualmente es Markdown.
- Un directorio definido mediante `RAG_DOCS_DIR` debe existir y contener archivos `.md` legibles.
- No se utiliza una base de datos vectorial ni persistencia del índice.
- Los modelos de embeddings y reranking se ejecutan en CPU y deben estar disponibles localmente o ser descargados previamente por sus librerías.
- El servidor incluido es el servidor de desarrollo local de Flask, no un despliegue de producción.
- Claude y una clave de Anthropic son necesarios para consultas narrativas; la ruta estructurada de permisos no invoca al LLM después del retrieval.
- La calidad final depende del contenido, la estructura y la cobertura del corpus, así como de la calidad del retrieval y del reranking.

## Estado del proyecto

Prototipo funcional de portafolio con interfaz web local, consola, recuperación híbrida, reranking, routing estructurado y generación grounded. Incluye un corpus ficticio reproducible, selección configurable del corpus y configuración segura para publicación. Cada usuario debe aportar su propia clave de Anthropic para las consultas narrativas; las consultas estructuradas compatibles generan su respuesta sin LLM.

## Aprendizajes técnicos

- Combinar señales semánticas y léxicas mejora la cobertura frente al uso aislado de una sola estrategia.
- RRF permite fusionar rankings heterogéneos sin exigir que sus scores estén en la misma escala.
- El reranking con pares pregunta–contexto aporta una señal de relevancia más precisa antes del Top K final.
- Preservar jerarquías y cabeceras de tabla durante el chunking mejora la interpretabilidad de fragmentos aislados.
- Separar consultas deterministas de consultas narrativas reduce uso innecesario del LLM y hace verificables ciertos resultados.
- Grounding, citas y tratamiento defensivo del corpus son controles complementarios; ninguno sustituye la evaluación del sistema.

Para los valores exactos de modelos, profundidades y rutas, consulta [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
