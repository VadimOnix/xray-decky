# Xray Decky — Cliente VPN y proxy para Steam Deck

[English](README.md) · [Русский](README.ru.md) · [中文](README.zh-CN.md) · [فارسی](README.fa.md) · **Español**

Ejecuta una VPN en tu Steam Deck, incluso en el modo Gaming (Gaming Mode).
Xray Decky es un plugin de [Decky Loader](https://wiki.deckbrew.xyz/): un
cliente proxy completo (VLESS/VMess/Trojan/Shadowsocks/Hysteria2/TUIC) cuyo
modo TUN enruta **todo** el tráfico del sistema a través de un túnel
cifrado, ofreciendo una cobertura a nivel de todo el sistema, al estilo
VPN, que ni siquiera los juegos pueden ignorar. Incluye suscripciones
multiservidor, un panel de administración web con estilo Steam, kill
switch y estadísticas de tráfico en vivo.

## Características

- **Amplia cobertura de protocolos y transportes** — importa **VLESS**
  (REALITY / XTLS-Vision), **VMess**, **Trojan** y **Shadowsocks** (incl.
  cifrados 2022) sobre RAW/TCP, WebSocket, gRPC, HTTPUpgrade, XHTTP y mKCP,
  con parámetros completos de TLS / REALITY / huella uTLS. **Hysteria2** y
  **TUIC** se ejecutan sobre el núcleo sing-box, que se descarga bajo
  demanda.
- **Perfiles y suscripciones multiservidor** — almacena muchos servidores;
  importa una URL de suscripción (listas en base64 o de texto plano) y la
  actualiza en el mismo lugar. Los servidores añadidos manualmente se
  conservan al actualizar, y la cuota de datos / caducidad del proveedor
  (`Subscription-Userinfo`) se muestra cuando está disponible.
- **Prueba de latencia** — TCPing de todos los servidores, con resultados
  por servidor codificados por color tanto en el selector del QAM como en
  el panel web.
- **Estadísticas de tráfico en vivo** — velocidad de descarga/subida y
  totales de la sesión en el QAM, además de un gráfico de velocidad en
  tiempo real en el panel web.
- **Panel de administración web** — interfaz de gestión con estilo Steam en
  tu teléfono/PC (emparejamiento por QR desde el QAM): estado en vivo +
  gráfico de velocidad, lista de servidores, información de la suscripción,
  importación, interruptores de TUN / kill switch, y un comprobador de
  actualizaciones del núcleo. Protegido por un token aleatorio por
  instalación con limitación de intentos fallidos de autenticación.
- **Menú de acceso rápido (Quick Access Menu)** — interruptor de conexión,
  selector de servidor, estado/velocidad en vivo, TUN + kill switch, y un
  código QR del panel de administración.
- **Inglés / Ruso** — tanto el QAM como el panel web están localizados
  (detectado automáticamente según el idioma de Steam / del navegador).
- **Interruptor de conexión** — activa/desactiva el proxy desde el acceso
  rápido.
- **Modo TUN** — enrutamiento a nivel de todo el sistema, al estilo VPN, a
  través de una interfaz de red virtual, **recomendado para el modo
  Gaming (Gaming Mode)**.
- **Kill Switch** — bloquea el tráfico cuando el proxy se desconecta
  (opcional).
- **Resiliente** — un fallo de xray-core se detecta al instante y se
  reinicia con backoff; las rutas TUN se vuelven a aplicar tras
  suspender/reanudar; el núcleo fijado se autorrepara si el sistema de
  archivos inmutable borra el binario incluido.

**Recuperación de red:** si el Deck pierde la conectividad porque el
plugin terminó de forma abrupta, ejecuta `sudo bash recover.sh` (incluido
en la carpeta del plugin, también disponible en
[defaults/recover.sh](defaults/recover.sh)) desde una terminal en modo
Desktop (Desktop Mode); elimina la cadena de firewall del kill switch, las
rutas TUN obsoletas y el proxy del sistema.

## Instalación

**Requisitos previos:** Steam Deck con [Decky Loader](https://wiki.deckbrew.xyz/) instalado.

- **Plugin Store (recomendado):** Decky Loader → Plugin Store → busca "Xray Decky" → Install.
- **Modo Desktop (un clic):** Descarga [Install-Xray-Decky.desktop](https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop), márcalo como ejecutable (Properties → Permissions) y haz doble clic para ejecutarlo. Consulta [scripts/README.md](scripts/README.md).
- **Manual:** Descarga el zip de la [última versión](https://github.com/VadimOnix/xray-decky/releases/latest) → Decky Loader → Settings → Developer → Install Plugin from URL → pega la URL del zip.

**Modo TUN (recomendado):** En el modo Gaming, Steam no respeta la
configuración del proxy SOCKS del sistema: los juegos y la mayoría de los
servicios del sistema lo ignoran. El modo TUN crea una interfaz de red
virtual que enruta **todo** el tráfico del sistema a través del proxy,
lo que lo convierte en la única forma fiable de enrutar el tráfico en el modo Gaming.
Activa TUN en la configuración del plugin; no se necesita configuración
adicional.

Sin TUN, el plugin recurre al modo proxy SOCKS, que funciona en modo
Desktop pero puede no cubrir juegos ni servicios del sistema en el modo
Gaming.

**Uso, solución de problemas y más:** [documentación en GitHub Pages](https://vadimonix.github.io/xray-decky/).

## Desarrollo

### Requisitos previos

- Node.js v16.14+
- pnpm v9 (obligatorio)
- Python 3.x
- binario de xray-core

### Configuración

```bash
pnpm install
pnpm run build
# Backend: pip install -r requirements-dev.txt
# xray-core: place in bin/xray-core
```

Pruebas y linters (sin necesidad de dispositivo): `pnpm test`,
`pnpm run lint`, `pytest tests/`, `ruff check py_modules/ tests/ main.py conftest.py`.
Consulta [Tests and linters](CONTRIBUTING.md#tests-and-linters).

### Estructura del proyecto

```
├── src/                      # Frontend TypeScript/React
├── py_modules/backend/src/   # Backend Python, xray-core/sing-box managers
├── defaults/static/          # Embedded web admin panel (ships to plugin root)
├── defaults/recover.sh       # Network recovery script (ships to plugin root)
├── tests/                    # Python test suite (pytest)
├── tests/frontend/           # Frontend test suite (vitest: src/ + admin panel)
├── bin/                      # Local dev core binaries (xray-core, sing-box)
├── site/                     # GitHub Pages site (Astro, 5 locales)
├── main.py                   # Backend entry point
├── plugin.json
└── package.json
```

Consulta [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) y [docs/RELEASING.md](docs/RELEASING.md) para más información.

## Licencia

MIT — consulta LICENSE.

## Recursos

- [Decky Loader](https://wiki.deckbrew.xyz/)
- [xray-core](https://xtls.github.io/)
- [Especificación del plugin](./specs/001-xray-vless-decky/spec.md)
