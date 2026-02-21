#!/usr/bin/env python3
"""
Capa de memoria persistente por proyecto para Alfred Dev.

Este modulo proporciona almacenamiento SQLite local para conservar decisiones
de diseno, eventos del flujo de trabajo y metadatos de commits entre sesiones.
La trazabilidad completa (problema -> decision -> commit -> validacion) permite
que Alfred y el Bibliotecario respondan preguntas historicas con evidencia real,
no con inferencias.

La memoria es una capa lateral opcional: si no se activa, el flujo del plugin
sigue igual que siempre. Cuando esta activa, cada proyecto tiene su propia base
de datos en ``.claude/alfred-memory.db``.

Componentes principales:
    - sanitize_content(): limpia texto de posibles secretos antes de persistir.
    - MemoryDB: clase que encapsula la conexion SQLite, el esquema y todas las
      operaciones de lectura y escritura sobre la memoria.

Seguridad:
    Todo texto que entra en la base de datos pasa por sanitize_content(), que
    aplica los mismos patrones regex de secret-guard.sh. Los secretos detectados
    se reemplazan por marcadores [REDACTED:<tipo>] para evitar fugas accidentales.
"""

import json
import os
import re
import sqlite3
import stat
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Patrones de sanitizacion
# ---------------------------------------------------------------------------
# Compilados a partir de los mismos regex que usa hooks/secret-guard.sh.
# Cada tupla contiene (patron_compilado, etiqueta_para_el_marcador).
# El orden importa: los patrones mas especificos van primero para evitar
# que un patron generico consuma un match que deberia ser mas preciso.

_SECRET_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS_KEY"),
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "ANTHROPIC_KEY"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "SK_KEY"),
    (
        re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})"),
        "GITHUB_TOKEN",
    ),
    (re.compile(r"xox[bpsa]-[a-zA-Z0-9\-]{10,}"), "SLACK_TOKEN"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "GOOGLE_KEY"),
    (
        re.compile(r"SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}"),
        "SENDGRID_KEY",
    ),
    (
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        "PRIVATE_KEY",
    ),
    (
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
        ),
        "JWT",
    ),
    (
        re.compile(
            r"(?:mysql|postgresql|postgres|mongodb(?:\+srv)?|redis|amqp)"
            r"://[^\s\"']{10,}@"
        ),
        "CONNECTION_STRING",
    ),
    (
        re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"),
        "SLACK_WEBHOOK",
    ),
    (
        re.compile(
            r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"
        ),
        "DISCORD_WEBHOOK",
    ),
    # Asignaciones directas de credenciales en codigo
    (
        re.compile(
            r"(?i)(?:password|passwd|api_key|apikey|api_secret|secret_key"
            r"|auth_token|access_token|private_key)"
            r"""\s*[:=]\s*["'][^"']{8,}["']"""
        ),
        "HARDCODED_CREDENTIAL",
    ),
]

# Version actual del esquema. Se almacena en la tabla meta y se usa
# para detectar si es necesario aplicar migraciones en el futuro.
_SCHEMA_VERSION = 1


def sanitize_content(text: Optional[str]) -> Optional[str]:
    """
    Elimina posibles secretos del texto antes de persistirlo.

    Recorre los patrones de secretos conocidos (claves API, tokens, cadenas
    de conexion, credenciales hardcodeadas) y reemplaza cada coincidencia
    por un marcador ``[REDACTED:<tipo>]``. Esto garantiza que la memoria
    del proyecto nunca almacene material sensible, incluso si un agente
    intenta registrar texto que lo contenga.

    Los patrones son identicos a los del hook secret-guard.sh para mantener
    coherencia en toda la cadena de seguridad del plugin.

    Args:
        text: texto a sanitizar. Si es None, se devuelve None sin mas.

    Returns:
        Texto limpio con los secretos reemplazados por marcadores, o None
        si la entrada era None.
    """
    if text is None:
        return None

    result = text
    for pattern, label in _SECRET_PATTERNS:
        result = pattern.sub(f"[REDACTED:{label}]", result)
    return result


