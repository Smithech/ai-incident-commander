# ADR-003: PostgreSQL como estado persistente

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

La aplicación requiere persistencia durable para almacenar el estado de dominio asociado a la investigación de incidentes.

En particular, necesitamos persistir entidades como:

- `Incident`
- `Investigation`
- `InvestigationEvent`

## Alternativas consideradas

### 1. PostgreSQL

Ventajas: 

- Soporte ACID y transacciones.
- Integridad referencial mediante claves foráneas.
- Modelo relacional apropiado para Incident, Investigation e InvestigationEvent.
- Permite realizar consultas históricas y relaciones entre entidades.
- Soporte para índices y restricciones de integridad.
- PostgreSQL ofrece JSONB, permitiendo almacenar información estructurada que pueda evolucionar sin abandonar el modelo relacional.
- Buena capacidad para consultas analíticas sobre el historial de investigaciones.
- Soporte adecuado para múltiples instancias de la aplicación.
- SQLAlchemy y asyncpg proporcionan integración asíncrona con el stack actual.
- Existe una ruta de evolución clara hacia mayores volúmenes y concurrencia.

Desventajas:

- Requiere ejecutar y administrar un servicio de base de datos.
- Tiene mayor complejidad operacional que SQLite.
- Para desarrollo local requiere configurar una instancia de PostgreSQL, aunque esta complejidad se reduce utilizando Docker.
- Requiere gestionar migraciones de esquema.

### 2. SQLite

Ventajas: 

- No requiere un servidor de base de datos separado.
- Configuración extremadamente sencilla.
- La base de datos puede almacenarse como un único archivo.
- Muy útil para desarrollo local, pruebas y prototipos.
- Bajo coste operacional.
- Mantiene un modelo relacional y soporta transacciones.

Desventajas

- El modelo de concurrencia es menos apropiado para un servicio distribuido con múltiples instancias.
- El almacenamiento está ligado a un archivo local.
- La operación en entornos distribuidos requiere resolver explícitamente el acceso al archivo y su almacenamiento.
- Presenta menos opciones naturales para escalar horizontalmente.
- No encaja tan bien con una arquitectura donde varias instancias de FastAPI puedan acceder simultáneamente al mismo estado durable.
- Migrar posteriormente desde SQLite hacia una base de datos servidor puede introducir trabajo adicional.

## Decisión

PostgreSQL será la persistencia principal del estado durable de la aplicación.

Es importante distinguir dos responsabilidades diferentes:

### Persistencia de dominio

La persistencia del dominio representa información propia de la aplicación y debe mantenerse independientemente de la tecnología utilizada para ejecutar el workflow.

```
Domain Persistence

PostgreSQL
  ├── Incident
  ├── Investigation
  │     └── result (JSONB)
  └── InvestigationEvent
```

### Persistencia de workflow

El checkpoint de LangGraph representa el estado necesario para persistir y recuperar la ejecución de un workflow.

```
Workflow Persistence

LangGraph
   └── checkpoint / workflow execution state
```

La inicialización inicial del esquema se realizó mediante
`Base.metadata.create_all()` como una decisión provisional para el MVP.

Con la primera evolución real del esquema, la incorporación de
`Investigation.result` como columna `JSONB`, esta estrategia deja de ser
suficiente porque `create_all()` no modifica tablas existentes.

A partir de este punto se utilizará Alembic para gestionar la evolución
versionada del esquema de PostgreSQL.

`Base.metadata.create_all()` no será utilizado como mecanismo de migración
del esquema en entornos donde existan migraciones versionadas.

## Consecuencias

### Positivas
- El dominio tiene una fuente de verdad persistente y transaccional.
- Se mantiene una separación clara entre dominio y ejecución del workflow.
- La aplicación puede evolucionar hacia múltiples instancias.
- Se pueden consultar y auditar investigaciones históricas.
- La persistencia puede incorporar información flexible mediante JSONB cuando sea necesario.
- El stack actual de acceso a datos ya está validado.

### Negativas
- Se introduce PostgreSQL como dependencia de infraestructura.
- El entorno de desarrollo necesita una instancia de PostgreSQL, resuelta actualmente mediante Docker.
- Será necesario gestionar migraciones de esquema.
- La persistencia del dominio y los checkpoints de LangGraph deberán
coordinarse conceptualmente, aunque sean mecanismos independientes.

### Riesgos
Ninguno

## Notas

La inicialización inicial mediante `Base.metadata.create_all()` fue
intencionalmente provisional para evitar introducir Alembic antes de que
existiera una necesidad real de evolución del esquema.

La incorporación de `Investigation.result` constituye esa primera necesidad
real. Por ello, Alembic se introduce en este punto del desarrollo y será el
mecanismo utilizado para las futuras modificaciones versionadas del esquema.
