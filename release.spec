#!/bin/bash

APP_NAME="Flacon"

SOURCE=flacon-6.0.0.tar.gz

THIRD_PARTY_PROGS="faac flac lame mac metaflac mp3gain oggenc opusenc sox ttaenc vorbisgain wavpack wvgain wvunpack"

CERT_IDENTITY="Developer ID Application: Alex Sokolov (635H9TYSZJ)"


MAKE_DMG=Yes

. ./bin/makeBundle.sh