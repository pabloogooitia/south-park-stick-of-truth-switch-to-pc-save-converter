# Guía paso a paso: South Park: La Vara de la Verdad, Switch → PC

*English: [GUIDE.md](GUIDE.md)*

1. [Sacar la partida de la Switch](#1-sacar-la-partida-de-la-switch)
2. [Preparar el juego en PC](#2-preparar-el-juego-en-pc)
3. [Convertir](#3-convertir)
4. [Instalar y jugar](#4-instalar-y-jugar)
5. [Steam Deck / Linux](#5-steam-deck--linux)
6. [Problemas frecuentes](#6-problemas-frecuentes)

---

## 1. Sacar la partida de la Switch

La Switch guarda las partidas en su memoria interna, y Nintendo no ofrece ninguna forma de
copiarlas a un ordenador. Ni siquiera la nube de Nintendo Switch Online: solo se puede descargar
de vuelta a una Switch. Hace falta un **gestor de partidas** homebrew, que funciona en consolas
con firmware modificado (Atmosphère).

> ⚠️ Usar homebrew incumple las condiciones de Nintendo y puede suponer el baneo de los servicios
> en línea. Para reducir el riesgo, usa **emuMMC**, mantén la consola **sin conexión (modo avión)**
> mientras uses el firmware modificado, y haz copia de todo antes. Si tienes Nintendo Switch
> Online, sube primero la partida a la **nube**, como red de seguridad.

### Opción A: tu Switch admite firmware modificado

Sigue la guía de la comunidad <https://switch.hacks.guide> (en inglés) para saber si tu consola
es compatible y cómo prepararla. Después usa una de estas apps:

| App | Cómo | Dónde quedan los archivos |
|---|---|---|
| **JKSV** (recomendada) | JKSV › tu usuario › *South Park: The Stick of Truth* › *Nueva copia* | `sd:/JKSV/South Park…/<nombre de la copia>/` (o un `.zip`) |
| **Checkpoint** | Elige el juego › *Backup* | `sd:/switch/Checkpoint/saves/<juego>/<nombre de la copia>/` |
| **DBI** | *Run MTP responder* y abre las partidas desde el PC por USB | cópialas a cualquier carpeta del PC |

Copia esa carpeta (o el zip) a tu ordenador. Contiene archivos como estos:

```
SP-Sav-M-Save-Slot-001     partidas manuales
SP-Sav-M-Save-Slot-002
SP-Sav-A-Checkpoint-1      autoguardados
SP-Sav-A-Checkpoint-2
SP-Sav-A-Checkpoint-3
SP-Opt                     ajustes (no hace falta)
.nx_save_meta.bin          datos de JKSV (no hace falta)
```

### Opción B: tu Switch no se puede modificar (modelo parcheado, Lite, OLED, Switch 2)

Usa la **transferencia de datos de guardado** de la propia consola para mover la partida a una
Switch que *sí* admita firmware modificado (la de un amigo, o una original de 2017 de segunda
mano), y haz la opción A en esa:

1. En tu consola: **Configuración de la consola › Gestión de datos › Transferir datos de
   guardado › Enviar datos de guardado a otra consola**.
2. En la otra consola (con el sistema oficial, no con el modificado), recíbela.
3. Arranca esa consola con el firmware modificado y haz la copia con JKSV.

La transferencia **mueve** la partida: se borra de la consola que la envía. Si puedes, súbela
antes a la nube, o devuélvela después por el mismo método.

---

## 2. Preparar el juego en PC

El conversor necesita **una partida guardada por tu juego de PC** para copiar unos valores que
solo existen en PC: una dirección de memoria que cambia con cada versión del ejecutable, y el
bloque cifrado de estadísticas.

1. Instala el juego en Steam y ábrelo.
2. Empieza una **partida nueva** y juega hasta que se guarde la primera partida o punto de
   control (unos minutos).
3. Cierra el juego.

Las partidas de PC están en:

```
%USERPROFILE%\Documents\My Games\South Park - The Stick of Truth\save
```

Si tu carpeta *Documentos* está en OneDrive, estarán en `OneDrive\Documents` (o
`OneDrive\Documentos`). `sot-save-converter where` te dice qué carpeta ha encontrado.

---

## 3. Convertir

### Ejecutable para Windows

Descarga `StickOfTruth-SaveConverter.exe` de la página de [Releases](../../../releases) y **arrastra encima
la carpeta o el zip del paso 1**. Encuentra tu carpeta de partidas de PC, usa como plantilla tu
partida de PC más reciente y deja los archivos convertidos en una carpeta `PC saves` al lado.

### Python

Python 3.8 o superior, sin paquetes adicionales:

```bash
python -m sot_save_converter convert "ruta/a/la/copia de JKSV"
```

Opciones útiles:

```bash
# elegir tú la plantilla
python -m sot_save_converter convert copia.zip --template "…/save/Save Slot 001.sav"

# escribir directamente en la carpeta del juego (antes comprime lo que haya)
python -m sot_save_converter convert copia.zip --install

# igual, y además borrar los .sav antiguos (quedan en el zip de copia)
python -m sot_save_converter convert copia.zip --install --clean
```

Para ver qué contiene una partida (descripción, número de objetos, estadísticas de Switch):

```bash
python -m sot_save_converter info SP-Sav-M-Save-Slot-002 "Save Slot 002.sav"
```

---

## 4. Instalar y jugar

1. **Desactiva Steam Cloud para el juego**: Steam › Biblioteca › clic derecho en *South Park™:
   The Stick of Truth™* › Propiedades › General › desmarca *Mantener partidas guardadas en Steam
   Cloud*. Si no, Steam puede sustituir los archivos nuevos por los antiguos de la nube.
2. Haz copia de la carpeta `save` de PC (`--install` la hace por ti como `save_backup_<fecha>.zip`).
3. Copia los `.sav` convertidos en la carpeta `save` (`--install` también lo hace).
4. Abre el juego › *Cargar partida*. Tus partidas de Switch aparecen con su descripción original,
   por ejemplo `LV 5, 02:10:33, Kastillo Kupa`.
5. Cuando cargue, **guarda una partida nueva en PC**, sal y carga esa. A partir de ahí juegas con
   una partida escrita por el propio juego de PC.
6. Vuelve a activar Steam Cloud si quieres.

Mientras juegas, comprueba el inventario y el equipo, el número de amigos, el diario de misiones,
las habilidades y las mejoras. Si algo falla, mira abajo.

---

## 5. Steam Deck / Linux

El juego funciona con Proton. Su carpeta de partidas está dentro del prefijo de Proton:

```
~/.steam/steam/steamapps/compatdata/213670/pfx/drive_c/users/steamuser/Documents/My Games/South Park - The Stick of Truth/save
```

En el modo escritorio, abre una terminal (Konsole). SteamOS ya trae Python 3:

```bash
python3 -m sot_save_converter convert ~/Downloads/copia-jksv --install
```

---

## 6. Problemas frecuentes

| Problema | Qué hacer |
|---|---|
| `no Nintendo Switch saves found` | Los archivos deben conservar su nombre original (`SP-Sav-M-Save-Slot-NNN`, `SP-Sav-A-Checkpoint-N`). Para convertir un archivo renombrado, pásalo directamente como archivo en vez de la carpeta. |
| `no PC save found to use as template` | Guarda primero una partida en PC (paso 2), o indica una con `--template`. |
| El juego no muestra las partidas convertidas | Comprueba que están en la carpeta que indica `where` (¡OneDrive!). Comprueba que Steam Cloud no ha restaurado las antiguas. |
| El juego se cierra o se queda colgado al cargar | Prueba con un punto de control en vez de la partida manual. Ejecuta `info` sobre el archivo de Switch y sobre el convertido y [abre un issue](../../../issues) con el resultado. No adjuntes las partidas en público salvo que no te importe. |
| Números distintos en la pantalla de estadísticas | Es lo esperado. Ese bloque va cifrado en PC y todavía no se puede convertir. |
| Algo concreto falla dentro del juego (falta un objeto, una misión no avanza…) | [Abre un issue](../../../issues) describiéndolo. Es justo la información que necesita el proyecto. |
