<p align="center">
  <img src="https://img.shields.io/badge/MyAgent-Copiloto%20IA%20Empresarial-1e40af?style=for-the-badge&logo=robot&logoColor=white" alt="MyAgent"/>
</p>

<h1 align="center">🤖 MyAgent — Copiloto IA Empresarial</h1>

<p align="center">
  <strong>Sistema multi-agente de IA para operaciones empresariales impulsado por Qwen Cloud</strong><br/>
  <em>7 Agentes · 20 Herramientas MCP · 5 Servidores · 7 Idiomas · Debate Agent Society</em>
</p>

<p align="center">
  <a href="README.md">📖 English Documentation</a> ·
  <a href="docs/architecture-diagram.md">📐 Diagrama de Arquitectura</a> ·
  <a href="http://43.98.164.203:3000">🌐 Demo en Vivo</a>
</p>

---

## 🎯 El Problema

Operaciones empresariales gestionando **+32,000 puntos de venta** con **+500 productos digitales** enfrentan:

- 📚 Curva de aprendizaje pronunciada para nuevos operadores
- 🔀 Múltiples interfaces para diferentes verticales (energía, logística, recargas)
- ⏱️ Procesos manuales que consumen tiempo con clientes esperando
- 💸 Dificultad para maximizar comisiones por desconocimiento del catálogo
- 📊 Sin insights estratégicos sobre crecimiento y optimización

## 💡 La Solución

**MyAgent** es un copiloto de IA agéntica que:

| Capacidad | Descripción |
|-----------|-------------|
| 🧠 **Entiende** | Lenguaje natural en 7 idiomas (texto + voz + imágenes) |
| 🎯 **Rutea** | Supervisor inteligente dirige al agente especializado correcto |
| ⚡ **Ejecuta** | Acciones transaccionales autónomas vía protocolo MCP (20 herramientas) |
| 🧠 **Recuerda** | Memoria persistente cross-sesión con olvido inteligente |
| 🛡️ **Protege** | Guardrails de doble capa (regex + filtro ML de contenido) |
| 🏛️ **Asesora** | Agent Society — 5 agentes debaten estrategias con datos reales |
| 👁️ **Ve** | Análisis visual de facturas, etiquetas y documentos |

---

## 🏗️ Arquitectura

<p align="center">
  <img src="docs/architecture.png" alt="Diagrama de Arquitectura MyAgent" width="100%"/>
</p>

<details>
<summary>📐 Ver Diagrama Interactivo (Código Mermaid)</summary>

