# Esquemas de tareas

El archivo `task.py` contiene tres modelos de Pydantic: `TaskCreate`, `TaskUpdate` y `TaskResponse`. Definen los datos de entrada y salida de las tareas. No guardan datos ni comprueban la autenticación o la propiedad de una tarea.

## TaskCreate

Representa los datos necesarios para crear una tarea.

| Campo | Tipo | Obligatorio | Reglas y valor predeterminado |
| --- | --- | --- | --- |
| `title` | `str` | Sí | Entre 1 y 150 caracteres después de quitar espacios exteriores. |
| `content` | `str` | No | Máximo 5.000 caracteres. Puede estar vacío; por defecto es `""`. |
| `deadline` | `AwareDatetime` | Sí | Fecha y hora con zona horaria. Se convierte a UTC. |
| `priority` | `TaskPriority` | No | Por defecto, `TaskPriority.MEDIUM`. |
| `status` | `TaskStatus` | No | Por defecto, `TaskStatus.NOT_STARTED`. |

Ninguno de estos campos admite `null`. Los valores predeterminados se aplican cuando el campo se omite, no cuando contiene un valor inválido.

Las enumeraciones se definen en `api/domain/enums.py`. Sus valores actuales son:

- `TaskPriority`: `"Low"`, `"Medium"` y `"High"`.
- `TaskStatus`: `"Not Started"`, `"In Progress"` y `"Done"`.

Se deben respetar las mayúsculas y los espacios de estos valores.

### Configuración y validadores

`ConfigDict(extra="forbid")` rechaza campos desconocidos. Esto detecta errores como `priorty` e impide proporcionar campos como `id` o `user_id`. El propietario deberá obtenerse del usuario autenticado fuera del esquema.

`strip_text` utiliza `mode="before"` para eliminar espacios exteriores de `title` y `content` antes de comprobar sus longitudes. Conserva los espacios y saltos de línea internos. Un título formado solo por espacios se convierte en `""` y se rechaza; el contenido sí puede quedar vacío.

`normalize_deadline` se ejecuta después de la validación del tipo. `AwareDatetime` exige una fecha con zona horaria y `astimezone(timezone.utc)` la convierte a UTC conservando el mismo instante. Se permiten fechas pasadas.

### Ejemplo

```json
{
  "title": "Study Python",
  "deadline": "2026-10-01T18:00:00+02:00"
}
```

El contenido será `""`, la prioridad será `"Medium"` y el estado será `"Not Started"`. La fecha se normalizará a `2026-10-01T16:00:00Z`.

## TaskUpdate

Representa una actualización parcial. Todos los campos pueden omitirse; cuando se envían, deben cumplir las siguientes reglas:

| Campo | Validación |
| --- | --- |
| `title` | Texto de entre 1 y 150 caracteres después de quitar espacios exteriores. |
| `content` | Texto de hasta 5.000 caracteres; puede quedar vacío. |
| `deadline` | Fecha y hora con zona horaria, normalizada a UTC. |
| `priority` | Un valor de `TaskPriority`. |
| `status` | Un valor de `TaskStatus`. |

### Omitir un campo no equivale a enviar null

Los campos se declaran con `| None` y `default=None`, pero `reject_null_values` rechaza cualquier `None` enviado explícitamente, representado en JSON como `null`.

Los campos omitidos conservan su valor interno predeterminado: con la configuración actual, Pydantic no ejecuta los validadores sobre los valores por defecto.

| Entrada | Efecto esperado al aplicar la actualización |
| --- | --- |
| Se omite `content` | Conservar el contenido actual. |
| `"content": "New description"` | Sustituir el contenido. |
| `"content": ""` | Dejar la descripción vacía. |
| `"content": "   "` | Normalizar la descripción a `""`. |
| `"content": null` | Rechazar la entrada. |

Para obtener únicamente los campos que envió el cliente, el código que aplique los cambios debe utilizar:

```python
changes = task_update.model_dump(exclude_unset=True)
```

Así se evita sobrescribir campos no enviados con sus valores internos por defecto. El esquema por sí solo no modifica ninguna tarea existente.

### Configuración y validadores

- `extra="forbid"` rechaza campos desconocidos.
- `reject_null_values`, con `mode="before"`, rechaza valores nulos explícitos en los cinco campos.
- `strip_text` limpia los espacios exteriores antes de comprobar las longitudes.
- `normalize_deadline` convierte a UTC una fecha ya validada.

### Actualización vacía

El esquema acepta `{}` porque todos sus campos pueden omitirse. El rechazo de una petición sin cambios con `400 Bad Request` deberá implementarse en el router comprobando si `changes` está vacío. Esta comprobación no está implementada en `task.py`.

### Ejemplo

```json
{
  "priority": "High",
  "status": "In Progress"
}
```

Al aplicar únicamente los campos enviados, se conservarán el título, el contenido y la fecha existentes.

## TaskResponse

Define los datos que devuelve la API para una tarea. Todos los campos son obligatorios.

| Campo | Tipo | Significado |
| --- | --- | --- |
| `id` | `int` | Identificador de la tarea. |
| `title` | `str` | Título. |
| `content` | `str` | Descripción, que puede estar vacía. |
| `deadline` | `AwareDatetime` | Fecha y hora de vencimiento con zona horaria. |
| `priority` | `TaskPriority` | Prioridad. |
| `status` | `TaskStatus` | Estado. |
| `user_id` | `int` | Identificador del propietario. |

`ConfigDict(from_attributes=True)` permite construir y validar el modelo leyendo atributos de un objeto, además de aceptar diccionarios. El objeto debe proporcionar los atributos correspondientes a los campos del esquema.

Este modelo comprueba tipos, campos requeridos y valores de las enumeraciones. No repite los límites de longitud ni la limpieza de los esquemas de entrada. Tampoco convierte la fecha a UTC: exige que tenga zona horaria, pero la normalización debe haberse realizado antes. La capa de persistencia deberá proporcionar fechas con zona horaria al recuperar datos.

Cuando un endpoint declare `response_model=TaskResponse`, FastAPI utilizará el esquema para validar y serializar la respuesta, limitando los campos expuestos a los definidos en él.

## Gestión de errores

Los validadores lanzan `ValueError` cuando detectan un valor no permitido. Pydantic recoge estos errores como errores de validación.

- En una petición validada por FastAPI, normalmente se devuelve `422 Unprocessable Entity` y no se ejecuta el cuerpo del endpoint.
- Si se instancia el modelo directamente desde Python, puede capturarse `pydantic.ValidationError`.
- Si la salida de un endpoint incumple su `response_model`, se trata de un error de la aplicación y normalmente produce una respuesta `500`.

Los esquemas no lanzan `HTTPException`. La respuesta `400` prevista para una actualización vacía corresponde a la capa HTTP.
