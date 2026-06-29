# FAQ e Incidencias Comunes - Disashop Smart POS

## Contacto de Soporte
- **Teléfono**: 981 055 210
- **Email**: soporte@disashop.com
- **Horario**: Lunes a Viernes 9:00-20:00 | Sábados 9:00-14:00
- **Urgencias fuera de horario**: 900 100 XXX (solo caídas de servicio)

---

## INCIDENCIAS DE TERMINAL

### El Smart POS no enciende
1. Verificar que está conectado a la corriente
2. Mantener pulsado el botón de encendido 10 segundos
3. Si tiene batería, verificar nivel de carga (mínimo 5%)
4. Si no responde, desconectar corriente, esperar 30 segundos, reconectar
5. Si persiste, contactar soporte técnico

### Pantalla congelada
1. Mantener pulsado botón de encendido + volumen abajo durante 15 segundos
2. El terminal se reiniciará automáticamente
3. Las transacciones en curso se recuperan tras el reinicio
4. Si se congela frecuentemente, actualizar firmware (Ajustes > Sistema > Actualizar)

### No imprime tickets
1. Verificar que hay papel en la impresora
2. Abrir compartimento de papel y verificar que está bien colocado
3. El lado térmico (brillante) debe estar hacia arriba
4. Si el papel es correcto pero no imprime, limpiar cabezal con alcohol isopropílico
5. Reiniciar terminal si persiste

### Lector de códigos no funciona
1. Limpiar la cámara/lector con paño suave
2. Verificar que la app tiene permisos de cámara
3. Probar con buena iluminación
4. Si es código dañado, introducir manualmente los últimos 8 dígitos
5. Reiniciar app de logística

---

## INCIDENCIAS DE CONECTIVIDAD

### Sin conexión a internet
1. Verificar WiFi: Ajustes > WiFi > Verificar conexión
2. Si usa datos móviles: verificar cobertura y saldo de la SIM
3. Reiniciar router/modem del establecimiento
4. Probar con datos móviles si WiFi no funciona
5. Las transacciones offline se sincronizan al recuperar conexión

### Transacción "pendiente" o "en proceso" mucho tiempo
1. NO repetir la transacción (puede duplicarse)
2. Esperar 5 minutos
3. Verificar en: Gestión > Transacciones > Pendientes
4. Si tras 10 minutos sigue pendiente, contactar soporte con el código de transacción
5. El sistema tiene protección anti-duplicados

### Error "Servidor no disponible"
1. Verificar conexión a internet
2. Puede ser mantenimiento programado (consultar alertas del sistema)
3. Esperar 15 minutos y reintentar
4. Si persiste más de 30 minutos, contactar soporte

---

## INCIDENCIAS DE TRANSACCIONES

### Recarga no aplicada al cliente
1. Verificar código de transacción en el ticket
2. Esperar hasta 5 minutos (tiempo normal de procesamiento)
3. Si tras 10 minutos no se aplica:
   - Ir a Gestión > Transacciones > buscar por código
   - Verificar estado: "completada" = se aplicó, "fallida" = no se cobró
4. Si estado es "completada" pero cliente no recibe:
   - Problema del operador destino
   - Abrir incidencia con código de transacción
   - El cliente recibirá reembolso o re-envío en 24-48h

### PIN no funciona para el cliente
1. Verificar que el cliente introduce el código EXACTO (sin espacios extra)
2. Verificar que lo canjea en la plataforma correcta
3. Algunos PINs tienen activación diferida (hasta 1 hora)
4. Si tras 2 horas no funciona:
   - Anotar código de transacción + PIN
   - Abrir incidencia: Soporte > Incidencias > PIN no válido
   - Resolución típica: 24-48h con reemplazo de PIN

### Cobro duplicado
1. NUNCA devolver dinero en efectivo al cliente sin verificar
2. Ir a Gestión > Transacciones > buscar las dos transacciones
3. Si efectivamente hay duplicado:
   - Una aparecerá como "completada" y otra como "fallida" o "revertida"
   - Si ambas aparecen como "completadas", contactar soporte INMEDIATAMENTE
4. Soporte gestiona el reembolso en 24-48h

---

## INCIDENCIAS DE PAQUETERÍA

### Paquete dañado a la recepción
1. NO aceptar el paquete si el daño es severo
2. Si el daño es leve, aceptar pero:
   - Fotografiar el daño
   - Anotar en el albarán "Recibido con daño visible"
   - Registrar incidencia en: Logística > Incidencias > Paquete dañado
3. El cliente será notificado del estado

### Cliente reclama paquete que no está
1. Verificar código/PIN del cliente
2. Buscar en: Logística > Paquetes > buscar por código
3. Posibles estados:
   - "Devuelto": ya se devolvió por plazo expirado
   - "En tránsito": aún no ha llegado al punto
   - "Entregado": ya se entregó (verificar fecha y firma)
4. Si no aparece en el sistema, el paquete no fue asignado a tu punto

### No puedo escanear un paquete
1. Limpiar código de barras (puede estar mojado o sucio)
2. Probar con más/menos luz
3. Introducir manualmente: últimos 8 dígitos del código
4. Si el código está completamente ilegible:
   - Contactar al transportista para obtener el tracking
   - Registrar manualmente con el número de tracking

---

## GESTIÓN DEL NEGOCIO

### Cómo hacer cierre de caja
1. Ir a Gestión > Cierre de Caja
2. El sistema muestra:
   - Total transacciones del día
   - Desglose por tipo (recargas, pines, paquetería, energía)
   - Comisiones generadas
   - Saldo actual
3. Confirmar cierre
4. Se genera informe PDF descargable

### Cómo ver mis comisiones
- Tiempo real: Panel principal > "Mi Beneficio Hoy"
- Histórico: Gestión > Comisiones > Filtrar por fecha
- Desglose: Por categoría (recargas, pines, logística, energía)
- Exportar: Botón "Exportar" para Excel/PDF

### Cómo solicitar un adelanto de saldo
1. Ir a Gestión > Saldo > Solicitar Adelanto
2. Monto mínimo: 50€ | Máximo: según historial
3. Se abona en 24h laborables
4. Comisión por adelanto: 1.5%

### Modelo 347 y facturación
- El sistema genera automáticamente los datos para el modelo 347
- Facturas electrónicas (Facturae) disponibles en: Gestión > Facturación
- Exportar datos fiscales: Gestión > Fiscal > Exportar año

---

## SEGURIDAD

### Sospecha de fraude en transacción
1. NO completar la transacción
2. Si ya se completó, anotar todos los datos
3. Contactar soporte INMEDIATAMENTE: 981 055 210
4. Señales de alerta:
   - Cliente pide múltiples recargas de alto valor seguidas
   - Cliente insiste en no dar datos de contacto
   - Comportamiento nervioso o presión por rapidez
   - Pago con billetes sospechosos

### Actualización de seguridad del terminal
- Las actualizaciones se instalan automáticamente por la noche
- NO apagar el terminal durante la noche si hay actualización pendiente
- Verificar versión: Ajustes > Sistema > Versión
- Versión mínima requerida: 4.2.1 (mayo 2026)

---

## TIPS PARA MAXIMIZAR COMISIONES

1. **Ofrecer proactivamente**: Cuando un cliente compra una recarga, sugerir también un PIN de entretenimiento
2. **Zona visible**: Colocar cartelería de servicios disponibles (Disashop proporciona material)
3. **Horario amplio**: Más horas = más paquetes = más comisiones
4. **Energía**: Un solo cambio de tarifa = 25€, equivale a 83 recargas de 5€
5. **Fidelización**: Clientes de paquetería vuelven cada semana
