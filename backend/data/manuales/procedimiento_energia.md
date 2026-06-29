# Procedimiento: Servicio de Comparador de Energía

## Descripción del Servicio
El comparador de energía de Disashop permite al comerciante actuar como asesor energético para sus clientes. El tendero analiza la factura del cliente, compara tarifas del mercado y gestiona el cambio de comercializadora directamente desde el Smart POS.

## Modelo de Negocio
- El cliente ahorra en su factura de luz
- El tendero gana una comisión por cada cambio exitoso (20-30€)
- Disashop cobra un porcentaje a la comercializadora destino
- Win-Win-Win: Cliente ahorra, tendero gana, Disashop crece

## Comisiones por Comercializadora
| Comercializadora | Comisión por alta | Tipo |
|-----------------|-------------------|------|
| EnergíaVerde    | 25€               | Indexada |
| LuzDirecta      | 20€               | Plana |
| PowerSave       | 30€               | Discriminación horaria |
| EcoEnergía      | 22€               | Plana renovable |

---

## PROCEDIMIENTO PASO A PASO

### Paso 1: Recepción del Cliente
- El vecino/cliente trae su factura de luz al establecimiento
- Puede ser factura en papel o digital (mostrar en móvil)
- Datos necesarios: consumo en kWh y tipo de tarifa actual

### Paso 2: Acceso al Comparador
- Smart POS: Menú > Energía > Comparador
- Disashop PC: Panel lateral > Servicios > Energía

### Paso 3: Introducción de Datos
Datos a introducir:
- **Consumo mensual** (kWh): Aparece en la factura como "Energía consumida"
- **Tarifa actual**: Plana / Indexada / Discriminación horaria
- **Potencia contratada** (opcional): Para cálculo más preciso
- **Código postal**: Para verificar disponibilidad de ofertas

### Paso 4: Análisis Automático
El sistema:
1. Calcula el coste actual estimado del cliente
2. Compara con TODAS las tarifas disponibles en el mercado
3. Ordena por ahorro potencial (de mayor a menor)
4. Muestra resultado en pantalla con gráfico comparativo

### Paso 5: Presentación al Cliente
Mostrar al cliente:
- "Con tu consumo de X kWh, actualmente pagas aproximadamente Y€/mes"
- "Si cambias a [Tarifa Recomendada], pagarías Z€/mes"
- "Ahorro mensual: W€ | Ahorro anual: W×12€"

### Paso 6: Aceptación y Contratación
Si el cliente acepta:
1. Verificar identidad con DNI (físico o digital 2026)
2. El sistema pre-completa el formulario de cambio
3. El cliente firma en la pantalla del Smart POS
4. Se genera el contrato digital
5. Se envía a la comercializadora destino

### Paso 7: Confirmación
- El cambio se hace efectivo en el próximo ciclo (máx. 21 días)
- El cliente recibe email/SMS de confirmación
- La comisión se abona al punto de venta tras activación exitosa

---

## TIPOS DE TARIFA EXPLICADOS

### Tarifa Plana
- Precio fijo por kWh, sin variaciones
- Ideal para: clientes que quieren previsibilidad
- Precio típico: 0.15€ - 0.19€/kWh

### Tarifa Indexada
- Precio variable según mercado mayorista (OMIE)
- Ideal para: clientes con consumo flexible
- Precio típico: 0.10€ - 0.16€/kWh (varía por hora)
- Mayor ahorro potencial pero con variabilidad

### Discriminación Horaria
- Dos precios: punta (cara) y valle (barata)
- Punta: 0.20€ - 0.25€/kWh (8:00-24:00)
- Valle: 0.06€ - 0.10€/kWh (0:00-8:00)
- Ideal para: clientes que pueden concentrar consumo en horario nocturno

---

## PREGUNTAS FRECUENTES DEL CLIENTE

### "¿Hay penalización por cambiar de compañía?"
No. Desde 2009, el cambio de comercializadora en España es gratuito y sin permanencia. El cliente puede cambiar cuando quiera sin coste.

### "¿Se corta la luz durante el cambio?"
No. El suministro NUNCA se interrumpe durante un cambio de comercializadora. Es un trámite administrativo transparente.

### "¿Cuánto tarda el cambio?"
Máximo 21 días naturales. Normalmente se hace efectivo en el siguiente ciclo de facturación.

### "¿Qué pasa si no estoy contento con la nueva tarifa?"
Puede volver a cambiar en cualquier momento, sin coste ni permanencia.

### "¿Necesito hacer algo en mi instalación?"
No. No se toca nada físico. Solo cambia la empresa que factura.

---

## VERIFICACIÓN DE IDENTIDAD (DNI Digital 2026)

### Nuevo Procedimiento con DNI Digital
A partir de 2026, los clientes pueden verificar su identidad con el nuevo DNI digital:
1. El cliente acerca su DNI al lector NFC del Smart POS
2. El terminal lee los datos del chip
3. Se verifica la autenticidad del documento
4. Los datos se pre-completan automáticamente en el formulario
5. Mayor seguridad y rapidez en el proceso

### Ventajas del DNI Digital
- Elimina errores de transcripción manual
- Verificación criptográfica de autenticidad
- Proceso más rápido (30 segundos vs 3 minutos)
- Mayor seguridad contra fraude de identidad

---

## INCIDENCIAS

### "El comparador no muestra resultados"
- Verificar conexión a internet
- Comprobar que el código postal es correcto
- Puede haber mantenimiento del servicio (consultar alertas)

### "El cliente no recibe confirmación"
- Verificar email/teléfono introducido
- La confirmación puede tardar hasta 24h
- Si no llega en 48h, contactar soporte

### "Comisión no abonada"
- Las comisiones se abonan tras activación exitosa (21 días)
- Verificar en: Gestión > Comisiones > Energía
- Si tras 30 días no aparece, abrir incidencia

## Contacto Soporte Energía
- Email: energia@disashop.com
- Teléfono: 981 055 210 (opción 3)
- Horario: Lunes a Viernes 9:00-18:00
