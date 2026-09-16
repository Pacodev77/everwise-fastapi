# Checklist de Despliegue a Producción - Everwise FastAPI

Este documento especifica el protocolo obligatorio de seguridad, respaldo y configuración antes de desplegar el sistema Everwise FastAPI a producción y migrar los usuarios reales.

---

## 📋 Lista de Verificación (Checklist)

### 1. Variables de Entorno (`.env` fuera del repositorio)
- [x] El archivo `.env` **NUNCA** debe ser commiteado al repositorio Git.
- [x] `.gitignore` debe contener las siguientes reglas explícitas:
  ```gitignore
  .env
  .env.*
  !.env.example
  *.db
  data/*.db
  ```
- [x] Copiar `.env.example` a `.env` en el servidor de producción y ajustar los valores reales.

---

### 2. Clave Secreta de Firma de Sesión (`SECRET_AUTH_KEY`)
- [x] La clave `SECRET_AUTH_KEY` debe ser completamente **diferente entre desarrollo y producción**.
- [x] Generar una clave aleatoria criptográficamente segura de al menos 32 caracteres ejecutando:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [x] Configurar la clave generada en la variable `SECRET_AUTH_KEY` de `.env` en el servidor de producción.

---

### 3. Respaldo Obligatorio de la Base de Datos (`everwise.db`)
- [x] Antes de ejecutar cualquier script de migración o dar de alta usuarios reales, realizar un respaldo completo de la base de datos SQLite:
  ```bash
  mkdir -p backups
  cp data/everwise.db backups/everwise.db.bak_$(date +%Y%m%d_%H%M%S)
  ```
- [x] Verificar la integridad del archivo respaldado antes de proceder:
  ```bash
  sqlite3 backups/everwise.db.bak_$(date +%Y%m%d_%H%M%S) "PRAGMA integrity_check;"
  ```

---

### 4. Banderas de Seguridad de Cookies y Entorno
- [x] **`COOKIE_SECURE=True`**: Garantiza que las cookies de sesión se transmitan únicamente mediante conexiones cifradas HTTPS.
- [x] **`DEBUG=False`**: Evita la exposición de depuración interactiva o trazas internas de error al usuario final.

---

### 5. Control de Cambio Obligatorio de Contraseña (`must_change_password`)
- [x] Todos los usuarios migrados desde la versión legacy arrancan con la bandera `must_change_password = 1`.
- [x] Al iniciar sesión por primera vez con su contraseña temporal (ej. `123`), el middleware y router `/change-password` redirigen automáticamente al usuario a la pantalla de cambio de contraseña obligatoria antes de conceder acceso a los tableros.

---

## 🚀 Comando de Inicio en Producción
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```
