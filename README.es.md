# South Park: La Vara de la Verdad — Conversor de partidas de Switch a PC

**Pasa tu partida de *South Park: La Vara de la Verdad* (*The Stick of Truth*) de Nintendo Switch a
PC (Steam / Steam Deck).**

*English: [README.md](README.md)*

El juego no tiene partidas compartidas entre plataformas, y copiar una partida de Switch a la
carpeta de guardado de PC no sirve de nada: el juego de PC la ignora. Stick of Truth Save Converter traduce la
partida de Switch al formato de PC para que sigas jugando donde lo dejaste.

```
SP-Sav-M-Save-Slot-002   ──►   Save Slot 002.sav
(Nintendo Switch)               (PC / Steam / Steam Deck)
```

## Qué se transfiere

| Se transfiere | No se transfiere |
|---|---|
| Progreso de la historia y misiones, decisiones | La **pantalla de estadísticas** (daño infligido, dinero recogido, tiempo jugado…). En PC ese bloque va cifrado con una clave que no tenemos, así que conserva los valores de tu partida de PC. |
| Nivel, clase, habilidades, mejoras | Ajustes exclusivos de Switch |
| Inventario, equipo, parches, artefactos, coleccionables | |
| Amigos, aspecto del personaje | |
| Ubicación, estado de los NPC, miniatura y descripción de la partida | |

Solo funciona **de Switch a PC**. De PC a Switch todavía no está implementado.

## Estado

Primera versión, pero funcional: una partida real de Switch a mitad de juego se convirtió, cargó
y jugó en la versión de Steam. [Cuéntanos](../../issues) si te ha funcionado, tanto si sí
como si no.

## Qué necesitas

1. **Tu partida de Switch en archivos.** La Switch no deja copiar partidas a un PC por sí sola,
   así que hace falta un gestor de partidas como **JKSV** o **Checkpoint**. Esas apps solo
   funcionan en una Switch con firmware modificado, pero si la tuya no lo está hay alternativa.
   Mira la [guía paso a paso](docs/GUIDE.es.md#1-sacar-la-partida-de-la-switch).
2. **El juego en PC**, abierto al menos una vez y con **una partida guardada en PC** (basta con
   empezar una partida nueva y llegar al primer punto de control). El conversor copia de ella
   unos valores propios de PC.
3. El **ejecutable de Windows** de la página de [Releases](../../releases), o **Python 3.8+**.
   No hay más dependencias.

## Uso rápido

### Windows, sin Python

1. Descarga `StickOfTruth-SaveConverter.exe` de [Releases](../../releases).
2. Arrastra la carpeta con los archivos de tu partida de Switch (o el `.zip` que crea JKSV)
   **encima del exe**.
3. Las partidas convertidas aparecen en una carpeta `PC saves` al lado. Cópialas en
   `Documentos\My Games\South Park - The Stick of Truth\save`.
4. **Antes, desactiva Steam Cloud para el juego**: Steam › clic derecho en el juego ›
   Propiedades › General. Si no, Steam puede volver a poner tus partidas antiguas.

### Con Python (Windows, macOS, Linux, Steam Deck)

```bash
git clone <este repositorio> && cd south-park-stick-of-truth-switch-to-pc-save-converter

# convierte a ./PC saves (usa como plantilla tu partida de PC más reciente)
python -m sot_save_converter convert ruta/a/la/copia/de/JKSV

# …o convierte e instala directamente (antes comprime tus partidas de PC actuales en un zip)
python -m sot_save_converter convert ruta/a/la/copia/de/JKSV --install
```

Otros comandos:

```bash
python -m sot_save_converter info "Save Slot 002.sav" SP-Sav-M-Save-Slot-002   # ver qué contiene una partida
python -m sot_save_converter where                                              # localizar la carpeta de PC
python -m sot_save_converter convert --help
```

| Opción | Qué hace |
|---|---|
| `-t, --template ARCHIVO` | partida de PC de la que se toman los valores de PC (por defecto, la más reciente) |
| `-o, --output CARPETA` | dónde escribir las partidas convertidas (por defecto, `PC saves` junto a la entrada) |
| `--install` | escribe directamente en la carpeta de PC, después de comprimir lo que haya |
| `--clean` | con `--install`: borra los `.sav` antiguos (quedan en el zip de copia) |
| `--save-dir CARPETA` | carpeta de partidas de PC, si no se detecta sola |

Los nombres se traducen así: `SP-Sav-M-Save-Slot-NNN` → `Save Slot NNN.sav`,
`SP-Sav-A-Checkpoint-N` → `Checkpoint N.sav`. `SP-Opt` (ajustes) y `.nx_save_meta.bin` se ignoran.

## Cómo funciona

Las dos versiones guardan el estado del juego como un volcado directo de la memoria, y la mayor
parte es idéntica byte a byte. Las diferencias vienen de que la Switch es de 64 bits y la versión
de PC de 32 bits. La herramienta reescribe esas estructuras, recodifica la miniatura en PNG y
añade la cabecera de PC. El formato completo está documentado en [docs/FORMAT.md](docs/FORMAT.md)
(en inglés).

## Preguntas frecuentes

**¿Me pueden banear la Switch?** El conversor solo se ejecuta en tu ordenador y nunca toca la
consola. Lo que sí requiere homebrew es *sacar* la partida de la Switch, y eso va contra las
condiciones de Nintendo. En la [guía](docs/GUIDE.es.md) se explica cómo minimizar el riesgo.

**¿Puedo usar como plantilla la partida de PC de otra persona?** Usa la tuya. La plantilla debe
venir de la misma versión del juego de PC con la que vas a jugar.

**La pantalla de estadísticas muestra otros números.** Es lo esperado (ver la tabla de arriba).
`sot-save-converter info SP-Sav-M-Save-Slot-NNN` muestra tus estadísticas de Switch, para que al menos
las conozcas.

**¿Sirve para Retaguardia en Peligro (The Fractured But Whole)?** No. Es otro juego, con otro motor.

## Colaborar

Se agradecen reportes de errores, resultados de pruebas e investigación.
Ver [CONTRIBUTING.md](CONTRIBUTING.md). No adjuntes partidas en issues públicos salvo que no te
importe que sean públicas.

## Aviso legal

- Es un **proyecto de fans, no oficial y sin ánimo de lucro**. No tiene relación con Ubisoft, South
  Park Digital Studios, Obsidian Entertainment, Comedy Partners / Paramount, Nintendo ni Valve, ni
  está respaldado por ellos. *South Park*, *La Vara de la Verdad* / *The Stick of Truth* y el resto
  de nombres son marcas de sus dueños, y aquí solo se usan para indicar con qué juego funciona.
- **No es un mod**: no modifica, parchea ni redistribuye el juego, su ejecutable ni ninguno de sus
  recursos, y no incluye archivos del juego. Solo convierte **partidas guardadas que has creado
  tú** del formato de una plataforma al de otra, para un juego que tienes en las dos.
- El formato se ha deducido comparando partidas guardadas. No se ha descompilado el programa del juego.
- Sacar una partida de la Switch requiere homebrew, lo que va contra el acuerdo de usuario de
  Nintendo. Ese paso es decisión y responsabilidad tuya; ver la [guía](docs/GUIDE.es.md).
- Sin garantía (ver la [licencia](LICENSE)). Haz copia de tus partidas.

## Licencia

[MIT](LICENSE)
