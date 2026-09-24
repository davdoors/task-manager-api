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
# Esquemas de Usuarios
El archivo `user.py` define `UserCreate` para validar los datos de registro y `UserResponse` para describir la respuesta pública del usuario.

## UserCreate

Todos los campos de `UserCreate` son obligatorios y ninguno admite `null`.

| Campo | Tipo | Validaciones |
| --- | --- | --- |
| `username` | `str` | Entre 3 y 30 caracteres después de normalizar. Solo letras ASCII, números y guion bajo. |
| `email` | `EmailStr` | Dirección de correo con formato válido. Se eliminan espacios exteriores antes de validarla. |
| `password` | `str` | Entre 8 y 100 caracteres. Se conserva exactamente como se recibe. |

`ConfigDict(extra="forbid")` rechaza campos no definidos, como `id`, y detecta errores en los nombres de los campos.

### Normalización y validación del nombre de usuario

`normalize_username`, con `mode="before"`, elimina espacios exteriores y convierte el nombre a minúsculas antes de comprobar el tipo y la longitud. Por ejemplo, `"  David_01  "` se convierte en `"david_01"`.

Después, `validate_username` comprueba los caracteres sin expresiones regulares:

- `isascii()` exige caracteres ASCII, descartando letras acentuadas, `ñ` y emojis.
- `isalnum()` permite letras y números.
- `character == "_"` permite también el guion bajo.
- `all(...)` exige que todos los caracteres cumplan la condición.

`isalnum()` por sí solo admite letras de otros alfabetos; por eso se combina con `isascii()`. Los espacios interiores no se eliminan: se rechazan.

### Validación del correo

`strip_email` elimina espacios exteriores antes de que `EmailStr` valide y normalice la dirección. `EmailStr` requiere la dependencia `email-validator`, instalada en el entorno virtual del proyecto.

Esta validación comprueba el formato del correo; no demuestra que el buzón exista ni que pertenezca al usuario. La verificación de propiedad requeriría un proceso adicional, no implementado en este esquema.

### Tratamiento de la contraseña

La contraseña no se recorta ni se convierte a minúsculas. Sus espacios cuentan para la longitud y forman parte de su valor. Actualmente solo se comprueban el tipo y la longitud; no se exigen símbolos, números ni combinaciones de mayúsculas.

`repr=False` evita mostrarla en la representación habitual del modelo, pero no la cifra ni la excluye de `model_dump()` o de todos los posibles mensajes de error. Por ello, no debe registrarse ni devolverse el contenido completo de `UserCreate`.

El esquema no genera el hash de la contraseña. Esa operación corresponde al componente de seguridad utilizado por el servicio antes de guardar el usuario.

### Ejemplo de entrada

```json
{
  "username": "  David_01  ",
  "email": " david@example.com ",
  "password": "A sample password 123"
}
```

El nombre queda como `"david_01"`, el correo como `"david@example.com"` y la contraseña se conserva sin modificaciones.

| Entrada | Resultado |
| --- | --- |
| `username` igual a `"ab"` | Rechazada por longitud insuficiente. |
| `username` igual a `"david name"` | Rechazada por el espacio interior. |
| `username` igual a `"niño"` | Rechazada por contener un carácter no ASCII. |
| `email` igual a `"invalid"` | Rechazada por formato incorrecto. |
| Contraseña de menos de 8 o más de 100 caracteres | Rechazada por longitud. |
| Un campo obligatorio omitido o enviado como `null` | Rechazada. |

La unicidad del nombre de usuario y del correo no se comprueba aquí: requiere consultar datos y aplicar las restricciones correspondientes en el servicio y la base de datos.

## UserResponse

Define los datos públicos que devuelve la API para un usuario.

| Campo | Tipo | Obligatorio | Significado |
| --- | --- | --- | --- |
| `id` | `int` | Sí | Identificador del usuario. |
| `username` | `str` | Sí | Nombre de usuario. |

`ConfigDict(from_attributes=True)` permite obtener los campos a partir de atributos de un objeto, además de aceptar diccionarios.

No incluye correo, contraseña ni hash de contraseña. Cuando se utiliza como `response_model` de un endpoint, FastAPI valida y serializa la salida con estos campos.