Ver [docs/architecture-diagram.md](docs/architecture-diagram.md) para el código Mermaid completo que puedes pegar en [mermaid.live](https://mermaid.live).

</details>

---

## 🤖 Agentes

| Agente | Modelo | Capacidades |
|--------|--------|-------------|
| 🧭 **Supervisor** | qwen3.5-omni-plus | Clasificación multilingüe de intención + routing (7 idiomas) |
| ⚡ **Energía** | qwen3.5-omni-flash | Comparación de tarifas · Análisis de ahorro · Gestión de contratos |
| 📦 **Logística** | qwen3.5-omni-flash | Registro de paquetes · Verificación de entrega · Devoluciones |
| 💬 **Soporte** | qwen3.5-omni-flash | Recargas telefónicas (13 países) · PINs digitales (19 plataformas) · RAG |
| 👁️ **Visual** | qwen-vl-max | OCR de facturas · Lectura de etiquetas · Análisis de documentos |
| 📊 **Analytics** | qwen3.5-omni-flash | Seguimiento de comisiones · Tendencias · Rendimiento de productos |
| 🏛️ **Society** | qwen3.5-omni-plus | Debate estratégico multi-agente (Ventas · Marketing · Operaciones · Finanzas · Moderador) |

---

## 📡 Protocolo MCP

5 servidores exponiendo 20 herramientas vía Model Context Protocol estándar:

| Servidor | Herramientas | Descripción |
|----------|-------------|-------------|
| `myagent-energia` | `calcular_ahorro_energetico` · `preparar_contrato_energia` · `consultar_tarifas_disponibles` | Tarifas y contratos energéticos |
| `myagent-logistica` | `registrar_paquetes` · `confirmar_entrega_paquete` · `consultar_estado_paquete` · `gestionar_devolucion` · `listar_paquetes_pendientes` | Gestión de paquetería |
| `myagent-catalogo` | `procesar_recarga` · `activar_pin_digital` · `buscar_en_manuales` · `consultar_catalogo_productos` | Recargas, PINs, RAG, Catálogo |
| `myagent-memory` | `store_memory` · `recall_memories` · `forget_memory` · `get_memory_summary` | Gestión de memoria persistente |
| `myagent-analytics` | `get_daily_summary` · `get_top_products` · `get_commission_trend` · `compare_periods` | Inteligencia de negocio |

---

## 🏛️ Agent Society

Cuando los usuarios hacen preguntas estratégicas, MyAgent activa un **debate multi-agente**:

1. 💼 **Estratega de Ventas** — Patrones de ingresos, conversión, venta cruzada
2. 📢 **Asesor de Marketing** — Visibilidad, posicionamiento, tácticas locales
3. ⚙️ **Optimizador de Operaciones** — Eficiencia, cuellos de botella, ahorro de tiempo
4. 📊 **Analista Financiero** — ROI, proyecciones, costo-beneficio
5. 🎯 **Moderador** — Identifica conflictos → desafía posiciones → sintetiza consenso

El debate se ejecuta en **2 rondas** con datos reales del negocio, produciendo un plan de acción priorizado visible en tiempo real vía SSE streaming.

---

## 🌍 Multilingüe

Detección automática de idioma y respuesta en:

🇪🇸 Español · 🇬🇧 Inglés · 🇫🇷 Francés · 🇵🇹 Portugués · 🇩🇪 Alemán · 🇮🇹 Italiano · 🇨🇳 Chino

La interfaz también se traduce dinámicamente según el idioma seleccionado.

---

## 🛡️ Seguridad

| Capa | Protección |
|------|-----------|
| **Validador de Entrada** | Detección de prompt injection basada en regex, límites de longitud |
| **Filtro ML de Contenido** | Qwen Cloud como clasificador (SAFE/OFF_TOPIC/HARMFUL/ATTACK) |
| **Sanitizador de Salida** | Enmascaramiento de DNI/teléfonos, redacción de datos sensibles |
| **Validador de Transacciones** | Límites de monto, verificación de formato telefónico |
| **Rate Limiting MCP** | Limitación por cliente con registro de auditoría |

---

## ☁️ Infraestructura

Desplegado en **Alibaba Cloud**:

| Servicio | Uso |
|----------|-----|
| **ECS** (Elastic Compute Service) | Contenedores Docker (backend + frontend + PostgreSQL + Redis) |
| **VPC** (Virtual Private Cloud) | Red aislada (172.16.0.0/16) |
| **Security Group** | Reglas de firewall (puertos 22, 80, 443, 3000, 8000) |
| **OSS** (Object Storage Service) | Almacenamiento de imágenes del agente visual |
| **Log Service (SLS)** | Logging centralizado estructurado |
| **Qwen Cloud** (Model Studio) | 30+ modelos LLM con failover automático |

### 🔄 Router Inteligente de Modelos

MyAgent incluye un sistema de failover automático de modelos:
- **16 modelos por rol** en cadena de prioridad
- Si la cuota gratuita de un modelo se agota → cambia automáticamente al siguiente
- Soporta 30+ modelos de Qwen Cloud (flash, plus, max, coder, deepseek, glm)
- Cero tiempo de inactividad independientemente de los límites individuales

---

## 🚀 Inicio Rápido

```bash
# Clonar
git clone <repo-url>
cd hackaton-enterprise

# Configurar
cp .env.example .env
# Editar .env con tu API key de Qwen Cloud

# Ejecutar con Docker Compose
docker compose up --build

# Acceder
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Health:   http://localhost:8000/health
```

---

## 📊 Resultados de Tests

```
78 tests en producción | 77 aprobados | 98.7% tasa de éxito
Probado contra: http://43.98.164.203 (Alibaba Cloud ECS)
```

---

## 🏆 Tracks del Hackathon

| Track | Cobertura |
|-------|-----------|
| **Track 4: Autopilot Agent** | ✅ Principal — Automatización end-to-end de workflows con human-in-the-loop |
| **Track 1: MemoryAgent** | ✅ Fuerte — Memoria persistente cross-sesión con olvido inteligente |
| **Track 3: Agent Society** | ✅ Feature — Debate multi-agente con resolución de conflictos |

---

## 👤 Autor

**Sebastián Díaz G.**
AI Software Engineer · Full-Stack Developer

---

## 📄 Licencia

[Licencia MIT](LICENSE) — Open Source para Global AI Hackathon con Qwen Cloud 2026.
