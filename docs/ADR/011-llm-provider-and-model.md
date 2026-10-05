# ADR-010: LLM provider and model configuration

- **Fecha:** 
- **Estado:** Aceptada

## Contexto

El flujo de trabajo de investigación requiere un LLM para generar hipótesis a partir de evidencia estructurada.

El proveedor inicial seleccionado para el MVP es NVIDIA Build, utilizando su API compatible con OpenAI.

Sin embargo, la aplicación no debe estar acoplada a NVIDIA a través de su interfaz de configuración. El flujo de trabajo y la lógica de dominio deben depender de la capacidad genérica de un LLM, en lugar de un proveedor específico.

El límite de integración con el LLM está representado por el protocolo `LLMClient`, mientras que el comportamiento específico del proveedor se encapsula en `NvidiaLLMClient`.

El modelo inicial es:

`nvidia/nemotron-3-super-120b-a12b`

El modelo permanece configurable para permitir su cambio sin necesidad de modificar el código de la aplicación.

## Alternativas consideradas

### 1. Configuración especifica de proveedor

Variables de entorno: `NVIDIA_API_KEY`, `NVIDIA_BASE_URL`, `NVIDIA_MODEL`

Ventajas:

- Identifica explícitamente al proveedor.
- Fácil de entender inicialmente.
- Hace que la dependencia de NVIDIA sea inmediatamente visible en la configuración.

Desventajas:

- Acopla la configuración de la aplicación a NVIDIA.
- Cambiar de proveedor requiere modificar el contrato de configuración.
- Resta relevancia al límite de la interfaz genérica `LLMClient`.
- Mezcla la configuración de la aplicación con un proveedor de infraestructura específico.

### 2. Configuración LLM genérica

Variables de entorno: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`

Los valores iniciales apuntan a NVIDIA Build:

```
LLM_BASE_URL=https://integrate.api.nvidia.com/v1
LLM_MODEL=nvidia/nemotron-3-super-120b-a12b
```

Ventajas:

- Mantiene la configuración de la aplicación independiente del proveedor.
- Facilita el cambio de proveedores o modelos.
- Preserva la abstracción `LLMClient`.
- La configuración describe la capacidad requerida por la aplicación, en lugar de la implementación actual.
- Mantiene la lógica específica del proveedor aislada en el cliente concreto.

Desventajas:

- El proveedor resulta menos evidente basándose únicamente en los nombres de las variables de entorno.
- Diferentes proveedores pueden exponer capacidades o requisitos de configuración específicos de cada uno.
- Una configuración genérica no implica que todos los proveedores sean intercambiables.

## Decisión

Configuración LLM genérica y `NVIDIA Build` es el proveedor LLM inicial. 

El comportamiento específico del proveedor permanecerá encapsulado dentro de `NvidiaLLMClient`.

La aplicación y el flujo de trabajo dependerán del protocolo `LLMClient` en lugar de depender directamente de la configuración específica de NVIDIA o de los detalles del SDK.

Esta decisión no introduce una abstracción para múltiples proveedores ni una fábrica de proveedores. Solo se incorporarán proveedores adicionales si surge un requisito concreto.

Arquitectura:

```
Application
    │
    ▼
LLMClient
    │
    ▼
NvidiaLLMClient
    │
    ▼
NVIDIA Build API
```

## Consecuencias

### Positivas

- Facilidad de cambiar de proveedor de LLM. 
- Se manejan capacidades genéricas, independientes de las capacidades del modelo. 

### Negativas

## Notas