El esquema comprueba los tipos y la presencia de los campos, pero no repite la normalización ni las restricciones de longitud y caracteres de `UserCreate`.

### Ejemplo de respuesta

```json
{
  "id": 1,
  "username": "david_01"
}
```

# Esquemas de autenticación

El archivo `auth.py` define `TokenResponse`, el esquema de salida previsto para el inicio de sesión. Describe la respuesta que contiene el token de acceso; no comprueba las credenciales ni genera tokens.

## TokenResponse

| Campo | Tipo | Obligatorio | Validación o valor predeterminado |
| --- | --- | --- | --- |
| `access_token` | `str` | Sí | Al menos un carácter y sin espacios en blanco. No admite `null`. |
| `token_type` | `Literal["Bearer"]` | No | Solo admite `"Bearer"`, que también es su valor predeterminado. No admite `null`. |

### Validación del token de acceso

`Field(min_length=1)` rechaza una cadena vacía. El validador `validate_token` se ejecuta después de validar el tipo y comprueba cada carácter con `isspace()`.

Si algún carácter es un espacio en blanco, lanza `ValueError("Token must not contain whitespace.")`. Esto incluye espacios normales, tabulaciones y saltos de línea, tanto al principio y al final como en el interior.

El token se conserva exactamente como se recibe: no se utiliza `strip()` ni se transforma su contenido, ya que modificarlo podría invalidarlo.

`repr=False` evita mostrar el token en la representación habitual del modelo. No lo cifra ni lo excluye de `model_dump()` o de la respuesta JSON: el cliente necesita recibirlo. Tampoco garantiza ocultarlo en todos los posibles mensajes de error.

### Tipo de token

`Literal["Bearer"]` restringe el campo a ese valor exacto. Si se omite, se utiliza `"Bearer"`; valores como `"Basic"` o `"bearer"` se rechazan por el contrato actual del esquema.

El cliente utilizará el token de acceso en la cabecera de las peticiones protegidas:

```http
Authorization: Bearer <access_token>
```

El campo `access_token` contiene únicamente el token, sin el prefijo `Bearer `.

### Ejemplos de validación

| Entrada | Resultado |
| --- | --- |
| `access_token` omitido, vacío o igual a `null` | Rechazada. |
| `access_token` con espacios, tabulaciones o saltos de línea | Rechazada. |
| `access_token` con texto no vacío y sin espacios en blanco | Aceptada por este esquema; no demuestra que sea un JWT válido. |
| `token_type` omitido | Se utiliza `"Bearer"`. |
| `token_type` igual a `"Basic"` | Rechazada. |

Ejemplo ilustrativo de la estructura de respuesta; el token mostrado no es una credencial válida:

```json
{
  "access_token": "example-access-token",
  "token_type": "Bearer"
}
```

### Alcance y responsabilidades

Este esquema valida la estructura de la respuesta, pero no verifica el formato JWT, su firma, sus claims ni su caducidad. Esas comprobaciones corresponden al componente de seguridad al autenticar peticiones.

No define `extra="forbid"`: se aplica el comportamiento predeterminado de Pydantic, que ignora campos adicionales. Los campos de salida definidos son únicamente `access_token` y `token_type`.

Cuando se utilice `response_model=TokenResponse` en el endpoint de autenticación, FastAPI validará y serializará la salida según este contrato. Una respuesta que no lo cumpla constituye un error de la aplicación y normalmente produce un `500`.

No se incluye `refresh_token`. En el flujo previsto, cuando caduque el token de acceso, el usuario deberá iniciar sesión de nuevo. El esquema no implementa por sí mismo este flujo ni la caducidad.

## Gestión de errores

Los validadores lanzan `ValueError` cuando detectan un valor no permitido. Pydantic recoge estos errores como errores de validación.

- En una petición validada por FastAPI, normalmente se devuelve `422 Unprocessable Entity` y no se ejecuta el cuerpo del endpoint.
- Si se instancia el modelo directamente desde Python, puede capturarse `pydantic.ValidationError`.
- Si la salida de un endpoint incumple su `response_model`, se trata de un error de la aplicación y normalmente produce una respuesta `500`.

Los esquemas no lanzan `HTTPException`. La respuesta `400` prevista para una actualización vacía corresponde a la capa HTTP.