import type { Dict } from './types';
import { localeHref } from '../lib/urls';

/**
 * Cross-links baked into this locale's copy at module-eval time (build
 * time). localeHref() derives the prefix from the locale literal, so a
 * translated dict only has to swap 'en' for its own locale — the actual
 * path prefix always comes from the localePrefixes single source of truth.
 */
const guideHref = localeHref('es', 'vpn-on-steam-deck.html');
const landingFaqHref = `${localeHref('es', '')}#faq`;

export const es = {
  seo: {
    title: 'Xray Decky — Cliente VPN y proxy para Steam Deck',
    description:
      'Cliente VPN y proxy gratuito y de código abierto para Steam Deck (plugin de Decky Loader). VLESS, VMess, Trojan, Shadowsocks, Hysteria2, TUIC — modo TUN para el modo Gaming, suscripciones, kill switch, panel de administración web.',
  },

  nav: {
    ariaLabel: 'Navegación principal',
    features: 'Características',
    panel: 'Panel de administración',
    install: 'Instalación',
    guide: 'Guía',
    changelog: 'Novedades',
    help: 'Ayuda',
    github: 'GitHub ↗',
  },

  hero: {
    badgeStable: 'ESTABLE V2',
    badgeContext: 'Steam Deck · Decky Loader · Código abierto',
    titleHtml: 'Un cliente proxy de verdad.<br>En tu <span class="grad">Steam&nbsp;Deck</span>.',
    purpose:
      'VLESS · VMess · Trojan · Shadowsocks · Hysteria2 · TUIC — con REALITY y transportes modernos. Suscripciones con una lista de servidores gestionada, modo TUN, kill switch, estadísticas de tráfico en vivo — y un panel de administración web completo que abres desde tu teléfono.',
    ctaInstall: 'Instalar plugin',
    ctaGithub: 'Ver en GitHub',
    statsAriaLabel: 'Datos del proyecto',
    stats: [
      { countup: 6, label: 'protocolos compatibles' },
      { countup: 199, label: 'pruebas de backend' },
      { value: 'EN·RU', label: 'dos idiomas' },
      { value: 'MIT', label: 'licencia' },
    ],
    demoAriaLabel: 'Demo animada: el plugin en un Steam Deck junto al panel de administración web en un teléfono',
    demo: {
      deckStatus: 'Desconectado',
      enableConnection: 'Activar conexión',
      phonePill: 'DESCONECTADO',
      phoneStatus: 'Desconectado',
      phoneSub: 'El proxy está inactivo',
    },
    demoCaption: 'Acceso rápido en el Deck · panel de administración en tu teléfono — conecta con un toque',
  },

  protocols: {
    ariaLabel: 'Protocolos compatibles',
    chips: ['VLESS + REALITY', 'VMess', 'Trojan', 'Shadowsocks', 'Hysteria2', 'TUIC'],
    note: 'Hysteria2 / TUIC se ejecutan sobre el núcleo sing-box, descargado bajo demanda',
  },

  featuresTitle: 'Todo lo que un cliente proxy debería hacer',
  features: [
    {
      title: 'Importación con un solo pegado',
      html: 'Pega cualquier enlace <code>vless://</code>, <code>vmess://</code>, <code>trojan://</code>, <code>ss://</code>, <code>hysteria2://</code> o <code>tuic://</code>, una URL de suscripción, su contenido en base64 — o una configuración JSON completa de sing-box.',
    },
    {
      title: 'Suscripciones y lista de servidores',
      html: 'Suscripciones multiservidor con cuota y caducidad, nombres editables, actualización manual y <b>automática programada</b>. Los servidores añadidos manualmente siempre sobreviven a una actualización.',
    },
    {
      title: 'Prueba de latencia',
      html: 'Haz ping a todos los servidores a la vez, mira los resultados en la lista, cambia con un toque — una conexión activa se reconecta automáticamente a través del nuevo servidor.',
    },
    {
      title: 'Estadísticas de tráfico en vivo',
      html: 'Velocidad real de subida/bajada y totales de la sesión desde la API de estadísticas de xray — en la tarjeta de acceso rápido y como gráfico en vivo en el panel de administración.',
    },
    {
      title: 'Modo TUN',
      html: 'Enruta <b>todo</b> el tráfico del sistema a través del proxy — la única forma fiable en el modo Gaming, donde Steam ignora la configuración de SOCKS. Sobrevive a la suspensión y reanudación.',
    },
    {
      title: 'Kill switch que se limpia solo',
      html: 'Bloquea el tráfico si el proxy se cae — y elimina de forma fiable sus reglas de firewall después. El plugin incluye un script de recuperación, por si acaso.',
    },
    {
      title: 'Panel de administración web',
      html: 'Escanea un QR desde el Deck y gestiona todo desde tu teléfono: servidores, importar/exportar, opciones, actualizaciones. Protegido por token, con límite de peticiones y un interruptor de acceso por LAN.',
    },
    {
      title: 'Resiliente por diseño',
      html: 'El supervisor de procesos reinicia un núcleo caído en segundos, las rutas se reparan tras la suspensión, las versiones están fijadas — y todo está cubierto por 199 pruebas de backend.',
    },
  ],

  panel: {
    titleHtml: 'El menú de acceso rápido es para jugar.<br>El panel es para administrar.',
    introHtml:
      'El QAM se mantiene mínimo: conectar, elegir un servidor, ver la velocidad. Para todo lo demás hay un <b>panel de administración web con estilo Steam</b> que el propio plugin sirve por HTTPS:',
    list: [
      'Panel con estado en vivo y un gráfico de velocidad de dos minutos',
      'Lista de servidores ordenada por latencia, con etiquetas de protocolo y núcleo',
      'Barra de suscripción: actualizar, renombrar, programación de actualización automática, cuota y caducidad',
      'Importa cualquier cosa · exporta cada servidor como enlaces para compartir o una suscripción',
      'Comprobador de actualizaciones para el plugin y sus núcleos — sin telemetría',
      'Inglés y ruso, intercambiables al vuelo',
    ],
    securityHtml:
      '<b>Modelo de seguridad:</b> token por instalación (emparejado por QR), comparación en tiempo constante, límite de intentos de autenticación fallidos, las credenciales nunca se muestran en las vistas de lista — y un interruptor en el QAM para restringir todo el panel solo al Deck.',
  },

  install: {
    title: 'Instalación',
    prereqTitle: 'Requisitos previos',
    prereqHtml: [
      'Steam Deck con <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">Decky Loader</a> instalado',
      '<span class="badge-stable">STABLE</span> la línea v2 está probada en hardware real y se usa a diario — si algo falla, por favor <a href="https://github.com/VadimOnix/xray-decky/issues" target="_blank" rel="noopener">repórtalo</a>',
    ],
    methods: [
      {
        title: 'Opción 1 · Plugin Store',
        stepsHtml: [
          'Abre la configuración de <strong>Decky Loader</strong> (Quick Access → ⋯)',
          'Ve a <strong>Plugin Store</strong>',
          'Busca <strong>«Xray Decky»</strong>',
          'Haz clic en <strong>Install</strong>',
        ],
      },
      {
        title: 'Opción 2 · Modo Desktop',
        stepsHtml: [
          'Cambia al modo Desktop',
          'Descarga <a href="https://raw.githubusercontent.com/VadimOnix/xray-decky/master/scripts/Install-Xray-Decky.desktop" target="_blank" rel="noopener">Install‑Xray‑Decky.desktop</a>',
          'Properties → Permissions → «Is executable»',
          'Haz doble clic para ejecutar el instalador',
        ],
      },
      {
        title: 'Opción 3 · Manual',
        stepsHtml: [
          'Descarga el zip de la <a href="https://github.com/VadimOnix/xray-decky/releases/latest" target="_blank" rel="noopener">última versión</a>',
          'Decky → Settings → Developer → Install Plugin from URL',
          'Pega la URL del zip',
        ],
      },
    ],
    tunTitle: '¿Por qué el modo TUN?',
    tunHtml:
      'En el modo Gaming, Steam ignora la configuración del proxy SOCKS del sistema — los juegos y los servicios del sistema evitan el proxy. <b>TUN crea una interfaz de red virtual que enruta todo</b>, así que es el modo que realmente necesitas. Solo activa el interruptor; el plugin se encarga de las rutas y la limpieza.',
  },

  usageTitle: 'De cero a proxeado en tres pasos',
  usage: [
    {
      number: '1',
      title: 'Importar',
      body: 'Pega un enlace para compartir o una URL de suscripción en el QAM — o escanea el QR y pégala desde tu teléfono. Cada servidor de una suscripción se guarda.',
    },
    {
      number: '2',
      title: 'Conectar',
      body: 'Un interruptor. Estado y velocidad en vivo directamente en la tarjeta de acceso rápido. Elige otro servidor cuando quieras — la reconexión es automática.',
    },
    {
      number: '3',
      title: 'Cobertura de todo el sistema',
      body: 'Activa el modo TUN para cubrir el modo Gaming, añade el kill switch si quieres protección estricta contra fugas, y gestiona el resto desde el panel web.',
    },
  ],

  faqTitle: 'Solución de problemas',
  faq: [
    {
      q: 'La conexión falla',
      html: '<ul><li>Verifica que el enlace para compartir o la URL de suscripción sean válidos — los enlaces inválidos se rechazan antes de que puedan romper una configuración funcional</li><li>Comprueba la conectividad de red de tu Steam Deck</li><li>Haz ping a los servidores de la lista y prueba el más rápido</li></ul>',
    },
    {
      q: 'El modo TUN no funciona',
      html: '<ul><li>Asegúrate de que el plugin tiene los privilegios necesarios (consulta el INSTALLATION.md del repositorio)</li><li>Vuelve a activar TUN después de una actualización del sistema — las actualizaciones de SteamOS pueden borrar los permisos</li></ul>',
    },
    {
      q: 'El kill switch está bloqueando el tráfico',
      html: '<ul><li>Reconecta el proxy — el kill switch se libera automáticamente</li><li>O pulsa <b>Unblock traffic</b> en el plugin o el panel de administración</li><li>En el peor de los casos: <code>defaults/recover.sh</code> se incluye con el plugin y restaura la red incondicionalmente</li></ul>',
    },
    {
      q: 'No puedo abrir el panel de administración desde mi teléfono',
      html: '<ul><li>Comprueba el interruptor <b>Allow LAN access</b> en las opciones del QAM — en modo solo Deck, el panel es deliberadamente inaccesible desde otros dispositivos</li><li>Ambos dispositivos deben estar en la misma red; acepta la advertencia del certificado autofirmado</li><li>El QR incluye un token por instalación — empareja escaneando, no vuelvas a escribir la URL</li></ul>',
    },
    {
      q: 'Falta el binario de xray-core',
      html: '<ul><li>El plugin vuelve a descargar automáticamente su núcleo fijado en el siguiente inicio</li><li>¿Sin conexión? Descárgalo desde las <a href="https://github.com/XTLS/Xray-core/releases" target="_blank" rel="noopener">versiones de Xray-core</a> y colócalo en <code>backend/out/</code></li></ul>',
    },
    {
      q: '¿La Steam Deck admite una VPN?',
      html: '<p>No de fábrica — SteamOS no incluye ningún cliente VPN y el modo Gaming ignora la configuración de proxy del sistema. Xray Decky añade uno como plugin de Decky Loader: su modo TUN tuneliza todo el tráfico del sistema, así que también funciona en el modo Gaming.</p>',
    },
    {
      q: '¿Cómo uso una VPN en el modo Gaming?',
      html: `<p>Instala el plugin, importa un enlace de servidor, activa el modo TUN y conéctate — todo desde el menú de acceso rápido, sin cambiar al modo Desktop. Consulta la guía paso a paso: <a href="${guideHref}">Cómo configurar una VPN en Steam Deck</a>.</p>`,
    },
    {
      q: '¿Xray Decky es una VPN de verdad o un proxy?',
      html: '<p>Técnicamente es un cliente proxy (xray-core / sing-box) — pero con el modo TUN hace lo mismo que una VPN: una interfaz virtual enruta cada paquete del sistema a través del túnel cifrado. Sin TUN, se comporta como un proxy SOCKS para el modo Desktop.</p>',
    },
  ],

  footer: {
    links: ['GitHub', 'Novedades', 'Versiones', 'Reportar un problema', 'Hoja de ruta', 'Decky Loader', 'Xray-core'],
    copy: 'Xray Decky · Licencia MIT · Hecho para Steam Deck',
  },

  guide: {
    seo: {
      title: 'Configurar una VPN en Steam Deck (modo Gaming) | Xray Decky',
      description:
        'Paso a paso: instala una VPN en tu Steam Deck con Decky Loader y Xray Decky — funciona en el modo Gaming mediante el modo TUN, sin cambiar al modo Desktop.',
    },
    h1: 'Cómo configurar una VPN en Steam Deck (incluye el modo Gaming)',
    intro:
      'SteamOS no tiene un cliente VPN integrado, y en el modo Gaming los juegos ignoran por completo la configuración de proxy del sistema. Esta guía configura Xray Decky — un plugin de VPN y proxy gratuito y de código abierto para Decky Loader — para que todo tu tráfico se tunelice a nivel de sistema, sin salir nunca del modo Gaming.',
    whyTun: {
      title: 'Por qué necesitas TUN, no solo un proxy',
      body: 'Steam ignora la configuración del proxy SOCKS en el modo Gaming. El modo TUN crea una interfaz de red virtual que captura todo el tráfico del sistema — juegos, actualizaciones, chat de voz — y lo enruta a través de tu conexión cifrada al servidor. Eso es lo que hace que se comporte como una VPN en lugar de un proxy SOCKS que los juegos simplemente ignoran.',
    },
    prereqTitle: 'Lo que necesitas',
    prereqHtml: [
      'Una Steam Deck (cualquier modelo)',
      '<a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">Decky Loader</a> instalado',
      'Un enlace de servidor para compartir o una suscripción — <code>vless://</code>, <code>vmess://</code>, <code>trojan://</code>, <code>ss://</code>, <code>hysteria2://</code>, <code>tuic://</code> o una URL de suscripción',
    ],
    stepsTitle: 'Cinco pasos para una VPN funcional',
    stepsHtml: [
      '<b>Instala Decky Loader</b> — sigue la <a href="https://wiki.deckbrew.xyz/" target="_blank" rel="noopener">wiki de deckbrew.xyz</a>; sáltate este paso si ya lo tienes.',
      '<b>Instala Xray Decky</b> — Quick Access (⋯) → Plugin Store → busca «Xray Decky» → Install.',
      '<b>Importa tu servidor</b> — abre la tarjeta del plugin en Quick Access y pega un enlace para compartir o una URL de suscripción; o escanea el código QR y pégala desde tu teléfono.',
      '<b>Activa el modo TUN</b> — un interruptor en las opciones del plugin; las rutas y la limpieza son automáticas. Opcionalmente, activa el kill switch para una protección estricta contra fugas.',
      '<b>Conecta y verifica</b> — activa el interruptor de conexión y observa la velocidad en vivo en la tarjeta; abre cualquier página de tienda con restricción geográfica o un sitio de «cuál es mi IP» en el navegador del Deck para confirmar la nueva IP de salida.',
    ],
    troubleshootingTitle: '¿Algo no funciona?',
    troubleshootingHtml: `Consulta las <a href="${landingFaqHref}">preguntas frecuentes de solución de problemas</a> en la página de inicio — cubre fallos de conexión, el modo TUN, el kill switch y el acceso al panel de administración. En el peor de los casos, <code>defaults/recover.sh</code> se incluye con el plugin y restaura la red incondicionalmente.`,
  },
} satisfies Dict;