# ---------------------------------------------------------------------------
# SQL de creacion del esquema
# ---------------------------------------------------------------------------
# Se usa una cadena multilinea para mayor legibilidad. Las sentencias se
# ejecutan dentro de una transaccion para garantizar atomicidad.

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS iterations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    command          TEXT    NOT NULL,
    description      TEXT,
    status           TEXT    NOT NULL DEFAULT 'active',
    started_at       TEXT    NOT NULL,
    completed_at     TEXT,
    phases_completed TEXT,
    artifacts        TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    title         TEXT    NOT NULL,
    context       TEXT,
    chosen        TEXT    NOT NULL,
    alternatives  TEXT,
    rationale     TEXT,
    impact        TEXT,
    phase         TEXT,
    decided_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS commits (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    sha           TEXT    UNIQUE NOT NULL,
    message       TEXT,
    author        TEXT,
    files_changed INTEGER,
    insertions    INTEGER,
    deletions     INTEGER,
    committed_at  TEXT    NOT NULL,
    iteration_id  INTEGER REFERENCES iterations(id)
);

CREATE TABLE IF NOT EXISTS commit_links (
    commit_id   INTEGER REFERENCES commits(id),
    decision_id INTEGER REFERENCES decisions(id),
    link_type   TEXT,
    PRIMARY KEY (commit_id, decision_id)
);

CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    iteration_id  INTEGER REFERENCES iterations(id),
    event_type    TEXT    NOT NULL,
    phase         TEXT,
    payload       TEXT,
    created_at    TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_iterations_status
    ON iterations(status);
CREATE INDEX IF NOT EXISTS idx_decisions_iteration
    ON decisions(iteration_id);
CREATE INDEX IF NOT EXISTS idx_commits_iteration
    ON commits(iteration_id);
CREATE INDEX IF NOT EXISTS idx_events_iteration
    ON events(iteration_id);
CREATE INDEX IF NOT EXISTS idx_events_type
    ON events(event_type);
