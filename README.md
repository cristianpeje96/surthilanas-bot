# 🏢 SISTEMA FINANCIERO SURTHILANAS

> Bot de Telegram para registro y análisis financiero empresarial con almacenamiento en Google Drive

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot%20API-blue.svg)](https://core.telegram.org/bots/api)
[![Google Sheets](https://img.shields.io/badge/Google-Sheets%20API-green.svg)](https://developers.google.com/sheets/api)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 ÍNDICE

- [Descripción](#-descripción)
- [Características](#-características)
- [Arquitectura](#-arquitectura)
- [Requisitos](#-requisitos)
- [Instalación](#-instalación-rápida)
- [Uso](#-uso)
- [Comandos](#-comandos-disponibles)
- [Documentación](#-documentación)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 🎯 DESCRIPCIÓN

**SURTHILANAS Financial Bot** es un sistema automatizado de gestión financiera que permite a empresas registrar, almacenar y analizar información financiera de forma simple y eficiente mediante un bot de Telegram.

### ¿Por qué este proyecto?

- ✅ **Simple**: Interfaz conversacional fácil de usar
- ✅ **Accesible**: Disponible 24/7 desde cualquier dispositivo con Telegram
- ✅ **Confiable**: Datos almacenados en Google Drive
- ✅ **Rápido**: Registro de transacciones en menos de 1 minuto
- ✅ **Inteligente**: Reportes y análisis automáticos

---

## ✨ CARACTERÍSTICAS

### Funcionalidades principales:

#### 💰 Registro de Ventas

- Número de factura
- Cliente (opcional)
- Monto
- Medio de pago
- Observaciones

#### 💸 Registro de Gastos

- Categorización automática
- Proveedor
- Monto
- Medio de pago
- Notas adicionales

#### 📊 Reportes Financieros

- Resumen diario
- Resumen semanal
- Resumen mensual
- Histórico completo
- Cálculo automático de utilidades y márgenes

#### 🔐 Seguridad

- Control de acceso por usuario
- Almacenamiento seguro en Google Drive
- Variables de entorno para credenciales
- Logging de todas las operaciones

---

## 🏗️ ARQUITECTURA

```
┌─────────────────┐
│   TELEGRAM      │  ← Usuario interactúa
│   (Cliente)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   BOT SERVER    │  ← Python + python-telegram-bot
│   (bot.py)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  BUSINESS       │  ← Validaciones + Cálculos
│  LOGIC          │
│  (utils.py)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  GOOGLE SHEETS  │  ← Almacenamiento
│  API            │
└─────────────────┘
```

### Stack Tecnológico:

- **Lenguaje**: Python 3.11+
- **Bot Framework**: python-telegram-bot 20.7
- **Almacenamiento**: Google Sheets API
- **Autenticación**: Google Service Account
- **Gestión de configuración**: python-dotenv

---

## 📦 REQUISITOS

### Software:

- Python 3.11 o superior
- pip (gestor de paquetes)
- Cuenta de Google con acceso a Google Drive
- Cuenta de Telegram

### Credenciales necesarias:

- Token de Telegram Bot
- Credenciales de Google Service Account
- IDs de hojas de Google Sheets

---

## 🚀 INSTALACIÓN RÁPIDA

### 1. Clonar el repositorio

```bash
git clone https://github.com/cristianpeje96/surthilanas-bot.git
cd surthilanas-bot
```

### 2. Instalar dependencias

```bash
# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus credenciales
nano .env
```

### 4. Configurar Google Cloud

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar Google Drive API y Google Sheets API
3. Crear Service Account y descargar credenciales JSON
4. Renombrar archivo a `credentials.json`
5. Crear hojas de cálculo y compartirlas con la Service Account

### 5. Ejecutar el bot

```bash
python bot.py
```

Si todo está correcto, verás:

```
✅ Conectado exitosamente a Google Sheets
🤖 Bot de SURTHILANAS iniciado
```

**📖 Para instrucciones detalladas, consulta [INSTALACION.md](INSTALACION.md)**

---

## 💡 USO

### Primer uso:

1. Abre Telegram
2. Busca tu bot (el username que le diste)
3. Envía `/start`
4. ¡Listo! Comienza a registrar transacciones

### Ejemplo de registro de venta:

```
Tú: /venta
Bot: Ingresa la fecha
Tú: hoy
Bot: Número de factura:
Tú: FAC-001
Bot: Cliente:
Tú: Juan Pérez
Bot: Monto:
Tú: 150000
Bot: Medio de pago:
Tú: Transferencia
Bot: Observaciones:
Tú: Pago completo
Bot: ¿Confirmas? (Sí/No)
Tú: Sí
Bot: ✅ Venta registrada exitosamente
```

**📖 Para más ejemplos, consulta [MANUAL_USUARIO.md](MANUAL_USUARIO.md)**

---

## 🎮 COMANDOS DISPONIBLES

| Comando     | Descripción                     |
| ----------- | ------------------------------- |
| `/start`    | Inicia el bot y muestra el menú |
| `/venta`    | Registrar una nueva venta       |
| `/gasto`    | Registrar un nuevo gasto        |
| `/reporte`  | Generar reporte financiero      |
| `/estado`   | Ver estado financiero actual    |
| `/ayuda`    | Mostrar ayuda                   |
| `/cancelar` | Cancelar operación actual       |

---

## 📚 DOCUMENTACIÓN

### Documentos disponibles:

- **[ARQUITECTURA_SISTEMA.md](ARQUITECTURA_SISTEMA.md)** - Arquitectura técnica del sistema
- **[INSTALACION.md](INSTALACION.md)** - Guía completa de instalación
- **[MANUAL_USUARIO.md](MANUAL_USUARIO.md)** - Manual de uso del bot
- **[FLUJOS_SISTEMA.md](FLUJOS_SISTEMA.md)** - Diagramas de flujo detallados
- **[RECOMENDACIONES_MEJORAS.md](RECOMENDACIONES_MEJORAS.md)** - Roadmap y mejoras futuras

### Estructura del proyecto:

```
surthilanas-bot/
├── bot.py                      # Bot principal
├── config.py                   # Configuración centralizada
├── google_sheets.py            # Integración con Google Sheets
├── utils.py                    # Utilidades y validaciones
├── requirements.txt            # Dependencias
├── .env.example               # Ejemplo de variables de entorno
├── .gitignore                 # Archivos ignorados por Git
├── README.md                  # Este archivo
└── docs/                      # Documentación adicional
    ├── ARQUITECTURA_SISTEMA.md
    ├── INSTALACION.md
    ├── MANUAL_USUARIO.md
    ├── FLUJOS_SISTEMA.md
    └── RECOMENDACIONES_MEJORAS.md
```

---

## 🗺️ ROADMAP

### ✅ Versión 1.0 (Actual)

- [x] Bot de Telegram funcional
- [x] Registro de ventas y gastos
- [x] Reportes básicos
- [x] Integración con Google Sheets
- [x] Control de acceso

### 🔄 Versión 1.1 (Próxima)

- [ ] Edición y eliminación de registros
- [ ] Búsqueda de registros específicos
- [ ] Notificaciones automáticas
- [ ] Exportación a PDF

### 🚀 Versión 2.0 (Futura)

- [ ] Dashboard web
- [ ] Múltiples usuarios con roles
- [ ] Gráficos visuales
- [ ] Análisis comparativo

**📖 Roadmap completo en [RECOMENDACIONES_MEJORAS.md](RECOMENDACIONES_MEJORAS.md)**

---

## 🤝 CONTRIBUIR

¡Las contribuciones son bienvenidas! Si deseas mejorar el proyecto:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Áreas donde puedes contribuir:

- 🐛 Reportar bugs
- 💡 Sugerir nuevas características
- 📝 Mejorar la documentación
- 🔧 Corregir código
- 🌍 Traducir a otros idiomas

---

## 📝 LICENCIA

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

## 👥 AUTORES

- **Desarrollador Principal** - Cristian Pejendino - Sistema desarrollado para SURTHILANAS
- **Contribuidores** - Ver la lista de [contribuidores](https://github.com/tu-usuario/surthilanas-bot/contributors)

---

## 🙏 AGRADECIMIENTOS

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Framework de Telegram Bot
- [gspread](https://github.com/burnash/gspread) - Cliente de Google Sheets
- [Google Cloud Platform](https://cloud.google.com/) - Infraestructura de APIs

---

## 📞 SOPORTE

¿Necesitas ayuda?

- 📧 Email: cristianfernandopejendino@gmail.com
- 💬 Issues: [GitHub Issues](https://github.com/cristianpeje96/surthilanas-bot.git)
- 📖 Documentación: Ver carpeta `docs/`

---

## 🌟 MOSTRAR TU APOYO

Si este proyecto te ha sido útil, ¡dale una ⭐ en GitHub!

---

## 📊 ESTADÍSTICAS

![GitHub stars](https://img.shields.io/github/stars/tu-usuario/surthilanas-bot?style=social)
![GitHub forks](https://img.shields.io/github/forks/tu-usuario/surthilanas-bot?style=social)
![GitHub issues](https://img.shields.io/github/issues/tu-usuario/surthilanas-bot)
![GitHub pull requests](https://img.shields.io/github/issues-pr/tu-usuario/surthilanas-bot)

---

<p align="center">
  Hecho con ❤️ para SURTHILANAS
</p>

<p align="center">
  <sub>© 2025 SURTHILANAS. Todos los derechos reservados.</sub>
</p>
```

---

_README.md - Sistema Financiero SURTHILANAS v1.0_
