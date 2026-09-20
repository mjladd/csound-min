# csound-min

A pruned fork of [Csound](https://github.com/csound/csound) 7.0.0 beta, cut
down to the engine and the command line program, for Linux and macOS only.

This fork exists to be read. Upstream Csound carries ports for iOS, Android,
WebAssembly, Bela, Daisy and Zynq, bindings for Java, Python and Lisp, and
packaging for several systems. All of that is removed here. The engine, all
1,821 opcodes and the analysis utilities are kept unchanged.

Start with [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), a reading map of the engine.
[docs/BUILD.md](docs/BUILD.md) has the build and the render commands.
[src/tools/README.md](src/tools/README.md) records how the cut was made and how to
prove that a change leaves the audio alone.

This is a personal learning fork. It does not track upstream, and it is not a
place to send patches. Send those to
[csound/csound](https://github.com/csound/csound).

# INSTALLING

This fork publishes no binaries. Build it from source. [docs/BUILD.md](docs/BUILD.md) lists the
packages you need and the two commands that build it.

Upstream Csound does publish prebuilt binaries for Linux on Intel, Windows and
macOS. Take those from https://github.com/csound/csound/releases when you want
a supported install rather than this reading copy.

# WHAT IS CSOUND

A sound and music computing system, first written by Barry Vercoe at MIT in
1986, with roots in the Music N languages going back to 1957.

You write an orchestra, which declares instruments out of opcodes, and a
score, which says when to play them. Csound renders the result to a file or to
an audio device.

The [Csound Reference Manual](http://docs.csound.com) documents every opcode.
The [API reference](http://csound.github.io/docs/api/index.html) documents the
C interface in `src/include/csound.h`.

# LICENSE

Csound is copyright (c) 1991-2024 The Csound Developers. The full license
text is in [docs/COPYING](docs/COPYING), and the contributor list is in
[docs/AUTHORS](docs/AUTHORS) and under CONTRIBUTORS below.

Csound is free software; you can redistribute it and/or modify it under the
terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 2.1 of the License, or, at your option,
any later version.

Csound is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY, without even the implied warranty of MERCHANTABILITY or FITNESS FOR
A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
details.

You should have received a copy of the GNU Lesser General Public License along
with this software. If not, write to the Free Software Foundation, Inc.,
31 Milk Street, #960789, Boston, MA, 02196, USA.

# CONTRIBUTORS

Csound contains contributions from musicians, scientists, and programmers
from around the world. They include (but are not limited to):

* Allan Lee
* Andres Cabrera
* Anthony Kozar
* Barry Vercoe
* Bill Gardner
* Bill Verplank
* Dan Ellis
* David Macintyre
* Ed Costello
* Eli Breder
* Fabio P. Bertolotti
* Felipe Sataler
* François Pinot
* Gabriel Maldonado
* Greg Sullivan
* Hans Mikelson
* Henri Manson
* Ian McCurdy
* Istvan Varga
* Jean Piché
* Joachim Heintz
* John Ramsdell
* John ffitch
* Marc Resibois
* Mark Dolson
* Matt Ingalls
* Max Mathews
* Michael Casey
* Michael Clark
* Michael Gogins
* Mike Berry
* Nate Whetsell
* Paris Smaragdis
* Perry Cook
* Peter Neubäcker
* Peter Nix
* Rasmus Ekman
* Richard Dobson
* Richard Karpen
* Rob Shaw
* Robin Whittle
* Rory Walsh
* Sean Costello
* Stephen Kyne
* Steven Yi
* Tito Latini
* Tom Erbe
* Victor Lazzarini
* Ville Pulkki
* Werner Mendizabal