"""


class MemoryDB:
    """
    Interfaz de acceso a la memoria persistente de un proyecto.

    Encapsula una conexion SQLite con WAL activado y foreign keys habilitadas.
    Gestiona el ciclo de vida del esquema (creacion, deteccion de FTS5,
    versionado) y expone metodos de escritura y lectura para iteraciones,
    decisiones, commits y eventos.

    El fichero de base de datos se crea con permisos 0600 (solo el propietario
    puede leer y escribir) para proteger la informacion almacenada.

    Args:
        db_path: ruta absoluta o relativa al fichero SQLite.
    """

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._fts_enabled = False

        # Crear el directorio padre si no existe
        parent = os.path.dirname(db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

        # Activar WAL para mejor concurrencia y foreign keys para integridad
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        self._ensure_schema()
        self._detect_fts5()

        # Permisos 0600: solo el propietario puede leer y escribir.
        # Se aplica despues de la creacion para cubrir el caso de DB nueva.
        try:
            os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            # En algunos sistemas de ficheros (ej. FAT32) chmod no funciona.
            # No es critico: se continua sin permisos restrictivos.
            pass

    # --- Gestion del esquema ------------------------------------------------

    def _ensure_schema(self) -> None:
        """
        Crea las tablas e indices si no existen.

        Si la base de datos es nueva, registra la version del esquema y la
        fecha de creacion en la tabla meta. Si ya existe, se mantiene intacta
        (las sentencias usan ``IF NOT EXISTS``).
        """
        self._conn.executescript(_SCHEMA_SQL)

        # Registrar metadatos si es la primera vez
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()

        if row is None:
            now = datetime.now(timezone.utc).isoformat()
            self._conn.executemany(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                [
                    ("schema_version", str(_SCHEMA_VERSION)),
                    ("created_at", now),
                ],
            )
            self._conn.commit()

    def _detect_fts5(self) -> None:
        """
        Comprueba si el entorno SQLite soporta FTS5 y crea la tabla virtual.

        Si FTS5 esta disponible, se crea la tabla ``memory_fts`` y los triggers
        que la mantienen sincronizada con ``decisions`` y ``commits``. Si no
        esta disponible, se registra el resultado para que las busquedas usen
        el fallback con LIKE.
        """
        try:
            # Intentar crear una tabla FTS5 temporal para detectar soporte
            self._conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS _fts5_test "
                "USING fts5(test_col)"
            )
            self._conn.execute("DROP TABLE IF EXISTS _fts5_test")

            # FTS5 disponible: crear la tabla de busqueda real
            self._conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts "
                "USING fts5(source_type, source_id, content)"
            )

            # Triggers para mantener el indice actualizado.
            # Se usa INSERT OR REPLACE porque FTS5 no soporta UPDATE directo.
            self._conn.executescript("""
                CREATE TRIGGER IF NOT EXISTS fts_insert_decision
                AFTER INSERT ON decisions
                BEGIN
                    INSERT INTO memory_fts(source_type, source_id, content)
                    VALUES (
                        'decision',
                        CAST(NEW.id AS TEXT),
                        COALESCE(NEW.title, '') || ' ' ||
                        COALESCE(NEW.context, '') || ' ' ||
                        COALESCE(NEW.chosen, '') || ' ' ||
                        COALESCE(NEW.rationale, '')
                    );
                END;

                CREATE TRIGGER IF NOT EXISTS fts_insert_commit
                AFTER INSERT ON commits
                BEGIN
                    INSERT INTO memory_fts(source_type, source_id, content)
                    VALUES (
                        'commit',
                        CAST(NEW.id AS TEXT),
                        COALESCE(NEW.message, '')
                    );
                END;
            """)

            self._fts_enabled = True
        except sqlite3.OperationalError:
            # FTS5 no disponible: se usara LIKE como fallback
            self._fts_enabled = False

        # Registrar el resultado en meta para que otros componentes lo sepan
        self._conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
            ("fts_enabled", "1" if self._fts_enabled else "0"),
        )
        self._conn.commit()

    @property
    def fts_enabled(self) -> bool:
        """Indica si la busqueda de texto completo (FTS5) esta activa."""
        return self._fts_enabled

    # --- Escritura: iteraciones ---------------------------------------------

    def start_iteration(
        self,
        command: str,
        description: Optional[str] = None,
    ) -> int:
        """
        Inicia una nueva iteracion de trabajo.

        Cada iteracion representa un ciclo completo de un flujo (feature, fix,
        spike, etc.). Al crearla queda en estado ``active`` hasta que se complete
        o abandone.

        Args:
            command: tipo de flujo (feature, fix, spike, ship, audit).
            description: descripcion en lenguaje natural de la tarea.

        Returns:
            ID de la iteracion creada.
        """
        now = datetime.now(timezone.utc).isoformat()
        description = sanitize_content(description)
        cursor = self._conn.execute(
            "INSERT INTO iterations (command, description, status, started_at) "
            "VALUES (?, ?, 'active', ?)",
            (command, description, now),
        )
        self._conn.commit()
        return cursor.lastrowid

    def complete_iteration(
        self,
        iteration_id: int,
        status: str = "completed",
    ) -> None:
        """
        Marca una iteracion como completada o abandonada.

        Args:
            iteration_id: ID de la iteracion a cerrar.
            status: estado final (``completed`` o ``abandoned``).
        """
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE iterations SET status = ?, completed_at = ? WHERE id = ?",
            (status, now, iteration_id),
        )
        self._conn.commit()

    # --- Escritura: decisiones ----------------------------------------------

    def log_decision(
        self,
        title: str,
        chosen: str,
        context: Optional[str] = None,
        alternatives: Optional[List[str]] = None,
        rationale: Optional[str] = None,
        impact: Optional[str] = None,
        phase: Optional[str] = None,
        iteration_id: Optional[int] = None,
    ) -> int:
        """
        Registra una decision de diseno.

        Si no se proporciona ``iteration_id``, se vincula automaticamente a la
        iteracion activa (si existe). Todos los campos de texto se sanitizan
        antes de persistir.

        Args:
            title: titulo corto de la decision.
            chosen: opcion elegida.
            context: problema que se resolvia.
            alternatives: lista de opciones descartadas.
            rationale: justificacion de la eleccion.
            impact: nivel de impacto (low, medium, high, critical).
            phase: fase del flujo en la que se tomo la decision.
            iteration_id: ID de la iteracion (auto-detectado si se omite).

        Returns:
            ID de la decision creada.
        """
        # Auto-vincular a la iteracion activa si no se especifica
        if iteration_id is None:
            active = self.get_active_iteration()
            if active is not None:
                iteration_id = active["id"]

        now = datetime.now(timezone.utc).isoformat()

        # Sanitizar todos los campos de texto
        title = sanitize_content(title) or title
        chosen = sanitize_content(chosen) or chosen
        context = sanitize_content(context)
        rationale = sanitize_content(rationale)

        # Las alternativas se almacenan como JSON
        alt_json = None
        if alternatives is not None:
            sanitized_alts = [sanitize_content(a) or a for a in alternatives]
            alt_json = json.dumps(sanitized_alts, ensure_ascii=False)

        cursor = self._conn.execute(
            "INSERT INTO decisions "
            "(iteration_id, title, context, chosen, alternatives, "
            " rationale, impact, phase, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                iteration_id, title, context, chosen, alt_json,
                rationale, impact, phase, now,
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    # --- Escritura: commits -------------------------------------------------

    def log_commit(
        self,
        sha: str,
        message: Optional[str] = None,
        author: Optional[str] = None,
        files_changed: Optional[int] = None,
        insertions: Optional[int] = None,
        deletions: Optional[int] = None,
        iteration_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Registra un commit en la memoria.

        Si el SHA ya existe, se ignora silenciosamente (idempotencia). Si no se
        proporciona ``iteration_id``, se vincula a la iteracion activa.

        Args:
            sha: hash SHA del commit.
            message: mensaje del commit (se sanitiza).
            author: autor del commit.
            files_changed: numero de ficheros modificados.
            insertions: lineas anadidas.
            deletions: lineas eliminadas.
            iteration_id: ID de la iteracion.

        Returns:
            ID del commit creado, o None si ya existia.
        """
        # Auto-vincular a la iteracion activa si no se especifica
        if iteration_id is None:
            active = self.get_active_iteration()
            if active is not None:
                iteration_id = active["id"]

        now = datetime.now(timezone.utc).isoformat()
        message = sanitize_content(message)

        try:
            cursor = self._conn.execute(
                "INSERT INTO commits "
                "(sha, message, author, files_changed, insertions, "
                " deletions, committed_at, iteration_id) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    sha, message, author, files_changed,
                    insertions, deletions, now, iteration_id,
                ),
            )
            self._conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # El SHA ya existe: idempotencia, no es un error
            return None

    def link_commit_decision(
        self,
        commit_id: int,
        decision_id: int,
        link_type: str = "implements",
    ) -> None:
        """
        Vincula un commit con una decision.

        Permite establecer la trazabilidad entre decisiones de diseno y los
        commits que las implementan, revierten o se relacionan con ellas.

        Args:
            commit_id: ID del commit.
            decision_id: ID de la decision.
            link_type: tipo de vinculo (implements, reverts, relates).
        """
        try:
            self._conn.execute(
                "INSERT INTO commit_links (commit_id, decision_id, link_type) "
                "VALUES (?, ?, ?)",
                (commit_id, decision_id, link_type),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            # El vinculo ya existe: idempotencia
            pass

    # --- Escritura: eventos -------------------------------------------------

    def log_event(
        self,
        event_type: str,
        phase: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        iteration_id: Optional[int] = None,
    ) -> int:
        """
        Registra un evento del flujo de trabajo.

        Los eventos capturan hechos mecanicos (fase completada, gate superada,
        aprobacion del usuario) que complementan las decisiones con la
        cronologia detallada del flujo.

        Args:
            event_type: tipo de evento (phase_completed, gate_passed, etc.).
            phase: fase del flujo en la que ocurrio.
            payload: datos adicionales en formato diccionario.
            iteration_id: ID de la iteracion (auto-detectado si se omite).

        Returns:
            ID del evento creado.
        """
        if iteration_id is None:
            active = self.get_active_iteration()
            if active is not None:
                iteration_id = active["id"]

        now = datetime.now(timezone.utc).isoformat()
        payload_json = None
        if payload is not None:
            # Sanitizar los valores del payload por si contienen secretos
            sanitized = {
                k: sanitize_content(str(v)) if isinstance(v, str) else v
                for k, v in payload.items()
            }
            payload_json = json.dumps(sanitized, ensure_ascii=False)

        cursor = self._conn.execute(
            "INSERT INTO events "
            "(iteration_id, event_type, phase, payload, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (iteration_id, event_type, phase, payload_json, now),
        )
        self._conn.commit()
        return cursor.lastrowid

    # --- Lectura: iteraciones -----------------------------------------------

    def get_iteration(self, iteration_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene los datos completos de una iteracion por su ID.

        Args:
            iteration_id: ID de la iteracion a consultar.

        Returns:
            Diccionario con los datos de la iteracion, o None si no existe.
        """
        row = self._conn.execute(
            "SELECT * FROM iterations WHERE id = ?", (iteration_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_active_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la iteracion activa mas reciente.

        Solo puede haber una iteracion activa a la vez en el modelo normal
        de uso. Si hay varias (por inconsistencia), se devuelve la mas
        reciente por ID.

        Returns:
            Diccionario con los datos de la iteracion activa, o None.
        """
        row = self._conn.execute(
            "SELECT * FROM iterations WHERE status = 'active' "
            "ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def get_latest_iteration(self) -> Optional[Dict[str, Any]]:
        """
        Obtiene la iteracion mas reciente independientemente de su estado.

        A diferencia de ``get_active_iteration``, no filtra por estado.
        Util como fallback cuando no hay iteracion activa y se necesita
        contexto de la ultima iteracion registrada.

        Returns:
            Diccionario con los datos de la iteracion mas reciente, o None.
        """
        row = self._conn.execute(
            "SELECT * FROM iterations ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    # --- Lectura: decisiones ------------------------------------------------

    def get_decisions(
        self,
        iteration_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene decisiones, opcionalmente filtradas por iteracion.

        Args:
            iteration_id: si se proporciona, solo decisiones de esa iteracion.
            limit: numero maximo de resultados.

        Returns:
            Lista de diccionarios con los datos de cada decision.
        """
        if iteration_id is not None:
            rows = self._conn.execute(
                "SELECT * FROM decisions WHERE iteration_id = ? "
                "ORDER BY decided_at DESC LIMIT ?",
                (iteration_id, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM decisions ORDER BY decided_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    # --- Lectura: busqueda --------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 20,
        iteration_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca en decisiones y commits por texto.

        Si FTS5 esta disponible, usa MATCH para busqueda de texto completo.
        En caso contrario, usa LIKE como fallback (mas lento pero funcional).

        Los resultados se enriquecen con el tipo de fuente y los datos
        completos del registro original.

        Args:
            query: termino de busqueda.
            limit: numero maximo de resultados.
            iteration_id: si se proporciona, filtra por iteracion.

        Returns:
            Lista de diccionarios con los resultados, cada uno con la clave
            ``source_type`` ('decision' o 'commit') y los datos del registro.
        """
        results: List[Dict[str, Any]] = []

        if self._fts_enabled:
            results = self._search_fts(query, limit, iteration_id)
        else:
            results = self._search_like(query, limit, iteration_id)

        return results

    def _search_fts(
        self,
        query: str,
        limit: int,
        iteration_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Busqueda con FTS5 MATCH."""
        results: List[Dict[str, Any]] = []

        # FTS5 requiere escapar caracteres especiales en la query.
        # Se envuelve entre comillas dobles para tratarla como frase literal.
        safe_query = '"' + query.replace('"', '""') + '"'

        rows = self._conn.execute(
            "SELECT source_type, source_id FROM memory_fts "
            "WHERE memory_fts MATCH ? LIMIT ?",
            (safe_query, limit),
        ).fetchall()

        for row in rows:
            source_type = row["source_type"]
            source_id = int(row["source_id"])
            record = self._fetch_source_record(source_type, source_id)
            if record is None:
                continue
            # Filtrar por iteracion si se especifico
            if iteration_id is not None:
                if record.get("iteration_id") != iteration_id:
                    continue
            results.append({
                "source_type": source_type,
                **record,
            })

        return results

    def _search_like(
        self,
        query: str,
        limit: int,
        iteration_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        """Busqueda con LIKE como fallback cuando FTS5 no esta disponible."""
        results: List[Dict[str, Any]] = []
        like_pattern = f"%{query}%"

        # Buscar en decisiones
        if iteration_id is not None:
            decision_rows = self._conn.execute(
                "SELECT * FROM decisions "
                "WHERE (title LIKE ? OR context LIKE ? OR chosen LIKE ? "
                "       OR rationale LIKE ?) "
                "  AND iteration_id = ? "
                "ORDER BY decided_at DESC LIMIT ?",
                (like_pattern, like_pattern, like_pattern, like_pattern,
                 iteration_id, limit),
            ).fetchall()
        else:
            decision_rows = self._conn.execute(
                "SELECT * FROM decisions "
                "WHERE title LIKE ? OR context LIKE ? OR chosen LIKE ? "
                "      OR rationale LIKE ? "
                "ORDER BY decided_at DESC LIMIT ?",
                (like_pattern, like_pattern, like_pattern, like_pattern, limit),
            ).fetchall()

        for row in decision_rows:
            results.append({"source_type": "decision", **dict(row)})

        # Buscar en commits (solo si no se ha alcanzado el limite)
        remaining = limit - len(results)
        if remaining > 0:
            if iteration_id is not None:
                commit_rows = self._conn.execute(
                    "SELECT * FROM commits "
                    "WHERE message LIKE ? AND iteration_id = ? "
                    "ORDER BY committed_at DESC LIMIT ?",
                    (like_pattern, iteration_id, remaining),
                ).fetchall()
            else:
                commit_rows = self._conn.execute(
                    "SELECT * FROM commits WHERE message LIKE ? "
                    "ORDER BY committed_at DESC LIMIT ?",
                    (like_pattern, remaining),
                ).fetchall()

            for row in commit_rows:
                results.append({"source_type": "commit", **dict(row)})

        return results

    def _fetch_source_record(
        self, source_type: str, source_id: int
    ) -> Optional[Dict[str, Any]]:
        """Obtiene el registro completo de una fuente (decision o commit)."""
        table = "decisions" if source_type == "decision" else "commits"
        row = self._conn.execute(
            f"SELECT * FROM {table} WHERE id = ?", (source_id,)
        ).fetchone()
        return dict(row) if row else None

    # --- Lectura: cronologia ------------------------------------------------

    def get_timeline(
        self,
        iteration_id: int,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Obtiene la cronologia de eventos de una iteracion.

        Args:
            iteration_id: ID de la iteracion.
            limit: numero maximo de eventos.

        Returns:
            Lista de diccionarios con los datos de cada evento, ordenados
            cronologicamente.
        """
        rows = self._conn.execute(
            "SELECT * FROM events WHERE iteration_id = ? "
            "ORDER BY created_at ASC LIMIT ?",
            (iteration_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Lectura: estadisticas ----------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """
        Devuelve estadisticas generales de la memoria del proyecto.

        Returns:
            Diccionario con contadores (iteraciones, decisiones, commits,
            eventos), estado de FTS5, version del esquema y fecha de creacion.
        """
        stats: Dict[str, Any] = {}

        # Contadores
        for table in ("iterations", "decisions", "commits", "events"):
            row = self._conn.execute(
                f"SELECT COUNT(*) as cnt FROM {table}"
            ).fetchone()
            stats[f"total_{table}"] = row["cnt"]

        # Metadatos
        meta_rows = self._conn.execute("SELECT key, value FROM meta").fetchall()
        for row in meta_rows:
            stats[row["key"]] = row["value"]

        return stats

    # --- Mantenimiento ------------------------------------------------------

    def purge_old_events(self, retention_days: int) -> int:
        """
        Elimina eventos anteriores a la ventana de retencion.

        Solo se purgan eventos: las decisiones e iteraciones se conservan
        siempre por su alto valor para la trazabilidad.

        Args:
            retention_days: numero de dias de retencion.

        Returns:
            Numero de eventos eliminados.
        """
        cutoff = (
            datetime.now(timezone.utc) - timedelta(days=retention_days)
        ).isoformat()
        cursor = self._conn.execute(
            "DELETE FROM events WHERE created_at < ?", (cutoff,)
        )
        self._conn.commit()
        return cursor.rowcount

    # --- Ciclo de vida ------------------------------------------------------

    def close(self) -> None:
        """Cierra la conexion con la base de datos."""
        self._conn.close()
